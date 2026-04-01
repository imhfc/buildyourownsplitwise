import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.balance import GroupBalanceSummary, OverallBalance, UserBalance
from app.services.settlement_service import calculate_balances


async def get_group_balances(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupBalanceSummary:
    """取得群組內每位成員的淨餘額"""
    from app.services.group_service import check_membership
    await check_membership(db, group_id, user_id)

    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()

    balances = await calculate_balances(db, group_id)

    user_ids = list(balances.keys())
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        user_map = {u.id: u.display_name for u in user_result.scalars().all()}
    else:
        user_map = {}

    return GroupBalanceSummary(
        group_id=group_id,
        group_name=group.name,
        currency=group.default_currency,
        balances=[
            UserBalance(
                user_id=uid,
                display_name=user_map.get(uid, "Unknown"),
                balance=bal,
            )
            for uid, bal in balances.items()
        ],
    )


async def get_overall_balances(
    db: AsyncSession, user_id: uuid.UUID
) -> OverallBalance:
    """取得使用者在所有群組的餘額總覽"""
    # 查使用者所屬的所有群組
    member_result = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == user_id)
    )
    group_ids = [row[0] for row in member_result.all()]

    # 取得使用者偏好幣別
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    preferred_currency = user.preferred_currency or "TWD"

    by_group: list[GroupBalanceSummary] = []
    total_owed_to_you = Decimal("0")
    total_you_owe = Decimal("0")

    for gid in group_ids:
        summary = await get_group_balances(db, gid, user_id)
        by_group.append(summary)

        # 找到當前使用者在這個群組的餘額
        for ub in summary.balances:
            if ub.user_id == user_id:
                if ub.balance > 0:
                    total_owed_to_you += ub.balance
                else:
                    total_you_owe += abs(ub.balance)
                break

    return OverallBalance(
        total_owed_to_you=total_owed_to_you,
        total_you_owe=total_you_owe,
        net_balance=total_owed_to_you - total_you_owe,
        currency=preferred_currency,
        by_group=by_group,
    )
