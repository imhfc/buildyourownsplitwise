import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, ValidationError
from app.models.reminder import PaymentReminder
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.activity_log_service import log_activity
from app.services.group_service import check_membership


async def create_reminder(
    db: AsyncSession,
    group_id: uuid.UUID,
    from_user_id: uuid.UUID,
    data: ReminderCreate,
) -> ReminderResponse:
    """建立付款提醒，同一對象 24 小時內只能發送一次"""
    await check_membership(db, group_id, from_user_id)
    await check_membership(db, group_id, data.to_user)

    if from_user_id == data.to_user:
        raise ValidationError("Cannot remind yourself")

    # 24 小時頻率限制
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    existing = await db.execute(
        select(PaymentReminder).where(
            PaymentReminder.group_id == group_id,
            PaymentReminder.from_user == from_user_id,
            PaymentReminder.to_user == data.to_user,
            PaymentReminder.created_at > cutoff,
        )
    )
    if existing.scalar_one_or_none():
        raise ValidationError("Already sent a reminder to this user within 24 hours")

    reminder = PaymentReminder(
        group_id=group_id,
        from_user=from_user_id,
        to_user=data.to_user,
        amount=data.amount,
        currency=data.currency,
    )
    db.add(reminder)
    await db.flush()

    # 記錄活動
    to_user_result = await db.execute(select(User.display_name).where(User.id == data.to_user))
    to_name = to_user_result.scalar_one_or_none() or "Unknown"

    await log_activity(
        db, group_id=group_id, actor_id=from_user_id, action="reminder_sent",
        target_type="reminder", target_id=reminder.id,
        amount=data.amount, currency=data.currency, extra_name=to_name,
    )

    # 載入使用者名稱
    from_result = await db.execute(select(User.display_name).where(User.id == from_user_id))
    from_name = from_result.scalar_one_or_none() or "Unknown"

    # 發送 Push 通知
    from app.services.push_service import notify_reminder
    await notify_reminder(db, data.to_user, from_name, data.amount, data.currency, group_id)

    return ReminderResponse(
        id=reminder.id,
        group_id=group_id,
        from_user=from_user_id,
        from_user_name=from_name,
        to_user=data.to_user,
        to_user_name=to_name,
        amount=data.amount,
        currency=data.currency,
        created_at=reminder.created_at,
    )


async def create_batch_reminders(
    db: AsyncSession,
    group_id: uuid.UUID,
    from_user_id: uuid.UUID,
    reminders: list[ReminderCreate],
) -> tuple[list[ReminderResponse], list[dict]]:
    """批次發送付款提醒，跳過 24 小時內已提醒或無效的對象"""
    sent: list[ReminderResponse] = []
    skipped: list[dict] = []

    for item in reminders:
        try:
            result = await create_reminder(db, group_id, from_user_id, item)
            sent.append(result)
        except (ValidationError, ForbiddenError) as e:
            skipped.append({"to_user": str(item.to_user), "reason": str(e)})

    return sent, skipped
