from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.expense import Expense
from app.models.group import Group, GroupMember
from app.models.settlement import Settlement
from app.models.user import User
from app.schemas.activity import ActivityItem

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityItem])
async def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """回傳目前使用者所有群組的最新活動（費用新增 + 結算完成），依時間排序。"""
    # 取得使用者所有群組 ID
    membership_result = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
    )
    group_ids = membership_result.scalars().all()
    if not group_ids:
        return []

    # 查費用（含 creator 和 group）
    expense_result = await db.execute(
        select(Expense)
        .where(Expense.group_id.in_(group_ids))
        .options(selectinload(Expense.creator), selectinload(Expense.group))
        .order_by(Expense.created_at.desc())
        .limit(limit * 2)
    )
    expenses = expense_result.scalars().all()

    # 查結算（含 payer、payee 和 group）
    settlement_result = await db.execute(
        select(Settlement)
        .where(Settlement.group_id.in_(group_ids))
        .options(
            selectinload(Settlement.payer),
            selectinload(Settlement.payee),
            selectinload(Settlement.group),
        )
        .order_by(Settlement.settled_at.desc())
        .limit(limit * 2)
    )
    settlements = settlement_result.scalars().all()

    # 合併轉換成 ActivityItem
    items: list[ActivityItem] = []

    for e in expenses:
        items.append(
            ActivityItem(
                type="expense_added",
                group_id=e.group_id,
                group_name=e.group.name,
                actor_name=e.creator.display_name,
                description=e.description,
                amount=e.total_amount,
                currency=e.currency,
                timestamp=e.created_at,
            )
        )

    for s in settlements:
        items.append(
            ActivityItem(
                type="settlement_created",
                group_id=s.group_id,
                group_name=s.group.name,
                actor_name=s.payer.display_name,
                to_name=s.payee.display_name,
                amount=s.amount,
                currency=s.currency,
                timestamp=s.settled_at,
            )
        )

    # 按時間降序排序，套用分頁
    items.sort(key=lambda x: x.timestamp, reverse=True)
    return items[skip : skip + limit]
