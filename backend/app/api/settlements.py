import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.schemas.expense import SettlementCreate, SettlementResponse, SettlementSuggestion
from app.services import settlement_service

router = APIRouter(prefix="/groups/{group_id}/settlements", tags=["settlements"])


@router.get("/suggestions", response_model=list[SettlementSuggestion])
async def get_settlement_suggestions(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await settlement_service.get_settlement_suggestions(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.post("", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def create_settlement(
    group_id: uuid.UUID,
    data: SettlementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await settlement_service.create_settlement(db, group_id, current_user.id, data)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("", response_model=list[SettlementResponse])
async def list_settlements(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await settlement_service.list_settlements(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
