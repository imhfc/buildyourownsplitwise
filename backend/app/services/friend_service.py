import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.friendship import Friendship
from app.models.user import User
from app.schemas.friendship import (
    FriendListResponse,
    FriendRequestResponse,
    FriendSearchResult,
)
from app.schemas.user import UserResponse


async def send_friend_request(
    db: AsyncSession, user_id: uuid.UUID, friend_email: str
) -> FriendRequestResponse:
    """Send a friend request to another user by email."""
    # Find target user
    result = await db.execute(select(User).where(User.email == friend_email))
    target = result.scalar_one_or_none()
    if not target:
        raise NotFoundError("User not found")

    if target.id == user_id:
        raise ValidationError("Cannot send friend request to yourself")

    # Check existing friendship in either direction
    existing = await db.execute(
        select(Friendship).where(
            or_(
                (Friendship.user_id == user_id) & (Friendship.friend_id == target.id),
                (Friendship.user_id == target.id) & (Friendship.friend_id == user_id),
            )
        )
    )
    friendship = existing.scalar_one_or_none()

    if friendship:
        if friendship.status == "accepted":
            raise ConflictError("Already friends")
        if friendship.status == "pending":
            raise ConflictError("Friend request already pending")
        if friendship.status == "rejected":
            # Allow re-sending after rejection: update existing record
            friendship.status = "pending"
            friendship.user_id = user_id
            friendship.friend_id = target.id
            await db.flush()
            await db.refresh(friendship)
            return _format_request(friendship, target)

    new_friendship = Friendship(user_id=user_id, friend_id=target.id, status="pending")
    db.add(new_friendship)
    await db.flush()

    return _format_request(new_friendship, target)


async def list_pending_requests(
    db: AsyncSession, user_id: uuid.UUID
) -> list[FriendRequestResponse]:
    """List incoming friend requests (where I am the friend_id)."""
    result = await db.execute(
        select(Friendship, User)
        .join(User, Friendship.user_id == User.id)
        .where(Friendship.friend_id == user_id, Friendship.status == "pending")
        .order_by(Friendship.created_at.desc())
    )
    rows = result.all()
    return [_format_request(f, u) for f, u in rows]


async def respond_to_request(
    db: AsyncSession, user_id: uuid.UUID, request_id: uuid.UUID, action: str
) -> None:
    """Accept or reject a friend request."""
    if action not in ("accept", "reject"):
        raise ValidationError("Action must be 'accept' or 'reject'")

    result = await db.execute(
        select(Friendship).where(Friendship.id == request_id)
    )
    friendship = result.scalar_one_or_none()
    if not friendship:
        raise NotFoundError("Friend request not found")

    if friendship.friend_id != user_id:
        raise ForbiddenError("Not your friend request")

    if friendship.status != "pending":
        raise ConflictError("Request already processed")

    friendship.status = "accepted" if action == "accept" else "rejected"
    await db.flush()


async def list_friends(
    db: AsyncSession, user_id: uuid.UUID
) -> list[FriendListResponse]:
    """List all accepted friends."""
    # Friendships where I am user_id
    result_as_user = await db.execute(
        select(Friendship, User)
        .join(User, Friendship.friend_id == User.id)
        .where(Friendship.user_id == user_id, Friendship.status == "accepted")
    )

    # Friendships where I am friend_id
    result_as_friend = await db.execute(
        select(Friendship, User)
        .join(User, Friendship.user_id == User.id)
        .where(Friendship.friend_id == user_id, Friendship.status == "accepted")
    )

    friends = []
    for f, u in result_as_user.all():
        friends.append(FriendListResponse(
            friend=UserResponse.model_validate(u),
            friendship_id=f.id,
            since=f.updated_at,
        ))
    for f, u in result_as_friend.all():
        friends.append(FriendListResponse(
            friend=UserResponse.model_validate(u),
            friendship_id=f.id,
            since=f.updated_at,
        ))

    return friends


async def remove_friend(
    db: AsyncSession, user_id: uuid.UUID, friend_id: uuid.UUID
) -> None:
    """Remove an accepted friendship."""
    result = await db.execute(
        select(Friendship).where(
            or_(
                (Friendship.user_id == user_id) & (Friendship.friend_id == friend_id),
                (Friendship.user_id == friend_id) & (Friendship.friend_id == user_id),
            ),
            Friendship.status == "accepted",
        )
    )
    friendship = result.scalar_one_or_none()
    if not friendship:
        raise NotFoundError("Friendship not found")

    await db.delete(friendship)


async def search_users(
    db: AsyncSession, user_id: uuid.UUID, query: str
) -> list[FriendSearchResult]:
    """Search users by email for adding friends."""
    # 轉義 SQL LIKE 特殊字元，避免使用者透過 % 或 _ 進行模式注入
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    result = await db.execute(
        select(User).where(
            User.email.ilike(f"%{escaped}%", escape="\\"),
            User.id != user_id,
        ).limit(10)
    )
    users = result.scalars().all()

    # Batch check friendship status
    search_results = []
    for u in users:
        friendship_result = await db.execute(
            select(Friendship).where(
                or_(
                    (Friendship.user_id == user_id) & (Friendship.friend_id == u.id),
                    (Friendship.user_id == u.id) & (Friendship.friend_id == user_id),
                )
            )
        )
        friendship = friendship_result.scalar_one_or_none()

        search_results.append(FriendSearchResult(
            user=UserResponse.model_validate(u),
            is_friend=friendship.status == "accepted" if friendship else False,
            has_pending_request=friendship.status == "pending" if friendship else False,
        ))

    return search_results


def _format_request(friendship: Friendship, requester: User) -> FriendRequestResponse:
    return FriendRequestResponse(
        id=friendship.id,
        user=UserResponse.model_validate(requester),
        status=friendship.status,
        created_at=friendship.created_at,
    )
