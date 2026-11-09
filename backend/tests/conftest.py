"""Shared test fixtures.

How it works:
- Tests run on SQLite instead of PostgreSQL, which keeps them fast and isolated.
- Tables are created before EVERY test and dropped after it.
- The `client` fixture swaps the get_db dependency for the test session.
- The admin_user/worker_user fixtures create users in the test database.
- Authentication goes through the X-Dev-Telegram-Id header (dev-mode bypass).

Dependencies:
- aiosqlite: async SQLite driver for the tests.
- httpx: AsyncClient that calls FastAPI without a real server.
- pytest-asyncio: async test support.
"""

import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Must be set before the app is imported: tests sign in through the dev-only header.
os.environ["APP_ENV"] = "development"

from backend.app.db.base import Base  # noqa: E402
from backend.app.db.session import get_db  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.models.user import User, UserRole  # noqa: E402

# Recreated for every test, so each one starts from an empty database.
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """One event loop for the whole test session; async fixtures need it."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test and drop them after, so tests cannot affect each other."""
    import backend.app.models  # noqa: F401 — the import registers the models in Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Test database session, used directly and through `client`."""
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for calling the API.

    1. Replaces the get_db dependency with the test session.
    2. ASGITransport sends requests straight into the app, with no network.
    3. base_url="http://test" is a placeholder; nothing leaves the process.
    4. Clears the overrides after the test.
    """

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create a test administrator. telegram_id=111111111."""
    user = User(
        telegram_id=111111111,
        first_name="Test",
        last_name="Admin",
        username="test_admin",
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def worker_user(db: AsyncSession) -> User:
    """Create a test worker. telegram_id=222222222."""
    user = User(
        telegram_id=222222222,
        first_name="Test",
        last_name="Worker",
        username="test_worker",
        role=UserRole.WORKER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_worker(db: AsyncSession) -> User:
    """A second worker, for shared-access and isolation tests."""
    user = User(
        telegram_id=333333333,
        first_name="Second",
        last_name="Worker",
        username="second_worker",
        role=UserRole.WORKER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
