import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.group import (
    AddMemberRequest,
    GroupCreate,
    GroupListResponse,
    GroupResponse,
    GroupUpdate,
)

router = APIRouter(prefix="/groups", tags=["groups"])


async def _check_membership(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> GroupMember:
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=403, detail="Not a member of this group")
    return member


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    group = Group(
        name=data.name,
        description=data.description,
        default_currency=data.default_currency,
        created_by=current_user.id,
    )
    db.add(group)
    await db.flush()

    # Creator is automatically an admin member
    member = GroupMember(group_id=group.id, user_id=current_user.id, role="admin")
    db.add(member)
    await db.flush()

    return await _get_group_detail(db, group.id)


@router.get("", response_model=list[GroupListResponse])
async def list_my_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Group.id,
            Group.name,
            Group.description,
            Group.default_currency,
            Group.created_at,
            func.count(GroupMember.id).label("member_count"),
        )
        .join(GroupMember, Group.id == GroupMember.group_id)
        .where(
            Group.id.in_(
                select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
            )
        )
        .group_by(Group.id)
        .order_by(Group.created_at.desc())
    )
    rows = result.all()
    return [
        GroupListResponse(
            id=r.id,
            name=r.name,
            description=r.description,
            default_currency=r.default_currency,
            member_count=r.member_count,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_membership(db, group_id, current_user.id)
    return await _get_group_detail(db, group_id)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await _check_membership(db, group_id, current_user.id)
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update group")

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await db.flush()

    return await _get_group_detail(db, group_id)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await _check_membership(db, group_id, current_user.id)
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete group")

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    await db.delete(group)


@router.post("/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: uuid.UUID,
    data: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_membership(db, group_id, current_user.id)

    # Check user exists
    result = await db.execute(select(User).where(User.id == data.user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already a member
    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == data.user_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")

    member = GroupMember(group_id=group_id, user_id=data.user_id)
    db.add(member)
    return {"detail": "Member added"}


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    membership = await _check_membership(db, group_id, current_user.id)
    if membership.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Only admins can remove others")

    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    await db.delete(target)


async def _get_group_detail(db: AsyncSession, group_id: uuid.UUID) -> GroupResponse:
    result = await db.execute(
        select(Group)
        .where(Group.id == group_id)
        .options(selectinload(Group.members).selectinload(GroupMember.user))
    )
    group = result.scalar_one()
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        default_currency=group.default_currency,
        created_by=group.created_by,
        created_at=group.created_at,
        members=[
            {
                "user": m.user,
                "role": m.role,
                "joined_at": m.joined_at,
            }
            for m in group.members
        ],
    )
