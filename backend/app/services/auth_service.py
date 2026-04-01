import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.models.user import User
from app.schemas.user import UserUpdate


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
    """Verify Google access token via tokeninfo + userinfo API, find or create user.

    Returns (access_token, refresh_token, user).
    """
    import httpx

    from app.core.config import settings

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: 驗證 access token 有效性並檢查 audience（防止其他應用的 token 被冒用）
        if settings.GOOGLE_CLIENT_IDS:
            tokeninfo_resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"access_token": google_access_token},
            )
            if tokeninfo_resp.status_code != 200:
                raise ValidationError("Invalid Google access token")

            tokeninfo = tokeninfo_resp.json()
            allowed_client_ids = [cid.strip() for cid in settings.GOOGLE_CLIENT_IDS.split(",") if cid.strip()]
            if tokeninfo.get("aud") not in allowed_client_ids:
                raise ValidationError("Google token audience mismatch")

        # Step 2: 取得使用者資訊
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

    if user and avatar_url:
        user.avatar_url = avatar_url

    if not user and email:
        # Try to link to existing email account
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.auth_provider_id = google_id
            if avatar_url:
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
