import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.user import User
from app.schemas.balance import GroupBalanceSummary, OverallBalance
from app.services import balance_service

router = APIRouter(prefix="/balances", tags=["balances"])


@router.get("", response_model=OverallBalance)
async def get_overall_balances(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得使用者所有群組的餘額總覽"""
    return await balance_service.get_overall_balances(db, current_user.id)


@router.get("/groups/{group_id}", response_model=GroupBalanceSummary)
async def get_group_balances(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得群組內每位成員的餘額"""
    try:
        return await balance_service.get_group_balances(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
