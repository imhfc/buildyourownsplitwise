"""Expo Push Notification 基礎架構"""
import uuid
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_push(
    db: AsyncSession,
    to_user_id: uuid.UUID,
    title: str,
    body: str,
    data: dict | None = None,
) -> bool:
    """發送 push notification 給指定使用者（若已註冊 push token）"""
    result = await db.execute(
        select(User.push_token).where(User.id == to_user_id)
    )
    token = result.scalar_one_or_none()
    if not token:
        return False

    message = {
        "to": token,
        "title": title,
        "body": body,
        "sound": "default",
    }
    if data:
        message["data"] = data

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(EXPO_PUSH_URL, json=message, timeout=10)
            return resp.status_code == 200
    except Exception:
        return False


async def notify_group_members(
    db: AsyncSession,
    group_id: uuid.UUID,
    exclude_user_id: uuid.UUID,
    title: str,
    body: str,
    notification_type: str,
) -> None:
    """通知群組所有成員（排除操作者自己）"""
    from app.models.group import GroupMember
    result = await db.execute(
        select(GroupMember.user_id).where(GroupMember.group_id == group_id)
    )
    member_ids = {row[0] for row in result.all()} - {exclude_user_id}
    for uid in member_ids:
        await send_push(db, uid, title, body, data={
            "type": notification_type,
            "group_id": str(group_id),
        })


async def notify_reminder(
    db: AsyncSession,
    to_user_id: uuid.UUID,
    from_user_name: str,
    amount: Decimal,
    currency: str,
    group_id: uuid.UUID,
) -> bool:
    """付款提醒 push notification"""
    title = "Payment Reminder"
    body = f"{from_user_name} reminds you to pay {currency} {amount}"
    return await send_push(db, to_user_id, title, body, data={
        "type": "reminder",
        "group_id": str(group_id),
    })


async def notify_expense_added(
    db: AsyncSession,
    to_user_id: uuid.UUID,
    actor_name: str,
    description: str,
    amount: Decimal,
    currency: str,
    group_id: uuid.UUID,
) -> bool:
    """新增消費 push notification"""
    title = "New Expense"
    body = f"{actor_name} added {currency} {amount} - {description}"
    return await send_push(db, to_user_id, title, body, data={
        "type": "expense_added",
        "group_id": str(group_id),
    })


async def notify_expense_updated(
    db: AsyncSession,
    group_id: uuid.UUID,
    actor_id: uuid.UUID,
    actor_name: str,
    description: str,
    amount: Decimal,
    currency: str,
) -> None:
    """消費更新 push notification — 通知群組所有成員"""
    await notify_group_members(
        db, group_id, actor_id,
        title="Expense Updated",
        body=f"{actor_name} updated {currency} {amount} - {description}",
        notification_type="expense_updated",
    )


async def notify_expense_deleted(
    db: AsyncSession,
    group_id: uuid.UUID,
    actor_id: uuid.UUID,
    actor_name: str,
    description: str,
) -> None:
    """消費刪除 push notification — 通知群組所有成員"""
    await notify_group_members(
        db, group_id, actor_id,
        title="Expense Deleted",
        body=f"{actor_name} deleted expense: {description}",
        notification_type="expense_deleted",
    )


async def notify_settlement(
    db: AsyncSession,
    to_user_id: uuid.UUID,
    from_user_name: str,
    amount: Decimal,
    currency: str,
    group_id: uuid.UUID,
) -> bool:
    """結算 push notification"""
    title = "Settlement"
    body = f"{from_user_name} paid you {currency} {amount}"
    return await send_push(db, to_user_id, title, body, data={
        "type": "settlement",
        "group_id": str(group_id),
    })


async def notify_settlement_confirmed(
    db: AsyncSession,
    to_user_id: uuid.UUID,
    confirmer_name: str,
    amount: Decimal,
    currency: str,
    group_id: uuid.UUID,
) -> None:
    """結算確認 push notification — 通知付款方"""
    await send_push(db, to_user_id, "Settlement Confirmed",
                    f"{confirmer_name} confirmed your {currency} {amount} payment",
                    data={"type": "settlement_confirmed", "group_id": str(group_id)})


async def notify_settlement_rejected(
    db: AsyncSession,
    to_user_id: uuid.UUID,
    rejecter_name: str,
    amount: Decimal,
    currency: str,
    group_id: uuid.UUID,
) -> None:
    """結算拒絕 push notification — 通知付款方"""
    await send_push(db, to_user_id, "Settlement Rejected",
                    f"{rejecter_name} rejected your {currency} {amount} payment",
                    data={"type": "settlement_rejected", "group_id": str(group_id)})


async def notify_member_joined(
    db: AsyncSession,
    group_id: uuid.UUID,
    new_member_id: uuid.UUID,
    member_name: str,
    group_name: str,
) -> None:
    """成員加入 push notification — 通知群組所有其他成員"""
    await notify_group_members(
        db, group_id, new_member_id,
        title="New Member",
        body=f"{member_name} joined {group_name}",
        notification_type="member_joined",
    )


async def notify_member_removed(
    db: AsyncSession,
    to_user_id: uuid.UUID,
    group_name: str,
    group_id: uuid.UUID,
) -> None:
    """成員被移除 push notification — 通知被移除的成員"""
    await send_push(db, to_user_id, "Removed from Group",
                    f"You were removed from {group_name}",
                    data={"type": "member_removed", "group_id": str(group_id)})


async def notify_group_updated(
    db: AsyncSession,
    group_id: uuid.UUID,
    actor_id: uuid.UUID,
    actor_name: str,
    group_name: str,
) -> None:
    """群組更新 push notification — 通知群組所有成員"""
    await notify_group_members(
        db, group_id, actor_id,
        title="Group Updated",
        body=f"{actor_name} updated {group_name}",
        notification_type="group_updated",
    )


async def notify_group_deleted(
    db: AsyncSession,
    group_id: uuid.UUID,
    actor_id: uuid.UUID,
    actor_name: str,
    group_name: str,
) -> None:
    """群組刪除 push notification — 通知群組所有成員"""
    await notify_group_members(
        db, group_id, actor_id,
        title="Group Deleted",
        body=f"{actor_name} deleted {group_name}",
        notification_type="group_deleted",
    )
