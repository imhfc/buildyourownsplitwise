import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.expense import Expense
from app.models.group import Group, GroupMember
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate, SimplifiedDebt
from app.services.activity_log_service import log_activity


async def check_membership(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    """Verify user is a group member and return the membership record."""
    result = await db.execute(
        select(GroupMember)
        .join(Group, GroupMember.group_id == Group.id)
        .where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            Group.deleted_at.is_(None),
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
    expense_count_subq = (
        select(func.count(Expense.id))
        .where(Expense.group_id == Group.id, Expense.deleted_at.is_(None))
        .correlate(Group)
        .scalar_subquery()
        .label("expense_count")
    )
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
            my_membership.sort_order,
            expense_count_subq,
        )
        .where(Group.deleted_at.is_(None))
        .join(GroupMember, Group.id == GroupMember.group_id)
        .join(my_membership, (Group.id == my_membership.group_id) & (my_membership.user_id == user_id))
        .group_by(Group.id, my_membership.role, my_membership.sort_order)
        .order_by(my_membership.sort_order.asc(), Group.created_at.desc())
    )
    return result.all()


async def get_groups_debts(
    db: AsyncSession, group_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[SimplifiedDebt]]:
    """Calculate simplified debts for multiple groups at once (per-currency, no conversion)."""
    from app.services.settlement_service import calculate_balances_by_currency, simplify_debts

    result: dict[uuid.UUID, list[SimplifiedDebt]] = {}
    if not group_ids:
        return result

    # Collect all user IDs we'll need
    all_user_ids: set[uuid.UUID] = set()

    # group_id -> { currency -> { user_id -> balance } }
    group_balances: dict[uuid.UUID, dict[str, dict[uuid.UUID, object]]] = {}
    for gid in group_ids:
        by_currency = await calculate_balances_by_currency(db, gid)
        group_balances[gid] = by_currency
        for balances in by_currency.values():
            all_user_ids.update(balances.keys())

    # Batch-load user display names
    user_map: dict[uuid.UUID, str] = {}
    if all_user_ids:
        user_result = await db.execute(
            select(User.id, User.display_name).where(User.id.in_(list(all_user_ids)))
        )
        user_map = {row.id: row.display_name for row in user_result.all()}

    for gid in group_ids:
        by_currency = group_balances[gid]
        if not by_currency:
            result[gid] = []
            continue
        debts: list[SimplifiedDebt] = []
        for cur, balances in sorted(by_currency.items()):
            transactions = simplify_debts(balances)
            debts.extend(
                SimplifiedDebt(
                    from_user_id=t["from"],
                    from_user_name=user_map.get(t["from"], "Unknown"),
                    to_user_id=t["to"],
                    to_user_name=user_map.get(t["to"], "Unknown"),
                    amount=t["amount"],
                    currency=cur,
                )
                for t in transactions
            )
        result[gid] = debts

    return result


async def reorder_groups(
    db: AsyncSession, user_id: uuid.UUID, group_ids: list[uuid.UUID]
) -> None:
    """Set sort_order for user's groups based on the provided order."""
    for idx, gid in enumerate(group_ids):
        result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == gid, GroupMember.user_id == user_id
            )
        )
        membership = result.scalar_one_or_none()
        if membership:
            membership.sort_order = idx + 1


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
    group.deleted_at = datetime.now(timezone.utc)


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

    # 查目標使用者名稱
    target_result = await db.execute(select(User.display_name).where(User.id == target_user_id))
    target_name = target_result.scalar_one_or_none() or "Unknown"
    await log_activity(
        db, group_id=group_id, actor_id=requester_id, action="member_added",
        target_type="member", target_id=target_user_id, extra_name=target_name,
    )


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

    # 查目標使用者名稱
    target_name_result = await db.execute(select(User.display_name).where(User.id == target_user_id))
    target_name = target_name_result.scalar_one_or_none() or "Unknown"
    await log_activity(
        db, group_id=group_id, actor_id=requester_id, action="member_removed",
        target_type="member", target_id=target_user_id, extra_name=target_name,
    )

    await db.delete(target)


async def get_group_detail(db: AsyncSession, group_id: uuid.UUID) -> GroupResponse:
    result = await db.execute(
        select(Group)
        .where(Group.id == group_id, Group.deleted_at.is_(None))
        .options(selectinload(Group.members).selectinload(GroupMember.user))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise NotFoundError("Group not found")
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        default_currency=group.default_currency,
        cover_image_url=group.cover_image_url,
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


# ---------------------------------------------------------------------------
# Invite token
# ---------------------------------------------------------------------------

async def create_invite_token(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> dict:
    """Generate or return existing invite token. Requires membership."""
    await check_membership(db, group_id, user_id)
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    if not group.invite_token:
        group.invite_token = secrets.token_hex(16)
        group.invite_token_created_at = datetime.now(timezone.utc)
        await db.flush()
    return {
        "invite_token": group.invite_token,
        "created_at": group.invite_token_created_at,
    }


async def revoke_invite_token(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Revoke invite token. Requires admin."""
    await check_admin(db, group_id, user_id)
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    group.invite_token = None
    group.invite_token_created_at = None


async def regenerate_invite_token(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> dict:
    """Regenerate invite token (invalidates old). Requires admin."""
    await check_admin(db, group_id, user_id)
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one()
    group.invite_token = secrets.token_hex(16)
    group.invite_token_created_at = datetime.now(timezone.utc)
    await db.flush()
    return {
        "invite_token": group.invite_token,
        "created_at": group.invite_token_created_at,
    }


async def get_invite_info(db: AsyncSession, token: str) -> dict:
    """Get group info from invite token."""
    result = await db.execute(
        select(Group).where(Group.invite_token == token, Group.deleted_at.is_(None))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise NotFoundError("Invalid invite link")
    member_count_result = await db.execute(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
    )
    return {
        "group_id": group.id,
        "group_name": group.name,
        "group_description": group.description,
        "member_count": member_count_result.scalar(),
    }


async def accept_invite(
    db: AsyncSession, token: str, user_id: uuid.UUID
) -> uuid.UUID:
    """Accept invite and join group. Returns group_id."""
    result = await db.execute(
        select(Group).where(Group.invite_token == token, Group.deleted_at.is_(None))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise NotFoundError("Invalid invite link")
    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group.id, GroupMember.user_id == user_id
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Already a member of this group")
    member = GroupMember(group_id=group.id, user_id=user_id, role="member")
    db.add(member)
    return group.id
