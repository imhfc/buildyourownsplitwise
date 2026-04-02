from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityItem, UnreadCountResponse
from app.services.activity_log_service import get_unread_count, list_user_activities, mark_activities_read

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得目前使用者的未讀活動數量。"""
    count = await get_unread_count(db, current_user.id)
    return UnreadCountResponse(count=count)


@router.post("/mark-read", response_model=UnreadCountResponse)
async def mark_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """將目前使用者的所有活動標記為已讀。"""
    await mark_activities_read(db, current_user.id)
    return UnreadCountResponse(count=0)


@router.get("", response_model=list[ActivityItem])
async def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """回傳目前使用者所有群組的最新活動，依時間排序。"""
    return await list_user_activities(db, current_user.id, skip, limit)
