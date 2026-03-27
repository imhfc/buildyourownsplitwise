import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.expense import Expense, ExpenseSplit
from app.models.group import GroupMember
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseSplitResponse

router = APIRouter(prefix="/groups/{group_id}/expenses", tags=["expenses"])


async def _check_membership(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID):
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this group")


async def _get_group_member_ids(db: AsyncSession, group_id: uuid.UUID) -> list[uuid.UUID]:
    result = await db.execute(
        select(GroupMember.user_id).where(GroupMember.group_id == group_id)
    )
    return [row[0] for row in result.all()]


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    group_id: uuid.UUID,
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_membership(db, group_id, current_user.id)
    member_ids = await _get_group_member_ids(db, group_id)

    # Validate payer is a member
    if data.paid_by not in member_ids:
        raise HTTPException(status_code=400, detail="Payer is not a group member")

    expense = Expense(
        group_id=group_id,
        description=data.description,
        total_amount=data.total_amount,
        currency=data.currency,
        paid_by=data.paid_by,
        split_method=data.split_method,
        note=data.note,
        created_by=current_user.id,
    )
    db.add(expense)
    await db.flush()

    # Calculate splits based on method
    splits = _calculate_splits(data, member_ids)
    for s in splits:
        split = ExpenseSplit(
            expense_id=expense.id,
            user_id=s["user_id"],
            amount=s["amount"],
            shares=s.get("shares"),
        )
        db.add(split)
    await db.flush()

    return await _get_expense_detail(db, expense.id)


def _calculate_splits(data: ExpenseCreate, member_ids: list[uuid.UUID]) -> list[dict]:
    if data.split_method == "equal":
        # Split equally among all specified users, or all members if none specified
        split_user_ids = [s.user_id for s in data.splits] if data.splits else member_ids
        per_person = data.total_amount / len(split_user_ids)
        # Handle rounding: give remainder to first person
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
            raise HTTPException(status_code=400, detail="Exact split requires split amounts")
        total_split = sum(s.amount for s in data.splits if s.amount)
        if abs(total_split - data.total_amount) > Decimal("0.01"):
            raise HTTPException(status_code=400, detail="Split amounts don't add up to total")
        return [{"user_id": s.user_id, "amount": s.amount} for s in data.splits]

    elif data.split_method in ("ratio", "shares"):
        if not data.splits:
            raise HTTPException(status_code=400, detail="Ratio/shares split requires share values")
        total_shares = sum(s.shares for s in data.splits if s.shares)
        if total_shares <= 0:
            raise HTTPException(status_code=400, detail="Total shares must be positive")
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

    raise HTTPException(status_code=400, detail=f"Unknown split method: {data.split_method}")


@router.get("", response_model=list[ExpenseResponse])
async def list_expenses(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_membership(db, group_id, current_user.id)
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id)
        .options(
            selectinload(Expense.splits).selectinload(ExpenseSplit.user),
            selectinload(Expense.payer),
        )
        .order_by(Expense.created_at.desc())
    )
    expenses = result.scalars().all()
    return [_format_expense(e) for e in expenses]


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_membership(db, group_id, current_user.id)
    return await _get_expense_detail(db, expense_id)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_membership(db, group_id, current_user.id)
    result = await db.execute(select(Expense).where(Expense.id == expense_id))
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if expense.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can delete expense")
    await db.delete(expense)


def _format_expense(e: Expense) -> ExpenseResponse:
    return ExpenseResponse(
        id=e.id,
        group_id=e.group_id,
        description=e.description,
        total_amount=e.total_amount,
        currency=e.currency,
        exchange_rate_to_base=e.exchange_rate_to_base,
        base_currency=e.base_currency,
        paid_by=e.paid_by,
        payer_display_name=e.payer.display_name,
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
        created_at=e.created_at,
    )


async def _get_expense_detail(db: AsyncSession, expense_id: uuid.UUID) -> ExpenseResponse:
    result = await db.execute(
        select(Expense)
        .where(Expense.id == expense_id)
        .options(
            selectinload(Expense.splits).selectinload(ExpenseSplit.user),
            selectinload(Expense.payer),
        )
    )
    expense = result.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return _format_expense(expense)
