import uuid
from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.expense import Expense, ExpenseSplit
from app.models.group import Group, GroupMember
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.expense import SettlementCreate, SettlementResponse, SettlementSuggestion

router = APIRouter(prefix="/groups/{group_id}/settlements", tags=["settlements"])


async def _check_membership(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID):
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not a member of this group")


@router.get("/suggestions", response_model=list[SettlementSuggestion])
async def get_settlement_suggestions(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate who owes whom using debt simplification algorithm."""
    await _check_membership(db, group_id, current_user.id)

    # Get group info
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()

    # Build net balance for each user
    balances = await _calculate_balances(db, group_id)

    if not balances:
        return []

    # Get user names
    user_ids = list(balances.keys())
    user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
    user_map = {u.id: u.display_name for u in user_result.scalars().all()}

    # Simplify debts
    transactions = _simplify_debts(balances)

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


async def _calculate_balances(
    db: AsyncSession, group_id: uuid.UUID
) -> dict[uuid.UUID, Decimal]:
    """
    Calculate net balance for each user.
    Positive = others owe them. Negative = they owe others.
    """
    balances: dict[uuid.UUID, Decimal] = defaultdict(Decimal)

    # Get all expenses with splits
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id)
        .options(selectinload(Expense.splits))
    )
    expenses = result.scalars().all()

    for expense in expenses:
        # Payer paid the full amount (credit)
        balances[expense.paid_by] += expense.total_amount

        # Each split user owes their share (debit)
        for split in expense.splits:
            balances[split.user_id] -= split.amount

    # Account for existing settlements
    settlement_result = await db.execute(
        select(Settlement).where(Settlement.group_id == group_id)
    )
    settlements = settlement_result.scalars().all()

    for s in settlements:
        balances[s.from_user] += s.amount  # payer reduces their debt
        balances[s.to_user] -= s.amount    # payee reduces their credit

    # Remove zero balances
    return {uid: bal for uid, bal in balances.items() if abs(bal) > Decimal("0.01")}


def _simplify_debts(balances: dict[uuid.UUID, Decimal]) -> list[dict]:
    """
    Minimize number of transactions using greedy algorithm.
    Match largest creditor with largest debtor.
    """
    debtors = []  # (user_id, amount_they_owe) — negative balance
    creditors = []  # (user_id, amount_owed_to_them) — positive balance

    for uid, balance in balances.items():
        if balance < 0:
            debtors.append([uid, -balance])  # make positive for easier math
        elif balance > 0:
            creditors.append([uid, balance])

    # Sort by amount descending
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


@router.post("", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def create_settlement(
    group_id: uuid.UUID,
    data: SettlementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record that current user paid someone."""
    await _check_membership(db, group_id, current_user.id)
    await _check_membership(db, group_id, data.to_user)

    settlement = Settlement(
        group_id=group_id,
        from_user=current_user.id,
        to_user=data.to_user,
        amount=data.amount,
        currency=data.currency,
        note=data.note,
    )
    db.add(settlement)
    await db.flush()

    # Fetch with relationships
    user_result = await db.execute(select(User).where(User.id.in_([current_user.id, data.to_user])))
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


@router.get("", response_model=list[SettlementResponse])
async def list_settlements(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_membership(db, group_id, current_user.id)
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
