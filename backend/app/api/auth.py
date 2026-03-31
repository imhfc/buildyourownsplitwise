from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import ConflictError, ForbiddenError, ValidationError
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.user import (
    GoogleAuthRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        access_token, refresh_token, user = await auth_service.register_user(db, data)
    except ConflictError as e:
        raise HTTPException(status_code=400, detail=e.message)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        access_token, refresh_token, user = await auth_service.login_user(db, data.email, data.password)
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=e.message)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access + refresh token pair."""
    try:
        access_token, refresh_token, user = await auth_service.refresh_tokens(db, data.refresh_token)
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=e.message)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/google", response_model=TokenResponse)
async def google_login(data: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a Google access token for app JWT tokens."""
    try:
        access_token, refresh_token, user = await auth_service.google_login(db, data.access_token)
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=e.message)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.update_user(db, current_user, data)
    return UserResponse.model_validate(user)


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await auth_service.change_password(db, current_user, data.old_password, data.new_password)
    except ForbiddenError as e:
        raise HTTPException(status_code=403, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/lookup", response_model=UserResponse)
async def lookup_user_by_email(
    email: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """以 email 查詢使用者（新增群組成員時使用）。"""
    from sqlalchemy import select as sa_select

    result = await db.execute(sa_select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
