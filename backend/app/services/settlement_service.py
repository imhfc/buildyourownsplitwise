import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError
from app.models.expense import Expense, ExpenseSplit
from app.models.group import Group
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.settlement import SettlementCreate, SettlementResponse, SettlementSuggestion
from app.services.exchange_rate_service import get_rate
from app.services.group_service import check_membership


async def calculate_balances(
    db: AsyncSession, group_id: uuid.UUID
) -> dict[uuid.UUID, Decimal]:
    """
    Calculate net balance for each user, converted to the group's base currency.
    Positive = others owe them. Negative = they owe others.
    """
    # 取得群組預設幣別
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()
    base_currency = group.default_currency

    balances: dict[uuid.UUID, Decimal] = defaultdict(Decimal)

    # 快取匯率，避免重複查詢同一幣別
    rate_cache: dict[str, Decimal] = {}

    async def to_base(amount: Decimal, currency: str) -> Decimal:
        """將金額轉換成群組 base currency"""
        currency = currency.upper()
        if currency == base_currency.upper():
            return amount
        if currency not in rate_cache:
            rate, _ = await get_rate(db, currency, base_currency)
            rate_cache[currency] = rate
        return round(amount * rate_cache[currency], 2)

    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id)
        .options(selectinload(Expense.splits))
    )
    expenses = result.scalars().all()

    for expense in expenses:
        converted_total = await to_base(expense.total_amount, expense.currency)
        balances[expense.paid_by] += converted_total
        for split in expense.splits:
            converted_split = await to_base(split.amount, expense.currency)
            balances[split.user_id] -= converted_split

    settlement_result = await db.execute(
        select(Settlement).where(Settlement.group_id == group_id)
    )
    settlements = settlement_result.scalars().all()

    for s in settlements:
        converted_amount = await to_base(s.amount, s.currency)
        balances[s.from_user] += converted_amount
        balances[s.to_user] -= converted_amount

    return {uid: bal for uid, bal in balances.items() if abs(bal) > Decimal("0.01")}


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


async def get_settlement_suggestions(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> list[SettlementSuggestion]:
    await check_membership(db, group_id, user_id)

    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()

    balances = await calculate_balances(db, group_id)
    if not balances:
        return []

    user_ids = list(balances.keys())
    user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    user_map = {u.id: u.display_name for u in user_result.scalars().all()}

    transactions = simplify_debts(balances)

    return [
        SettlementSuggestion(
            from_user_id=t["from"],
            from_user_name=user_map.get(t["from"], "Unknown"),
            to_user_id=t["to"],
            to_user_name=user_map.get(t["to"], "Unknown"),
            amount=t["amount"],
            currency=group.default_currency,
        )
        for t in transactions
    ]


async def create_settlement(
    db: AsyncSession,
    group_id: uuid.UUID,
    from_user_id: uuid.UUID,
    data: SettlementCreate,
) -> SettlementResponse:
    await check_membership(db, group_id, from_user_id)
    await check_membership(db, group_id, data.to_user)

    settlement = Settlement(
        group_id=group_id,
        from_user=from_user_id,
        to_user=data.to_user,
        amount=data.amount,
        currency=data.currency,
        note=data.note,
    )
    db.add(settlement)
    await db.flush()

    user_result = await db.execute(
        select(User).where(User.id.in_([from_user_id, data.to_user]))
    )
    users = {u.id: u.display_name for u in user_result.scalars().all()}

    return SettlementResponse(
        id=settlement.id,
        group_id=settlement.group_id,
        from_user=settlement.from_user,
        from_user_name=users.get(settlement.from_user, ""),
        to_user=settlement.to_user,
        to_user_name=users.get(settlement.to_user, ""),
        amount=settlement.amount,
        currency=settlement.currency,
        note=settlement.note,
        settled_at=settlement.settled_at,
    )


async def list_settlements(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> list[SettlementResponse]:
    await check_membership(db, group_id, user_id)
    result = await db.execute(
        select(Settlement)
        .where(Settlement.group_id == group_id)
        .options(selectinload(Settlement.payer), selectinload(Settlement.payee))
        .order_by(Settlement.settled_at.desc())
    )
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
            settled_at=s.settled_at,
        )
        for s in settlements
    ]
