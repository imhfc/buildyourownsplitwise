import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, String, JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User
from app.models.group import Group, GroupMember
from app.models.expense import Expense, ExpenseSplit
from app.models.settlement import Settlement

# ---------------------------------------------------------------------------
# SQLite async engine for testing (avoids needing PostgreSQL)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Make PostgreSQL UUID / JSONB work with SQLite by compiling to compatible types
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(PG_UUID, "sqlite")
def compile_uuid_sqlite(type_, compiler, **kw):
    return "CHAR(36)"


@compiles(PG_JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables once per test session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(setup_database):
    """Provide a transactional database session that rolls back after each test."""
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
