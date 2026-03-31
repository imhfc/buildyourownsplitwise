import os
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.expense import Expense, ExpenseSplit
from app.models.settlement import Settlement
from app.models.friendship import Friendship  # noqa: F401

# ---------------------------------------------------------------------------
# 使用真實 PostgreSQL 進行測試（Neon serverless 或本機 Docker）
# Neon 需要 NullPool + statement_cache_size=0 以避免連線衝突
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://splitewise:splitewise@localhost:5433/splitewise_test",
)

_is_neon = "neon.tech" in TEST_DATABASE_URL

engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool if _is_neon else None,
    connect_args={"statement_cache_size": 0} if _is_neon else {},
)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables once per test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(setup_database):
    """Provide a database session. Uses nested transaction on local DB, fresh session on Neon."""
    if _is_neon:
        # Neon serverless: 不支援 nested transaction，改用獨立 session + 測試後清資料
        session = AsyncSession(bind=engine, expire_on_commit=False)
        yield session
        await session.close()
        # 清除所有測試資料（按 FK 順序）
        async with engine.begin() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(table.delete())
    else:
        # 本機 Docker: nested transaction + rollback（零殘留）
        async with engine.connect() as conn:
            trans = await conn.begin()
            session = AsyncSession(bind=conn, expire_on_commit=False)
            yield session
            await session.close()
            await trans.rollback()


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
    password: str = "testpass123",
    display_name: str = "Test User",
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
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
    return await create_test_user(db, "alice@example.com", "pass123", "Alice")


@pytest_asyncio.fixture
async def user_b(db: AsyncSession) -> User:
    return await create_test_user(db, "bob@example.com", "pass123", "Bob")


@pytest_asyncio.fixture
async def user_c(db: AsyncSession) -> User:
    return await create_test_user(db, "charlie@example.com", "pass123", "Charlie")


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
