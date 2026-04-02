import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy.orm import selectinload

from app.models.activity_log import ActivityLog, ActivityRead
from app.models.group import Group, GroupMember
from app.schemas.activity import ActivityItem


async def log_activity(
    db: AsyncSession,
    group_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    target_type: str | None = None,
    target_id: uuid.UUID | None = None,
    description: str | None = None,
    amount: Decimal | None = None,
    currency: str | None = None,
    extra_name: str | None = None,
) -> None:
    """記錄一筆活動紀錄。"""
    log = ActivityLog(
        group_id=group_id,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        description=description,
        amount=amount,
        currency=currency,
        extra_name=extra_name,
    )
    db.add(log)
    await db.flush()


async def list_user_activities(
    db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 20
) -> list[ActivityItem]:
    """取得使用者所有群組的最新活動（排除已刪除群組）。"""
    membership_result = await db.execute(
        select(GroupMember.group_id)
        .join(Group, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == user_id, Group.deleted_at.is_(None))
    )
    group_ids = membership_result.scalars().all()
    if not group_ids:
        return []

    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.group_id.in_(group_ids))
        .options(selectinload(ActivityLog.actor), selectinload(ActivityLog.group))
        .order_by(ActivityLog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()

    return [
        ActivityItem(
            id=log.id,
            type=log.action,
            group_id=log.group_id,
            group_name=log.group.name,
            actor_name=log.actor.display_name,
            description=log.description,
            to_name=log.extra_name,
            amount=log.amount,
            currency=log.currency,
            timestamp=log.created_at,
        )
        for log in logs
    ]


async def get_unread_count(db: AsyncSession, user_id: uuid.UUID) -> int:
    """取得使用者的未讀活動數量。"""
    # 取得使用者所屬群組
    membership_result = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == user_id)
    )
    group_ids = membership_result.scalars().all()
    if not group_ids:
        return 0

    # 取得使用者的 last_read_at
    read_result = await db.execute(
        select(ActivityRead.last_read_at).where(ActivityRead.user_id == user_id)
    )
    last_read_at = read_result.scalar_one_or_none()

    # 計算未讀數量
    query = select(func.count()).select_from(ActivityLog).where(
        ActivityLog.group_id.in_(group_ids)
    )
    if last_read_at is not None:
        query = query.where(ActivityLog.created_at > last_read_at)

    result = await db.execute(query)
    return result.scalar_one()


async def mark_activities_read(db: AsyncSession, user_id: uuid.UUID) -> None:
    """將使用者的活動標記為已讀（更新 last_read_at）。"""
    now = datetime.now(timezone.utc)
    existing = await db.get(ActivityRead, user_id)
    if existing:
        existing.last_read_at = now
    else:
        db.add(ActivityRead(user_id=user_id, last_read_at=now))
    await db.flush()
