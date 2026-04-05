import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.reminder import BatchReminderCreate, BatchReminderResponse, ReminderCreate
from app.schemas.settlement import SettlementCreate, SettlementForgive, SettlementResponse, SettlementSuggestionsResponse
from app.services import settlement_service

# 群組內結算路由
router = APIRouter(prefix="/groups/{group_id}/settlements", tags=["settlements"])

# 跨群組結算路由（掛在 /api/v1/settlements）
user_router = APIRouter(prefix="/settlements", tags=["settlements"])


@router.get("/suggestions", response_model=SettlementSuggestionsResponse)
async def get_settlement_suggestions(
    group_id: uuid.UUID,
    unified_currency: str | None = Query(None, description="指定幣別則統一結算，不帶則分幣別"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await settlement_service.get_settlement_suggestions(
            db, group_id, current_user.id, unified_currency=unified_currency,
        )
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.get("/details")
async def get_pairwise_details(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得 pairwise 債務明細（不經簡化演算法）"""
    try:
        from app.services.group_service import check_membership
        await check_membership(db, group_id, current_user.id)
        return await settlement_service.get_pairwise_details(db, group_id)
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


@router.patch("/{settlement_id}/confirm", response_model=SettlementResponse)
async def confirm_settlement(
    group_id: uuid.UUID,
    settlement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await settlement_service.confirm_settlement(
            db, group_id, settlement_id, current_user.id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.patch("/{settlement_id}/reject", response_model=SettlementResponse)
async def reject_settlement(
    group_id: uuid.UUID,
    settlement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await settlement_service.reject_settlement(
            db, group_id, settlement_id, current_user.id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/forgive", response_model=SettlementResponse, status_code=status.HTTP_201_CREATED)
async def forgive_settlement(
    group_id: uuid.UUID,
    data: SettlementForgive,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """被欠款人（債權人）主動結清債務"""
    try:
        return await settlement_service.forgive_settlement(
            db, group_id, current_user.id, data.from_user, data.amount, data.currency,
        )
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("", response_model=list[SettlementResponse])
async def list_settlements(
    group_id: uuid.UUID,
    status_filter: str | None = Query(None, alias="status", description="pending / confirmed"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await settlement_service.list_settlements(
            db, group_id, current_user.id, status=status_filter,
        )
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


# --- 付款提醒 ---

@router.post("/reminders", status_code=status.HTTP_201_CREATED)
async def send_reminder(
    group_id: uuid.UUID,
    data: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """發送付款提醒（同一對象 24 小時內最多一次）"""
    from app.services import reminder_service
    try:
        return await reminder_service.create_reminder(db, group_id, current_user.id, data)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/reminders/batch", response_model=BatchReminderResponse, status_code=status.HTTP_200_OK)
async def send_batch_reminders(
    group_id: uuid.UUID,
    data: BatchReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批次發送付款提醒，跳過 24 小時內已提醒或無效的對象"""
    from app.services import reminder_service
    try:
        sent, skipped = await reminder_service.create_batch_reminders(
            db, group_id, current_user.id, data.reminders,
        )
        return BatchReminderResponse(sent=sent, skipped=skipped)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


# --- 跨群組端點 ---

@user_router.get("/pending", response_model=list[SettlementResponse])
async def list_pending_settlements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await settlement_service.list_pending_settlements(db, current_user.id)
