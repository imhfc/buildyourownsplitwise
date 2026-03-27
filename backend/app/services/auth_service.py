import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import UserRegister, UserUpdate


async def register_user(db: AsyncSession, data: UserRegister) -> tuple[str, str, User]:
    """Register a new user. Returns (access_token, refresh_token, user)."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
    )
    db.add(user)
    await db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return access_token, refresh_token, user


async def login_user(db: AsyncSession, email: str, password: str) -> tuple[str, str, User]:
    """Authenticate user and return (access_token, refresh_token, user)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise ValidationError("Invalid email or password")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return access_token, refresh_token, user


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str, User]:
    """Validate refresh token and issue new token pair. Returns (access_token, refresh_token, user)."""
    user_id = decode_refresh_token(refresh_token)
    if user_id is None:
        raise ValidationError("Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValidationError("User not found")

    new_access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))
    return new_access, new_refresh, user


async def update_user(db: AsyncSession, user: User, data: UserUpdate) -> User:
    """Update user profile fields."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.flush()
    return user
