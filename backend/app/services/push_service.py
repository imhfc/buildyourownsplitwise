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
