import hashlib
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


def _gravatar_url(email: str) -> str:
    email_hash = hashlib.md5(email.lower().strip().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?d=identicon&s=200"


async def register_user(db: AsyncSession, data: UserRegister) -> tuple[str, str, User]:
    """Register a new user. Returns (access_token, refresh_token, user)."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise ConflictError("Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name,
        avatar_url=_gravatar_url(data.email),
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


async def google_login(db: AsyncSession, google_access_token: str) -> tuple[str, str, User]:
    """Verify Google access token via userinfo API, find or create user. Returns (access_token, refresh_token, user)."""
    import httpx

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

    if resp.status_code != 200:
        raise ValidationError("Invalid Google access token")

    info = resp.json()
    google_id: str = info.get("sub", "")
    if not google_id:
        raise ValidationError("Invalid Google access token")

    email: str | None = info.get("email")
    display_name: str = info.get("name") or email or "User"
    avatar_url: str | None = info.get("picture")

    # Find by Google ID first
    result = await db.execute(
        select(User).where(User.auth_provider == "google", User.auth_provider_id == google_id)
    )
    user = result.scalar_one_or_none()

    if not user and email:
        # Try to link to existing email account
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.auth_provider_id = google_id
            if not user.avatar_url and avatar_url:
                user.avatar_url = avatar_url

    if not user:
        user = User(
            email=email,
            display_name=display_name,
            avatar_url=avatar_url,
            auth_provider="google",
            auth_provider_id=google_id,
        )
        db.add(user)
        await db.flush()

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return access_token, refresh_token, user
