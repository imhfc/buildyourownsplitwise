import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.email_invitation import EmailInvitationAction, PendingInvitationResponse
from app.schemas.group import InviteInfoResponse
from app.services import email_invitation_service, group_service

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


# ---------------------------------------------------------------------------
# Email invitations (user-facing)
# ---------------------------------------------------------------------------

@router.get("/email/pending", response_model=list[PendingInvitationResponse])
async def get_my_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.email:
        return []
    return await email_invitation_service.get_pending_for_user(db, current_user.email)


@router.post("/email/{invitation_id}/respond")
async def respond_to_invitation(
    invitation_id: uuid.UUID,
    data: EmailInvitationAction,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.email:
        raise HTTPException(status_code=400, detail="No email associated with your account")
    try:
        return await email_invitation_service.respond(
            db, invitation_id, current_user.id, current_user.email, data.action,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except (ConflictError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=e.message)
