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
from app.models.category import ExpenseCategory  # noqa: F401
from app.models.activity_log import ActivityLog, ActivityRead  # noqa: F401

# ---------------------------------------------------------------------------
# 使用真實 PostgreSQL 進行測試（Neon serverless 或本機 Docker）
# Neon 需要 NullPool + statement_cache_size=0 以避免連線衝突
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://splitewise:splitewise@localhost:5433/splitewise_test",
)

_is_neon = "neon.tech" in TEST_DATABASE_URL

# NullPool + statement_cache_size=0 避免 asyncpg 連線狀態衝突（Neon 和本機 Docker 皆適用）
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"statement_cache_size": 0},
)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """確保測試 DB schema 存在。Neon 由 Alembic 管理，本機可 create_all。"""
    async with engine.begin() as conn:
        # create_all 只建立不存在的表，不會覆蓋 Alembic 管理的 schema
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 不 drop_all — schema 由 Alembic 管理


@pytest_asyncio.fixture
async def db(setup_database):
    """Provide a database session. 測試後清除所有資料。"""
    session = AsyncSession(bind=engine, expire_on_commit=False)
    yield session
    await session.close()
    # 清除所有測試資料（按 FK 逆序 DELETE，忽略不存在的表）
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            try:
                await conn.execute(table.delete())
            except Exception:
                pass


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
