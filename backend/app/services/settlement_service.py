import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.expense import Expense, ExpensePayer, ExpenseSplit
from app.models.group import Group
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.settlement import (
    CurrencyGroupSuggestions,
    ExchangeRateInfo,
    SettlementCreate,
    SettlementResponse,
    SettlementSuggestion,
    SettlementSuggestionsResponse,
    UnifiedSuggestions,
)
from app.services.activity_log_service import log_activity
from app.services.exchange_rate_service import get_rate
from app.services.group_service import check_membership


# ---------------------------------------------------------------------------
# 內部工具
# ---------------------------------------------------------------------------

def _confirmed_filter():
    """只計入已確認的 settlement（相容舊資料 status IS NULL）"""
    return or_(Settlement.status == "confirmed", Settlement.status.is_(None))


def _build_response(s: Settlement, user_map: dict[uuid.UUID, str]) -> SettlementResponse:
    return SettlementResponse(
        id=s.id,
        group_id=s.group_id,
        from_user=s.from_user,
        from_user_name=user_map.get(s.from_user, "Unknown"),
        to_user=s.to_user,
        to_user_name=user_map.get(s.to_user, "Unknown"),
        amount=s.amount,
        currency=s.currency,
        note=s.note,
        status=s.status,
        settled_at=s.settled_at,
        confirmed_at=s.confirmed_at,
        original_currency=s.original_currency,
        original_amount=s.original_amount,
        locked_rate=s.locked_rate,
    )


# ---------------------------------------------------------------------------
# 餘額計算 — 統一幣別（原有邏輯，供 balance_service 使用）
# ---------------------------------------------------------------------------

async def calculate_balances(
    db: AsyncSession, group_id: uuid.UUID
) -> dict[uuid.UUID, Decimal]:
    """
    Calculate net balance for each user, converted to the group's base currency.
    Positive = others owe them. Negative = they owe others.
    Only confirmed settlements are counted.
    """
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()
    base_currency = group.default_currency

    balances: dict[uuid.UUID, Decimal] = defaultdict(Decimal)
    rate_cache: dict[str, Decimal] = {}

    async def to_base(amount: Decimal, currency: str) -> Decimal:
        currency = currency.upper()
        if currency == base_currency.upper():
            return amount
        if currency not in rate_cache:
            rate, _ = await get_rate(db, currency, base_currency)
            rate_cache[currency] = rate
        return round(amount * rate_cache[currency], 2)

    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
        .options(selectinload(Expense.splits), selectinload(Expense.payers))
    )
    expenses = result.scalars().all()

    for expense in expenses:
        # 多人付款：用 payers 分配付款金額；單人付款：全額歸 paid_by
        if expense.payers:
            converted_payer_amounts: list[tuple[uuid.UUID, Decimal]] = []
            for payer in expense.payers:
                converted_payer_amounts.append(
                    (payer.user_id, await to_base(payer.amount, expense.currency))
                )
            total_payer_converted = sum(amt for _, amt in converted_payer_amounts)
            for uid, amt in converted_payer_amounts:
                balances[uid] += amt
        else:
            total_payer_converted = await to_base(expense.total_amount, expense.currency)
            balances[expense.paid_by] += total_payer_converted

        # 轉換各 split，並強制合計 = 付款總額（尾差歸第一人）
        converted_splits: list[tuple[uuid.UUID, Decimal]] = []
        for split in expense.splits:
            converted_splits.append(
                (split.user_id, await to_base(split.amount, expense.currency))
            )
        total_splits_converted = sum(amt for _, amt in converted_splits)
        rounding_diff = total_payer_converted - total_splits_converted
        if rounding_diff != Decimal("0") and converted_splits:
            uid_0, amt_0 = converted_splits[0]
            converted_splits[0] = (uid_0, amt_0 + rounding_diff)

        for uid, amt in converted_splits:
            balances[uid] -= amt

    settlement_result = await db.execute(
        select(Settlement).where(
            Settlement.group_id == group_id,
            _confirmed_filter(),
        )
    )
    settlements = settlement_result.scalars().all()

    for s in settlements:
        converted_amount = await to_base(s.amount, s.currency)
        balances[s.from_user] += converted_amount
        balances[s.to_user] -= converted_amount

    return {uid: bal for uid, bal in balances.items() if abs(bal) > Decimal("0.01")}


# ---------------------------------------------------------------------------
# 餘額計算 — 分幣別（Phase 2）
# ---------------------------------------------------------------------------

async def calculate_balances_by_currency(
    db: AsyncSession, group_id: uuid.UUID
) -> dict[str, dict[uuid.UUID, Decimal]]:
    """
    按 expense.currency 分組計算淨餘額，不做幣別轉換。
    回傳：{ "USD": {user_a: +50, user_b: -50}, "TWD": {...} }
    """
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
        .options(selectinload(Expense.splits), selectinload(Expense.payers))
    )
    expenses = result.scalars().all()

    # currency -> user_id -> balance
    by_currency: dict[str, dict[uuid.UUID, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

    for expense in expenses:
        cur = expense.currency.upper()
        if expense.payers:
            for payer in expense.payers:
                by_currency[cur][payer.user_id] += payer.amount
        else:
            by_currency[cur][expense.paid_by] += expense.total_amount
        for split in expense.splits:
            by_currency[cur][split.user_id] -= split.amount

    # 只計入 confirmed settlement
    settlement_result = await db.execute(
        select(Settlement).where(
            Settlement.group_id == group_id,
            _confirmed_filter(),
        )
    )
    settlements = settlement_result.scalars().all()

    for s in settlements:
        # 換幣結算：用原始幣別/金額沖銷，確保原幣別債務歸零
        if s.original_currency and s.original_amount:
            cur = s.original_currency.upper()
            by_currency[cur][s.from_user] += s.original_amount
            by_currency[cur][s.to_user] -= s.original_amount
        else:
            cur = s.currency.upper()
            by_currency[cur][s.from_user] += s.amount
            by_currency[cur][s.to_user] -= s.amount

    # 檢核點：每個幣別池內所有人的淨餘額加總必須為 0
    for cur, balances in by_currency.items():
        total = sum(balances.values())
        if abs(total) > Decimal("0.02"):
            logger.error(
                "Balance integrity check failed: currency=%s sum=%s (expected 0)",
                cur, total,
            )
            raise ValueError(
                f"Balance integrity error: {cur} pool sums to {total}, expected 0"
            )

    # 過濾掉接近零的餘額
    cleaned: dict[str, dict[uuid.UUID, Decimal]] = {}
    for cur, balances in by_currency.items():
        filtered = {uid: bal for uid, bal in balances.items() if abs(bal) > Decimal("0.01")}
        if filtered:
            cleaned[cur] = filtered

    return cleaned


# ---------------------------------------------------------------------------
# 餘額計算 — 統一幣別（Phase 3，指定目標幣別）
# ---------------------------------------------------------------------------

async def calculate_balances_unified(
    db: AsyncSession, group_id: uuid.UUID, target_currency: str
) -> tuple[dict[uuid.UUID, Decimal], list[ExchangeRateInfo]]:
    """
    所有幣別轉換為 target_currency 後計算淨餘額。
    回傳：(balances_dict, exchange_rates_used)
    """
    balances: dict[uuid.UUID, Decimal] = defaultdict(Decimal)
    rate_cache: dict[str, tuple[Decimal, datetime]] = {}
    target = target_currency.upper()

    async def to_target(amount: Decimal, currency: str) -> Decimal:
        currency = currency.upper()
        if currency == target:
            return amount
        if currency not in rate_cache:
            rate, fetched_at = await get_rate(db, currency, target)
            rate_cache[currency] = (rate, fetched_at)
        return round(amount * rate_cache[currency][0], 2)

    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
        .options(selectinload(Expense.splits), selectinload(Expense.payers))
    )
    expenses = result.scalars().all()

    for expense in expenses:
        # 計算付款方轉換後總額
        if expense.payers:
            converted_payer_amounts: list[tuple[uuid.UUID, Decimal]] = []
            for payer in expense.payers:
                converted_payer_amounts.append(
                    (payer.user_id, await to_target(payer.amount, expense.currency))
                )
            total_payer_converted = sum(amt for _, amt in converted_payer_amounts)
            for uid, amt in converted_payer_amounts:
                balances[uid] += amt
        else:
            total_payer_converted = await to_target(expense.total_amount, expense.currency)
            balances[expense.paid_by] += total_payer_converted

        # 轉換各 split，並強制合計 = 付款總額（尾差歸第一人）
        converted_splits: list[tuple[uuid.UUID, Decimal]] = []
        for split in expense.splits:
            converted_splits.append(
                (split.user_id, await to_target(split.amount, expense.currency))
            )
        total_splits_converted = sum(amt for _, amt in converted_splits)
        rounding_diff = total_payer_converted - total_splits_converted
        if rounding_diff != Decimal("0") and converted_splits:
            uid_0, amt_0 = converted_splits[0]
            converted_splits[0] = (uid_0, amt_0 + rounding_diff)

        for uid, amt in converted_splits:
            balances[uid] -= amt

    settlement_result = await db.execute(
        select(Settlement).where(
            Settlement.group_id == group_id,
            _confirmed_filter(),
        )
    )
    settlements = settlement_result.scalars().all()

    for s in settlements:
        converted_amount = await to_target(s.amount, s.currency)
        balances[s.from_user] += converted_amount
        balances[s.to_user] -= converted_amount

    filtered = {uid: bal for uid, bal in balances.items() if abs(bal) > Decimal("0.01")}

    rates_used = [
        ExchangeRateInfo(
            from_currency=cur,
            to_currency=target,
            rate=rate,
            fetched_at=fetched_at,
        )
        for cur, (rate, fetched_at) in rate_cache.items()
    ]

    return filtered, rates_used


# ---------------------------------------------------------------------------
# 貪婪演算法簡化債務（不變）
# ---------------------------------------------------------------------------

def simplify_debts(balances: dict[uuid.UUID, Decimal]) -> list[dict]:
    """
    Minimize number of transactions using greedy algorithm.
    Match largest creditor with largest debtor.
    """
    debtors = []
    creditors = []

    for uid, balance in balances.items():
        if balance < 0:
            debtors.append([uid, -balance])
        elif balance > 0:
            creditors.append([uid, balance])

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    transactions = []
    i, j = 0, 0

    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]
        amount = min(debt, credit)

        if amount > Decimal("0.01"):
            transactions.append({
                "from": debtor_id,
                "to": creditor_id,
                "amount": round(amount, 2),
            })

        debtors[i][1] -= amount
        creditors[j][1] -= amount

        if debtors[i][1] < Decimal("0.01"):
            i += 1
        if creditors[j][1] < Decimal("0.01"):
            j += 1

    return transactions


# ---------------------------------------------------------------------------
# Pairwise 債務計算（simplify_debts=False 時使用）
# ---------------------------------------------------------------------------

async def calculate_pairwise_debts_by_currency(
    db: AsyncSession, group_id: uuid.UUID
) -> dict[str, list[dict]]:
    """
    按幣別計算每對使用者之間的淨債務，不做跨使用者簡化。
    回傳：{ "TWD": [{"from": uid_a, "to": uid_b, "amount": Decimal}], ... }
    """
    result_db = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
        .options(selectinload(Expense.splits), selectinload(Expense.payers))
    )
    expenses = result_db.scalars().all()

    # currency -> (debtor, creditor) -> amount
    pairwise: dict[str, dict[tuple[uuid.UUID, uuid.UUID], Decimal]] = defaultdict(
        lambda: defaultdict(Decimal)
    )

    for expense in expenses:
        cur = expense.currency.upper()
        if expense.payers:
            # 多人付款：每個 split 使用者對每個 payer 按比例欠款
            for split in expense.splits:
                for payer in expense.payers:
                    if split.user_id != payer.user_id:
                        # split 使用者對這個 payer 的欠款比例 = payer 付的比例 * split 的金額
                        payer_ratio = payer.amount / expense.total_amount
                        debt = round(split.amount * payer_ratio, 2)
                        pairwise[cur][(split.user_id, payer.user_id)] += debt
        else:
            for split in expense.splits:
                if split.user_id != expense.paid_by:
                    pairwise[cur][(split.user_id, expense.paid_by)] += split.amount

    # 扣除已確認的 settlement
    settlement_result = await db.execute(
        select(Settlement).where(
            Settlement.group_id == group_id,
            _confirmed_filter(),
        )
    )
    for s in settlement_result.scalars().all():
        # 換幣結算：用原始幣別/金額沖銷
        if s.original_currency and s.original_amount:
            cur = s.original_currency.upper()
            pairwise[cur][(s.from_user, s.to_user)] -= s.original_amount
        else:
            cur = s.currency.upper()
            pairwise[cur][(s.from_user, s.to_user)] -= s.amount

    # 淨額化每對使用者
    cleaned: dict[str, list[dict]] = {}
    for cur, pairs in pairwise.items():
        processed: set[tuple[uuid.UUID, uuid.UUID]] = set()
        transactions: list[dict] = []
        for (a, b), amount in pairs.items():
            if (a, b) in processed or (b, a) in processed:
                continue
            reverse = pairs.get((b, a), Decimal("0"))
            net = amount - reverse
            if net > Decimal("0.01"):
                transactions.append({"from": a, "to": b, "amount": round(net, 2)})
            elif net < Decimal("-0.01"):
                transactions.append({"from": b, "to": a, "amount": round(-net, 2)})
            processed.add((a, b))
            processed.add((b, a))
        if transactions:
            cleaned[cur] = transactions

    return cleaned


async def get_pairwise_details(
    db: AsyncSession, group_id: uuid.UUID
) -> list[dict]:
    """取得 pairwise 債務明細（供前端展開顯示用）"""
    pairwise_map = await calculate_pairwise_debts_by_currency(db, group_id)
    if not pairwise_map:
        return []

    all_user_ids: set[uuid.UUID] = set()
    for transactions in pairwise_map.values():
        for t in transactions:
            all_user_ids.add(t["from"])
            all_user_ids.add(t["to"])
    user_map = await _load_user_names(db, list(all_user_ids))

    result = []
    for cur, transactions in sorted(pairwise_map.items()):
        for t in transactions:
            result.append({
                "from_user_id": str(t["from"]),
                "from_user_name": user_map.get(t["from"], "Unknown"),
                "to_user_id": str(t["to"]),
                "to_user_name": user_map.get(t["to"], "Unknown"),
                "amount": str(t["amount"]),
                "currency": cur,
            })
    return result


# ---------------------------------------------------------------------------
# 結算建議（支援分幣別 / 統一幣別）
# ---------------------------------------------------------------------------

async def get_settlement_suggestions(
    db: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    unified_currency: str | None = None,
) -> SettlementSuggestionsResponse:
    """
    unified_currency=None  -> 分幣別模式（預設）
    unified_currency="TWD" -> 統一幣別模式
    """
    await check_membership(db, group_id, user_id)

    if unified_currency:
        # --- 統一幣別模式 ---
        balances, rates_used = await calculate_balances_unified(
            db, group_id, unified_currency
        )
        if not balances:
            return SettlementSuggestionsResponse(
                mode="unified",
                unified=UnifiedSuggestions(
                    target_currency=unified_currency, suggestions=[], exchange_rates=rates_used,
                ),
            )

        user_map = await _load_user_names(db, list(balances.keys()))
        transactions = simplify_debts(balances)

        suggestions = [
            SettlementSuggestion(
                from_user_id=t["from"],
                from_user_name=user_map.get(t["from"], "Unknown"),
                to_user_id=t["to"],
                to_user_name=user_map.get(t["to"], "Unknown"),
                amount=t["amount"],
                currency=unified_currency,
            )
            for t in transactions
        ]
        return SettlementSuggestionsResponse(
            mode="unified",
            unified=UnifiedSuggestions(
                target_currency=unified_currency,
                suggestions=suggestions,
                exchange_rates=rates_used,
            ),
        )

    # --- 分幣別模式（預設，使用簡化債務演算法）---
    balances_map = await calculate_balances_by_currency(db, group_id)
    if not balances_map:
        return SettlementSuggestionsResponse(mode="by_currency", by_currency=[])

    # 收集所有涉及的 user_id
    all_user_ids: set[uuid.UUID] = set()
    for balances in balances_map.values():
        all_user_ids.update(balances.keys())
    user_map = await _load_user_names(db, list(all_user_ids))

    groups: list[CurrencyGroupSuggestions] = []
    for cur, balances in sorted(balances_map.items()):
        transactions = simplify_debts(balances)
        suggestions = [
            SettlementSuggestion(
                from_user_id=t["from"],
                from_user_name=user_map.get(t["from"], "Unknown"),
                to_user_id=t["to"],
                to_user_name=user_map.get(t["to"], "Unknown"),
                amount=t["amount"],
                currency=cur,
            )
            for t in transactions
        ]
        if suggestions:
            groups.append(CurrencyGroupSuggestions(currency=cur, suggestions=suggestions))

    return SettlementSuggestionsResponse(mode="by_currency", by_currency=groups)


async def _load_user_names(db: AsyncSession, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    if not user_ids:
        return {}
    user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    return {u.id: u.display_name for u in user_result.scalars().all()}


# ---------------------------------------------------------------------------
# 建立結算
# ---------------------------------------------------------------------------

async def create_settlement(
    db: AsyncSession,
    group_id: uuid.UUID,
    from_user_id: uuid.UUID,
    data: SettlementCreate,
) -> SettlementResponse:
    if from_user_id == data.to_user:
        raise ValidationError("Cannot settle with yourself")

    await check_membership(db, group_id, from_user_id)
    await check_membership(db, group_id, data.to_user)

    settlement = Settlement(
        group_id=group_id,
        from_user=from_user_id,
        to_user=data.to_user,
        amount=data.amount,
        currency=data.currency,
        note=data.note,
        status="pending",
        original_currency=data.original_currency,
        original_amount=data.original_amount,
        locked_rate=data.locked_rate,
    )
    db.add(settlement)
    await db.flush()

    user_result_for_log = await db.execute(
        select(User.display_name).where(User.id == data.to_user)
    )
    payee_name = user_result_for_log.scalar_one_or_none() or "Unknown"

    await log_activity(
        db, group_id=group_id, actor_id=from_user_id, action="settlement_created",
        target_type="settlement", target_id=settlement.id,
        amount=data.amount, currency=data.currency, extra_name=payee_name,
    )

    user_map = await _load_user_names(db, [from_user_id, data.to_user])

    # Push 通知收款方
    from app.services.push_service import notify_settlement
    from_name = user_map.get(from_user_id, "Unknown")
    await notify_settlement(db, data.to_user, from_name, data.amount, data.currency, group_id)

    return _build_response(settlement, user_map)


# ---------------------------------------------------------------------------
# 確認結算（收款方操作）
# ---------------------------------------------------------------------------

async def confirm_settlement(
    db: AsyncSession,
    group_id: uuid.UUID,
    settlement_id: uuid.UUID,
    user_id: uuid.UUID,
) -> SettlementResponse:
    result = await db.execute(
        select(Settlement).where(
            Settlement.id == settlement_id,
            Settlement.group_id == group_id,
        )
    )
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise NotFoundError("Settlement not found")

    if settlement.to_user != user_id:
        raise ForbiddenError("Only the payee can confirm a settlement")

    if settlement.status != "pending":
        raise ValidationError(f"Settlement is already {settlement.status}")

    settlement.status = "confirmed"
    settlement.confirmed_at = datetime.now(timezone.utc)
    await db.flush()

    await log_activity(
        db, group_id=group_id, actor_id=user_id, action="settlement_confirmed",
        target_type="settlement", target_id=settlement.id,
        amount=settlement.amount, currency=settlement.currency,
    )

    user_map = await _load_user_names(db, [settlement.from_user, settlement.to_user])

    # Push 通知付款方：結算已確認
    from app.services.push_service import notify_settlement_confirmed
    confirmer_name = user_map.get(user_id, "Unknown")
    await notify_settlement_confirmed(
        db, settlement.from_user, confirmer_name, settlement.amount, settlement.currency, group_id,
    )

    return _build_response(settlement, user_map)


# ---------------------------------------------------------------------------
# 拒絕結算（收款方操作）
# ---------------------------------------------------------------------------

async def reject_settlement(
    db: AsyncSession,
    group_id: uuid.UUID,
    settlement_id: uuid.UUID,
    user_id: uuid.UUID,
) -> SettlementResponse:
    result = await db.execute(
        select(Settlement).where(
            Settlement.id == settlement_id,
            Settlement.group_id == group_id,
        )
    )
    settlement = result.scalar_one_or_none()
    if not settlement:
        raise NotFoundError("Settlement not found")

    if settlement.to_user != user_id:
        raise ForbiddenError("Only the payee can reject a settlement")

    if settlement.status != "pending":
        raise ValidationError(f"Settlement is already {settlement.status}")

    settlement.status = "rejected"
    await db.flush()

    await log_activity(
        db, group_id=group_id, actor_id=user_id, action="settlement_rejected",
        target_type="settlement", target_id=settlement.id,
        amount=settlement.amount, currency=settlement.currency,
    )

    user_map = await _load_user_names(db, [settlement.from_user, settlement.to_user])

    # Push 通知付款方：結算被拒絕
    from app.services.push_service import notify_settlement_rejected
    rejecter_name = user_map.get(user_id, "Unknown")
    await notify_settlement_rejected(
        db, settlement.from_user, rejecter_name, settlement.amount, settlement.currency, group_id,
    )

    return _build_response(settlement, user_map)


# ---------------------------------------------------------------------------
# 免除結算（被欠款人主動結清）
# ---------------------------------------------------------------------------

async def forgive_settlement(
    db: AsyncSession,
    group_id: uuid.UUID,
    to_user_id: uuid.UUID,
    from_user_id: uuid.UUID,
    amount: Decimal,
    currency: str,
) -> SettlementResponse:
    """被欠款人（債權人）主動結清債務，直接建立 confirmed settlement，
    並自動取消同一對同幣別的 pending settlement。"""
    if to_user_id == from_user_id:
        raise ValidationError("Cannot settle with yourself")

    await check_membership(db, group_id, to_user_id)
    await check_membership(db, group_id, from_user_id)

    # 建立直接確認的 settlement
    settlement = Settlement(
        group_id=group_id,
        from_user=from_user_id,
        to_user=to_user_id,
        amount=amount,
        currency=currency,
        status="confirmed",
        confirmed_at=datetime.now(timezone.utc),
    )
    db.add(settlement)
    await db.flush()

    # 自動取消同一對 (from→to) 同幣別的 pending settlements
    pending_result = await db.execute(
        select(Settlement).where(
            Settlement.group_id == group_id,
            Settlement.from_user == from_user_id,
            Settlement.to_user == to_user_id,
            Settlement.currency == currency,
            Settlement.status == "pending",
            Settlement.id != settlement.id,
        )
    )
    cancelled_ids = []
    for pending in pending_result.scalars().all():
        pending.status = "cancelled"
        cancelled_ids.append(pending.id)
    await db.flush()

    user_map = await _load_user_names(db, [from_user_id, to_user_id])
    creditor_name = user_map.get(to_user_id, "Unknown")

    await log_activity(
        db, group_id=group_id, actor_id=to_user_id, action="settlement_forgiven",
        target_type="settlement", target_id=settlement.id,
        amount=amount, currency=currency,
        extra_name=user_map.get(from_user_id, "Unknown"),
    )

    # Push 通知欠款方：債務已被免除
    from app.services.push_service import notify_settlement_forgiven
    await notify_settlement_forgiven(
        db, from_user_id, creditor_name, amount, currency, group_id,
    )

    return _build_response(settlement, user_map)


# ---------------------------------------------------------------------------
# 列出結算（群組內，支援 status filter）
# ---------------------------------------------------------------------------

async def list_settlements(
    db: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    status: str | None = None,
) -> list[SettlementResponse]:
    await check_membership(db, group_id, user_id)

    query = (
        select(Settlement)
        .where(Settlement.group_id == group_id)
        .options(selectinload(Settlement.payer), selectinload(Settlement.payee))
        .order_by(Settlement.settled_at.desc())
    )
    if status:
        query = query.where(Settlement.status == status)

    result = await db.execute(query)
    settlements = result.scalars().all()

    return [
        SettlementResponse(
            id=s.id,
            group_id=s.group_id,
            from_user=s.from_user,
            from_user_name=s.payer.display_name,
            to_user=s.to_user,
            to_user_name=s.payee.display_name,
            amount=s.amount,
            currency=s.currency,
            note=s.note,
            status=s.status,
            settled_at=s.settled_at,
            confirmed_at=s.confirmed_at,
            original_currency=s.original_currency,
            original_amount=s.original_amount,
            locked_rate=s.locked_rate,
        )
        for s in settlements
    ]


# ---------------------------------------------------------------------------
# 跨群組待確認結算列表
# ---------------------------------------------------------------------------

async def list_pending_settlements(
    db: AsyncSession, user_id: uuid.UUID
) -> list[SettlementResponse]:
    """列出所有待當前使用者確認的結算（跨群組）"""
    result = await db.execute(
        select(Settlement)
        .where(Settlement.to_user == user_id, Settlement.status == "pending")
        .options(
            selectinload(Settlement.payer),
            selectinload(Settlement.payee),
            selectinload(Settlement.group),
        )
        .order_by(Settlement.settled_at.desc())
    )
    settlements = result.scalars().all()

    return [
        SettlementResponse(
            id=s.id,
            group_id=s.group_id,
            group_name=s.group.name if s.group else None,
            from_user=s.from_user,
            from_user_name=s.payer.display_name,
            to_user=s.to_user,
            to_user_name=s.payee.display_name,
            amount=s.amount,
            currency=s.currency,
            note=s.note,
            status=s.status,
            settled_at=s.settled_at,
            confirmed_at=s.confirmed_at,
            original_currency=s.original_currency,
            original_amount=s.original_amount,
            locked_rate=s.locked_rate,
        )
        for s in settlements
    ]
