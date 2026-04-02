import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.expense import Expense, ExpensePayer, ExpenseSplit
from app.models.group import Group
from app.schemas.expense import (
    ExpenseCreate, ExpensePayerResponse, ExpenseResponse, ExpenseSplitResponse, ExpenseUpdate,
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
    return [format_expense(e) for e in expenses]


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
    expense.deleted_at = datetime.now(timezone.utc)

    await log_activity(
        db, group_id=group_id, actor_id=user_id, action="expense_deleted",
        target_type="expense", target_id=expense_id,
        description=expense.description, amount=expense.total_amount, currency=expense.currency,
    )


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
        .options(selectinload(Expense.splits))
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise NotFoundError("Expense not found")

    # Allow any involved member (payer or split participant) to update
    involved_user_ids = {expense.paid_by} | {s.user_id for s in expense.splits}
    if user_id not in involved_user_ids:
        raise ForbiddenError("Only involved members can update expense")

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

    return await get_expense_detail(db, expense.id)


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


def format_expense(e: Expense) -> ExpenseResponse:
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
    )
