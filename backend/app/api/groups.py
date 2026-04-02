import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.email_invitation import EmailInvitationCreate, EmailInvitationResponse
from app.schemas.group import (
    AddMemberRequest, GroupCreate, GroupListResponse, GroupResponse, GroupUpdate,
    InviteTokenResponse, ReorderGroupsRequest, SimplifiedDebt,
)
from app.services import email_invitation_service, group_service

router = APIRouter(prefix="/groups", tags=["groups"])

_STATUS_MAP = {
    ForbiddenError: 403,
    NotFoundError: 404,
    ConflictError: 400,
    ValidationError: 422,
}


def _handle(e: Exception):
    for exc_type, code in _STATUS_MAP.items():
        if isinstance(e, exc_type):
            raise HTTPException(status_code=code, detail=e.message)
    raise


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await group_service.create_group(db, data, current_user.id)


@router.get("", response_model=list[GroupListResponse])
async def list_my_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await group_service.list_user_groups(db, current_user.id)
    group_ids = [r.id for r in rows]
    debts_map = await group_service.get_groups_debts(db, group_ids)
    return [
        GroupListResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            default_currency=r.default_currency,
            member_count=r.member_count,
            created_at=r.created_at,
            created_by=r.created_by,
            my_role=r.my_role,
            sort_order=r.sort_order,
            is_settled=len(debts_map.get(r.id, [])) == 0 and r.expense_count > 0,
            unsettled_debts=debts_map.get(r.id, []),
        )
        for r in rows
    ]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await group_service.check_membership(db, group_id, current_user.id)
        return await group_service.get_group_detail(db, group_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await group_service.update_group(db, group_id, current_user.id, data)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await group_service.delete_group(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.put("/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_groups(
    data: ReorderGroupsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await group_service.reorder_groups(db, current_user.id, data.group_ids)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: uuid.UUID,
    data: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await group_service.add_member(db, group_id, current_user.id, data.user_id)
    except (ForbiddenError, NotFoundError, ConflictError) as e:
        _handle(e)
    return {"detail": "Member added"}


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await group_service.remove_member(db, group_id, current_user.id, user_id)
    except (ForbiddenError, NotFoundError) as e:
        _handle(e)


# ---------------------------------------------------------------------------
# Invite link management
# ---------------------------------------------------------------------------

@router.post("/{group_id}/invite", response_model=InviteTokenResponse)
async def create_invite(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await group_service.create_invite_token(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.delete("/{group_id}/invite", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invite(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await group_service.revoke_invite_token(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


@router.post("/{group_id}/invite/regenerate", response_model=InviteTokenResponse)
async def regenerate_invite(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await group_service.regenerate_invite_token(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)


# ---------------------------------------------------------------------------
# Email invitations
# ---------------------------------------------------------------------------

@router.post("/{group_id}/email-invitations", response_model=EmailInvitationResponse, status_code=status.HTTP_201_CREATED)
async def send_email_invitation(
    group_id: uuid.UUID,
    data: EmailInvitationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await email_invitation_service.create_invitation(db, group_id, current_user.id, data.email)
    except (ForbiddenError, NotFoundError, ConflictError) as e:
        _handle(e)

    from app.services.email_service import send_invitation_email
    background_tasks.add_task(
        send_invitation_email,
        to_email=result["email"],
        inviter_name=result["inviter_name"],
        group_name=result["group_name"],
        invite_token=result["token"],
    )
    return result


@router.get("/{group_id}/email-invitations", response_model=list[EmailInvitationResponse])
async def list_email_invitations(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await email_invitation_service.list_group_invitations(db, group_id, current_user.id)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
