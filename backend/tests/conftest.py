import os
import uuid
from decimal import Decimal
from pathlib import Path

os.environ.setdefault("TESTING", "true")

# 自動從 backend/.env 載入 TEST_DATABASE_URL 等環境變數
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=False)

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.expense import Expense, ExpenseSplit
from app.models.settlement import Settlement
from app.models.friendship import Friendship  # noqa: F401
from app.models.activity_log import ActivityLog, ActivityRead  # noqa: F401
from app.models.reminder import PaymentReminder  # noqa: F401

# ---------------------------------------------------------------------------
# 使用真實 PostgreSQL 進行測試（prod VM 或本機 Docker）
# NullPool + statement_cache_size=0 避免 asyncpg 連線狀態衝突
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://splitewise:splitewise@211.20.120.114:5433/splitewise_test",
)

# ---------------------------------------------------------------------------
# 建構 TRUNCATE 語句（只算一次）
# ---------------------------------------------------------------------------
_TRUNCATE_SQL: str | None = None


def _build_truncate_sql() -> str:
    table_names = [t.name for t in reversed(Base.metadata.sorted_tables)]
    return f"TRUNCATE {', '.join(table_names)} CASCADE"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"statement_cache_size": 0},
)


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """確保測試 DB schema 存在。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def db(setup_database):
    """Provide a database session. 測試後用 TRUNCATE CASCADE 清除（比逐表 DELETE 快很多）。"""
    global _TRUNCATE_SQL
    if _TRUNCATE_SQL is None:
        _TRUNCATE_SQL = _build_truncate_sql()

    session = AsyncSession(bind=engine, expire_on_commit=False)
    yield session
    await session.close()
    async with engine.begin() as conn:
        await conn.execute(text(_TRUNCATE_SQL))


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """Provide an httpx AsyncClient with the db dependency overridden."""

    async def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper: create a user directly in the DB
# ---------------------------------------------------------------------------


async def create_test_user(
    db: AsyncSession,
    email: str = "test@example.com",
    display_name: str = "Test User",
) -> User:
    user = User(
        email=email,
        display_name=display_name,
        auth_provider="google",
        auth_provider_id=f"google-{uuid.uuid4().hex[:8]}",
    )
    db.add(user)
    await db.flush()
    return user


def auth_header(user: User) -> dict[str, str]:
    """Return Authorization header for the given user."""
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# High-level fixtures for common scenarios
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def user_a(db: AsyncSession) -> User:
    return await create_test_user(db, email="alice@example.com", display_name="Alice")


@pytest_asyncio.fixture
async def user_b(db: AsyncSession) -> User:
    return await create_test_user(db, email="bob@example.com", display_name="Bob")


@pytest_asyncio.fixture
async def user_c(db: AsyncSession) -> User:
    return await create_test_user(db, email="charlie@example.com", display_name="Charlie")


@pytest_asyncio.fixture
async def group_with_members(db: AsyncSession, user_a: User, user_b: User) -> Group:
    """Create a group with user_a as admin and user_b as member."""
    group = Group(name="Test Group", description="For testing", created_by=user_a.id)
    db.add(group)
    await db.flush()

    member_a = GroupMember(group_id=group.id, user_id=user_a.id, role="admin")
    member_b = GroupMember(group_id=group.id, user_id=user_b.id, role="member")
    db.add(member_a)
    db.add(member_b)
    await db.flush()
    return group
