import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate


async def check_membership(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    """Verify user is a group member and return the membership record."""
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise ForbiddenError("Not a member of this group")
    return member


async def check_admin(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    """Verify user is a group admin."""
    membership = await check_membership(db, group_id, user_id)
    if membership.role != "admin":
        raise ForbiddenError("Only admins can perform this action")
    return membership


async def create_group(
    db: AsyncSession, data: GroupCreate, creator_id: uuid.UUID
) -> GroupResponse:
    group = Group(
        name=data.name,
        description=data.description,
        default_currency=data.default_currency,
        created_by=creator_id,
    )
    db.add(group)
    await db.flush()

    member = GroupMember(group_id=group.id, user_id=creator_id, role="admin")
    db.add(member)
    await db.flush()

    return await get_group_detail(db, group.id)


async def list_user_groups(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    my_membership = aliased(GroupMember)
    result = await db.execute(
        select(
            Group.id,
            Group.name,
            Group.description,
            Group.default_currency,
            Group.created_at,
            Group.created_by,
            func.count(GroupMember.id).label("member_count"),
            my_membership.role.label("my_role"),
        )
        .join(GroupMember, Group.id == GroupMember.group_id)
        .join(my_membership, (Group.id == my_membership.group_id) & (my_membership.user_id == user_id))
        .group_by(Group.id, my_membership.role)
        .order_by(Group.created_at.desc())
    )
    return result.all()


async def update_group(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID, data: GroupUpdate
) -> GroupResponse:
    await check_admin(db, group_id, user_id)

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await db.flush()

    return await get_group_detail(db, group_id)


async def delete_group(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    await check_admin(db, group_id, user_id)

    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    await db.delete(group)


async def add_member(
    db: AsyncSession, group_id: uuid.UUID, requester_id: uuid.UUID, target_user_id: uuid.UUID
) -> None:
    await check_membership(db, group_id, requester_id)

    # Check target user exists
    result = await db.execute(select(User).where(User.id == target_user_id))
    if not result.scalar_one_or_none():
        raise NotFoundError("User not found")

    # Check not already a member
    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == target_user_id
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("User is already a member")

    member = GroupMember(group_id=group_id, user_id=target_user_id)
    db.add(member)


async def remove_member(
    db: AsyncSession, group_id: uuid.UUID, requester_id: uuid.UUID, target_user_id: uuid.UUID
) -> None:
    membership = await check_membership(db, group_id, requester_id)
    if membership.role != "admin" and requester_id != target_user_id:
        raise ForbiddenError("Only admins can remove others")

    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == target_user_id
        )
    )
    target = result.scalar_one_or_none()
    if not target:
        raise NotFoundError("Member not found")
    await db.delete(target)


async def get_group_detail(db: AsyncSession, group_id: uuid.UUID) -> GroupResponse:
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


async def get_group_member_ids(db: AsyncSession, group_id: uuid.UUID) -> list[uuid.UUID]:
    result = await db.execute(
        select(GroupMember.user_id).where(GroupMember.group_id == group_id)
    )
    return [row[0] for row in result.all()]
