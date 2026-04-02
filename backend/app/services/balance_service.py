import uuid
from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.balance import (
    CurrencyBalance,
    CurrencyTotal,
    GroupBalanceSummary,
    OverallBalance,
    UserBalance,
)
from app.services.settlement_service import calculate_balances_by_currency


async def get_group_balances(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupBalanceSummary:
    """取得群組內每位成員的淨餘額（按幣別分列，不做匯率轉換）"""
    from app.services.group_service import check_membership
    await check_membership(db, group_id, user_id)

    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one()

    balances_map = await calculate_balances_by_currency(db, group_id)

    # 收集所有涉及的 user_id
    all_user_ids: set[uuid.UUID] = set()
    for balances in balances_map.values():
        all_user_ids.update(balances.keys())

    user_map: dict[uuid.UUID, str] = {}
    if all_user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(list(all_user_ids))))
        user_map = {u.id: u.display_name for u in user_result.scalars().all()}

    by_currency: list[CurrencyBalance] = []
    for cur in sorted(balances_map.keys()):
        balances = balances_map[cur]
        by_currency.append(CurrencyBalance(
            currency=cur,
            balances=[
                UserBalance(
                    user_id=uid,
                    display_name=user_map.get(uid, "Unknown"),
                    balance=bal,
                )
                for uid, bal in balances.items()
            ],
        ))

    return GroupBalanceSummary(
        group_id=group_id,
        group_name=group.name,
        by_currency=by_currency,
    )


async def get_overall_balances(
    db: AsyncSession, user_id: uuid.UUID
) -> OverallBalance:
    """取得使用者在所有群組的餘額總覽（按幣別分列，嚴禁跨幣別加總）"""
    member_result = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == user_id)
    )
    group_ids = [row[0] for row in member_result.all()]

    by_group: list[GroupBalanceSummary] = []
    # currency -> { owed_to_you, you_owe }
    currency_totals: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"owed_to_you": Decimal("0"), "you_owe": Decimal("0")}
    )

    for gid in group_ids:
        summary = await get_group_balances(db, gid, user_id)
        by_group.append(summary)

        # 從每個幣別池中找到當前使用者的餘額
        for cb in summary.by_currency:
            for ub in cb.balances:
                if ub.user_id == user_id:
                    if ub.balance > 0:
                        currency_totals[cb.currency]["owed_to_you"] += ub.balance
                    else:
                        currency_totals[cb.currency]["you_owe"] += abs(ub.balance)
                    break

    totals_by_currency = [
        CurrencyTotal(
            currency=cur,
            owed_to_you=totals["owed_to_you"],
            you_owe=totals["you_owe"],
            net_balance=totals["owed_to_you"] - totals["you_owe"],
        )
        for cur, totals in sorted(currency_totals.items())
    ]

    return OverallBalance(
        totals_by_currency=totals_by_currency,
        by_group=by_group,
    )
