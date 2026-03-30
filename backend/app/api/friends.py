import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.user import User
from app.schemas.friendship import (
    FriendListResponse,
    FriendRequestCreate,
    FriendRequestResponse,
    FriendRequestUpdate,
    FriendSearchResult,
)
from app.services import friend_service

router = APIRouter(prefix="/friends", tags=["friends"])


@router.get("", response_model=list[FriendListResponse])
async def list_friends(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all accepted friends."""
    return await friend_service.list_friends(db, current_user.id)


@router.post("/requests", response_model=FriendRequestResponse, status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    data: FriendRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a friend request by email."""
    try:
        return await friend_service.send_friend_request(db, current_user.id, data.friend_email)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/requests", response_model=list[FriendRequestResponse])
async def list_pending_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List incoming pending friend requests."""
    return await friend_service.list_pending_requests(db, current_user.id)


@router.patch("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def respond_to_request(
    request_id: uuid.UUID,
    data: FriendRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept or reject a friend request."""
    try:
        await friend_service.respond_to_request(db, current_user.id, request_id, data.action)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.delete("/{friend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_friend(
    friend_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove an accepted friend."""
    try:
        await friend_service.remove_friend(db, current_user.id, friend_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.get("/search", response_model=list[FriendSearchResult])
async def search_users(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search users by email to send friend requests."""
    return await friend_service.search_users(db, current_user.id, q)
