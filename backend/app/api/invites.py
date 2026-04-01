from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.schemas.group import InviteInfoResponse
from app.services import group_service

router = APIRouter(prefix="/invite", tags=["invites"])


@router.get("/{token}", response_model=InviteInfoResponse)
async def get_invite_info(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await group_service.get_invite_info(db, token)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/{token}/accept")
async def accept_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        group_id = await group_service.accept_invite(db, token, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    return {"group_id": str(group_id), "detail": "Joined group successfully"}
