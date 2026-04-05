import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.expense import Expense, ExpensePayer, ExpenseSplit
from app.models.group import Group
from app.models.settlement import Settlement
from app.schemas.expense import (
    ExpenseCreate, ExpensePayerInput, ExpensePayerResponse, ExpenseResponse, ExpenseSplitResponse,
    ExpenseUpdate, SettledInfo,
)
from app.services.activity_log_service import log_activity
from app.services.exchange_rate_service import get_rate
from app.services.group_service import check_membership, get_group_member_ids


def calculate_splits(data: ExpenseCreate, member_ids: list[uuid.UUID]) -> list[dict]:
    """Calculate how to split an expense based on the split method."""
    if data.split_method == "equal":
        split_user_ids = [s.user_id for s in data.splits] if data.splits else member_ids
        per_person = data.total_amount / len(split_user_ids)
        rounded = Decimal(str(round(per_person, 2)))
        total_rounded = rounded * len(split_user_ids)
        remainder = data.total_amount - total_rounded

        splits = []
        for i, uid in enumerate(split_user_ids):
            amt = rounded + remainder if i == 0 else rounded
            splits.append({"user_id": uid, "amount": amt})
        return splits

    elif data.split_method == "exact":
        if not data.splits:
            raise ValidationError("Exact split requires split amounts")
        total_split = sum(s.amount for s in data.splits if s.amount)
        if abs(total_split - data.total_amount) > Decimal("0.01"):
            raise ValidationError("Split amounts don't add up to total")
        return [{"user_id": s.user_id, "amount": s.amount} for s in data.splits]

    elif data.split_method in ("ratio", "shares"):
        if not data.splits:
            raise ValidationError("Ratio/shares split requires share values")
        total_shares = sum(s.shares for s in data.splits if s.shares)
        if total_shares <= 0:
            raise ValidationError("Total shares must be positive")
        splits = []
        running_total = Decimal("0")
        for i, s in enumerate(data.splits):
            if i == len(data.splits) - 1:
                amt = data.total_amount - running_total
            else:
                amt = round(data.total_amount * s.shares / total_shares, 2)
                running_total += amt
            splits.append({"user_id": s.user_id, "amount": amt, "shares": s.shares})
        return splits

    raise ValidationError(f"Unknown split method: {data.split_method}")


async def create_expense(
    db: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ExpenseCreate,
) -> ExpenseResponse:
    await check_membership(db, group_id, user_id)
    member_ids = await get_group_member_ids(db, group_id)

    # 驗證付款人
    if data.payers:
        payer_total = sum(p.amount for p in data.payers)
        if abs(payer_total - data.total_amount) > Decimal("0.01"):
            raise ValidationError("Payer amounts don't add up to total")
        for p in data.payers:
            if p.user_id not in member_ids:
                raise ValidationError("Payer is not a group member")
        primary_payer = data.payers[0].user_id
    else:
        if data.paid_by not in member_ids:
            raise ValidationError("Payer is not a group member")
        primary_payer = data.paid_by

    # 取得群組預設幣別作為 base_currency，並查即時匯率作為快照參考
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()
    base_currency = group.default_currency

    # currency 未指定時，fallback 到群組預設幣別
    expense_currency = (data.currency or base_currency).upper()

    if expense_currency != base_currency.upper():
        rate, _ = await get_rate(db, expense_currency, base_currency)
    else:
        rate = Decimal("1")

    expense = Expense(
        group_id=group_id,
        description=data.description,
        total_amount=data.total_amount,
        currency=expense_currency,
        base_currency=base_currency,
        exchange_rate_to_base=rate,
        paid_by=primary_payer,
        split_method=data.split_method,
        note=data.note,
        expense_date=data.expense_date,
        created_by=user_id,
    )
    db.add(expense)
    await db.flush()

    # 多人付款記錄
    if data.payers and len(data.payers) > 1:
        for p in data.payers:
            payer_record = ExpensePayer(
                expense_id=expense.id,
                user_id=p.user_id,
                amount=p.amount,
            )
            db.add(payer_record)

    splits = calculate_splits(data, member_ids)
    for s in splits:
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=s["user_id"],
            amount=s["amount"],
            shares=s.get("shares"),
        )
        db.add(split)
    await db.flush()

    await log_activity(
        db, group_id=group_id, actor_id=user_id, action="expense_added",
        target_type="expense", target_id=expense.id,
        description=data.description, amount=data.total_amount, currency=expense_currency,
    )

    # Push 通知所有參與者（排除建立者自己）
    from app.services.push_service import notify_expense_added
    from app.models.user import User
    creator_result = await db.execute(select(User.display_name).where(User.id == user_id))
    creator_name = creator_result.scalar_one_or_none() or "Unknown"
    notified_ids = {s["user_id"] for s in splits} - {user_id}
    for uid in notified_ids:
        await notify_expense_added(
            db, uid, creator_name, data.description, data.total_amount, expense_currency, group_id,
        )

    return await get_expense_detail(db, expense.id)


async def _get_last_confirmed_settlement(
    db: AsyncSession, group_id: uuid.UUID
) -> Settlement | None:
    """取得群組中最後一次 confirmed 的 settlement。"""
    result = await db.execute(
        select(Settlement)
        .where(
            Settlement.group_id == group_id,
            Settlement.status == "confirmed",
        )
        .options(selectinload(Settlement.payer))
        .order_by(Settlement.confirmed_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def check_expense_settled(
    db: AsyncSession, group_id: uuid.UUID, expense_created_at: datetime
) -> bool:
    """檢查某筆消費是否已被結清覆蓋。
    只有群組所有餘額歸零時，cutoff 之前的消費才算已結清。"""
    last = await _get_last_confirmed_settlement(db, group_id)
    if not last or not last.confirmed_at:
        return False
    if expense_created_at > last.confirmed_at:
        return False
    from app.services.settlement_service import calculate_balances
    current_balances = await calculate_balances(db, group_id)
    return len(current_balances) == 0


async def list_expenses(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> list[ExpenseResponse]:
    await check_membership(db, group_id, user_id)
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
        .options(
            selectinload(Expense.splits).selectinload(ExpenseSplit.user),
            selectinload(Expense.payer),
            selectinload(Expense.payers).selectinload(ExpensePayer.user),
        )
        .order_by(Expense.created_at.desc())
    )
    expenses = result.scalars().all()

    # 查詢最後一次 confirmed settlement 作為結清分界線
    last_settlement = await _get_last_confirmed_settlement(db, group_id)
    settled_info = None
    cutoff: datetime | None = None
    if last_settlement and last_settlement.confirmed_at:
        # 只有群組所有餘額歸零時，才標記 cutoff 之前的消費為已結清
        # 避免部分結清（如免除 A→B 債務）把不相關的消費也標為已結清
        from app.services.settlement_service import calculate_balances
        current_balances = await calculate_balances(db, group_id)
        if len(current_balances) == 0:
            cutoff = last_settlement.confirmed_at
            settled_info = SettledInfo(
                settled_by=last_settlement.payer.display_name,
                settled_at=last_settlement.confirmed_at,
            )

    return [
        format_expense(e, is_settled=(cutoff is not None and e.created_at <= cutoff), settled_info=settled_info)
        for e in expenses
    ]


async def delete_expense(
    db: AsyncSession, group_id: uuid.UUID, expense_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await check_membership(db, group_id, user_id)
    result = await db.execute(select(Expense).where(Expense.id == expense_id, Expense.deleted_at.is_(None)))
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundError("Expense not found")
    if expense.created_by != user_id:
        raise ForbiddenError("Only creator can delete expense")
    if await check_expense_settled(db, group_id, expense.created_at):
        raise ValidationError("Cannot delete a settled expense")
    expense.deleted_at = datetime.now(timezone.utc)

    await log_activity(
        db, group_id=group_id, actor_id=user_id, action="expense_deleted",
        target_type="expense", target_id=expense_id,
        description=expense.description, amount=expense.total_amount, currency=expense.currency,
    )

    # Push 通知群組所有成員（排除刪除者自己）
    from app.services.push_service import notify_expense_deleted
    from app.models.user import User
    deleter_result = await db.execute(select(User.display_name).where(User.id == user_id))
    deleter_name = deleter_result.scalar_one_or_none() or "Unknown"
    await notify_expense_deleted(db, group_id, user_id, deleter_name, expense.description)


async def _update_expense_in_place(
    db: AsyncSession,
    expense: Expense,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ExpenseUpdate,
    member_ids: list[uuid.UUID],
) -> ExpenseResponse:
    """直接修改未結清消費（原地更新）。"""
    # Update non-None fields
    if data.description is not None:
        expense.description = data.description
    if data.note is not None:
        expense.note = data.note
    if data.expense_date is not None:
        expense.expense_date = data.expense_date
    # 處理付款人更新
    if data.payers is not None:
        payer_total = sum(p.amount for p in data.payers)
        if abs(payer_total - (data.total_amount or expense.total_amount)) > Decimal("0.01"):
            raise ValidationError("Payer amounts don't add up to total")
        for p in data.payers:
            if p.user_id not in member_ids:
                raise ValidationError("Payer is not a group member")
        expense.paid_by = data.payers[0].user_id
        # 刪除舊的 payers
        old_payers = await db.execute(
            select(ExpensePayer).where(ExpensePayer.expense_id == expense.id)
        )
        for op in old_payers.scalars().all():
            await db.delete(op)
        # 多人付款才寫入
        if len(data.payers) > 1:
            for p in data.payers:
                db.add(ExpensePayer(
                    expense_id=expense.id, user_id=p.user_id, amount=p.amount,
                ))
    elif data.paid_by is not None:
        if data.paid_by not in member_ids:
            raise ValidationError("Payer is not a group member")
        expense.paid_by = data.paid_by
        # 清除多人付款記錄
        old_payers = await db.execute(
            select(ExpensePayer).where(ExpensePayer.expense_id == expense.id)
        )
        for op in old_payers.scalars().all():
            await db.delete(op)

    # Get group for default currency
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()
    base_currency = group.default_currency

    # Handle currency and amount changes
    if data.currency is not None:
        expense_currency = data.currency.upper()
        if expense_currency != base_currency.upper():
            rate, _ = await get_rate(db, expense_currency, base_currency)
        else:
            rate = Decimal("1")
        expense.currency = expense_currency
        expense.exchange_rate_to_base = rate

    if data.total_amount is not None:
        expense.total_amount = data.total_amount

    if data.split_method is not None:
        expense.split_method = data.split_method

    # If splits data provided, recalculate
    if data.splits is not None or data.split_method is not None or data.total_amount is not None:
        # Delete old splits
        result = await db.execute(
            select(ExpenseSplit).where(ExpenseSplit.expense_id == expense.id)
        )
        for split in result.scalars().all():
            await db.delete(split)
        await db.flush()

        # Build a temporary ExpenseCreate for calculate_splits
        split_data = ExpenseCreate(
            description=expense.description,
            total_amount=expense.total_amount,
            paid_by=expense.paid_by,
            split_method=expense.split_method,
            splits=data.splits or [],
        )

        splits = calculate_splits(split_data, member_ids)
        for s in splits:
            new_split = ExpenseSplit(
                expense_id=expense.id,
                user_id=s["user_id"],
                amount=s["amount"],
                shares=s.get("shares"),
            )
            db.add(new_split)

    await db.flush()

    await log_activity(
        db, group_id=group_id, actor_id=user_id, action="expense_updated",
        target_type="expense", target_id=expense.id,
        description=expense.description, amount=expense.total_amount, currency=expense.currency,
    )

    # Push 通知群組所有成員（排除更新者自己）
    from app.services.push_service import notify_expense_updated
    from app.models.user import User
    updater_result = await db.execute(select(User.display_name).where(User.id == user_id))
    updater_name = updater_result.scalar_one_or_none() or "Unknown"
    await notify_expense_updated(
        db, group_id, user_id, updater_name, expense.description, expense.total_amount, expense.currency,
    )

    # Expire the expense so get_expense_detail reloads from DB with proper eager loading.
    expense_id = expense.id
    db.expire(expense)

    return await get_expense_detail(db, expense_id)


async def _adjust_settled_expense(
    db: AsyncSession,
    original: Expense,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ExpenseUpdate,
    member_ids: list[uuid.UUID],
) -> ExpenseResponse:
    """沖銷+重建：軟刪除原始已結清消費，建立一筆新消費取代之。"""
    # 軟刪除原始消費（從餘額計算中移除）
    original_id = original.id
    original_desc = original.description
    original.deleted_at = datetime.now(timezone.utc)

    # 合併原始值與更新值，決定新消費的欄位
    new_description = data.description if data.description is not None else original.description
    new_total = data.total_amount if data.total_amount is not None else original.total_amount
    new_currency = data.currency if data.currency is not None else original.currency
    new_split_method = data.split_method if data.split_method is not None else original.split_method
    new_note = data.note if data.note is not None else original.note
    new_expense_date = data.expense_date if data.expense_date is not None else original.expense_date

    # 決定付款人
    if data.payers is not None:
        payer_total = sum(p.amount for p in data.payers)
        if abs(payer_total - new_total) > Decimal("0.01"):
            raise ValidationError("Payer amounts don't add up to total")
        for p in data.payers:
            if p.user_id not in member_ids:
                raise ValidationError("Payer is not a group member")
        primary_payer = data.payers[0].user_id
        payers_data = data.payers
    elif data.paid_by is not None:
        if data.paid_by not in member_ids:
            raise ValidationError("Payer is not a group member")
        primary_payer = data.paid_by
        payers_data = None
    else:
        primary_payer = original.paid_by
        # 保留原始的多人付款資料
        if original.payers:
            payers_data = [
                ExpensePayerInput(user_id=p.user_id, amount=p.amount)
                for p in original.payers
            ]
        else:
            payers_data = None

    # 取得匯率
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()
    base_currency = group.default_currency
    expense_currency = new_currency.upper()

    if expense_currency != base_currency.upper():
        rate, _ = await get_rate(db, expense_currency, base_currency)
    else:
        rate = Decimal("1")

    # 建立新消費，記錄來源
    new_expense = Expense(
        group_id=group_id,
        description=new_description,
        total_amount=new_total,
        currency=expense_currency,
        base_currency=base_currency,
        exchange_rate_to_base=rate,
        paid_by=primary_payer,
        split_method=new_split_method,
        note=new_note,
        expense_date=new_expense_date,
        created_by=user_id,
        adjusted_from_id=original_id,
    )
    db.add(new_expense)
    await db.flush()

    # 多人付款記錄
    if payers_data and len(payers_data) > 1:
        for p in payers_data:
            db.add(ExpensePayer(
                expense_id=new_expense.id, user_id=p.user_id, amount=p.amount,
            ))

    # 計算分帳
    split_data = ExpenseCreate(
        description=new_description,
        total_amount=new_total,
        paid_by=primary_payer,
        split_method=new_split_method,
        splits=data.splits or [],
    )
    splits = calculate_splits(split_data, member_ids)
    for s in splits:
        db.add(ExpenseSplit(
            expense_id=new_expense.id,
            user_id=s["user_id"],
            amount=s["amount"],
            shares=s.get("shares"),
        ))

    await db.flush()

    await log_activity(
        db, group_id=group_id, actor_id=user_id, action="expense_adjusted",
        target_type="expense", target_id=new_expense.id,
        description=new_description, amount=new_total, currency=expense_currency,
    )

    # Push 通知
    from app.services.push_service import notify_expense_updated
    from app.models.user import User
    updater_result = await db.execute(select(User.display_name).where(User.id == user_id))
    updater_name = updater_result.scalar_one_or_none() or "Unknown"
    await notify_expense_updated(
        db, group_id, user_id, updater_name, new_description, new_total, expense_currency,
    )

    return await get_expense_detail(db, new_expense.id)


async def update_expense(
    db: AsyncSession,
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ExpenseUpdate,
) -> ExpenseResponse:
    await check_membership(db, group_id, user_id)
    member_ids = await get_group_member_ids(db, group_id)

    result = await db.execute(
        select(Expense)
        .where(Expense.id == expense_id, Expense.deleted_at.is_(None))
        .options(selectinload(Expense.splits), selectinload(Expense.payers))
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundError("Expense not found")

    # Allow any involved member (payer or split participant) to update
    involved_user_ids = {expense.paid_by} | {s.user_id for s in expense.splits}
    if user_id not in involved_user_ids:
        raise ForbiddenError("Only involved members can update expense")

    is_settled = await check_expense_settled(db, group_id, expense.created_at)

    if is_settled:
        # 沖銷+重建：軟刪除原始消費，建立新消費取代
        return await _adjust_settled_expense(db, expense, group_id, user_id, data, member_ids)
    else:
        # 一般更新：原地修改
        return await _update_expense_in_place(db, expense, group_id, user_id, data, member_ids)


async def get_expense_detail(
    db: AsyncSession, expense_id: uuid.UUID, group_id: uuid.UUID | None = None
) -> ExpenseResponse:
    conditions = [Expense.id == expense_id, Expense.deleted_at.is_(None)]
    if group_id is not None:
        conditions.append(Expense.group_id == group_id)
    result = await db.execute(
        select(Expense)
        .where(*conditions)
        .options(
            selectinload(Expense.splits).selectinload(ExpenseSplit.user),
            selectinload(Expense.payer),
            selectinload(Expense.payers).selectinload(ExpensePayer.user),
        )
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundError("Expense not found")
    return format_expense(expense)


def format_expense(
    e: Expense,
    is_settled: bool = False,
    settled_info: SettledInfo | None = None,
) -> ExpenseResponse:
    base_amount = round(e.total_amount * e.exchange_rate_to_base, 2)
    return ExpenseResponse(
        id=e.id,
        group_id=e.group_id,
        description=e.description,
        total_amount=e.total_amount,
        currency=e.currency,
        exchange_rate_to_base=e.exchange_rate_to_base,
        base_currency=e.base_currency,
        base_amount=base_amount,
        paid_by=e.paid_by,
        payer_display_name=e.payer.display_name,
        payers=[
            ExpensePayerResponse(
                user_id=p.user_id,
                user_display_name=p.user.display_name,
                amount=p.amount,
            )
            for p in e.payers
        ] if e.payers else [],
        split_method=e.split_method,
        splits=[
            ExpenseSplitResponse(
                user_id=s.user_id,
                user_display_name=s.user.display_name,
                amount=s.amount,
                shares=s.shares,
            )
            for s in e.splits
        ],
        note=e.note,
        receipt_image_url=e.receipt_image_url,
        expense_date=e.expense_date,
        created_at=e.created_at,
        is_settled=is_settled,
        settled_info=settled_info if is_settled else None,
        adjusted_from_id=e.adjusted_from_id,
    )
