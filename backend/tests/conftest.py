"""
Общие фикстуры для тестов.

КАК РАБОТАЕТ:
- Используем SQLite в памяти (не PostgreSQL) — тесты быстрые и изолированные
- Перед КАЖДЫМ тестом создаются таблицы, после — удаляются (чистая БД)
- Фикстура `client` подменяет зависимость get_db на тестовую сессию
- Фикстуры admin_user/worker_user создают пользователей в тестовой БД
- Авторизация через заголовок X-Dev-Telegram-Id (dev-mode bypass)

ЗАВИСИМОСТИ:
- aiosqlite — async SQLite драйвер для тестов
- httpx — AsyncClient для отправки запросов к FastAPI без реального сервера
- pytest-asyncio — поддержка async тестов
"""

import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.user import User, UserRole

# SQLite в памяти — каждый тест начинает с нуля, ничего не остается на диске
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    """Один event loop на всю тест-сессию. Нужен для async фикстур."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """
    Автоматически выполняется перед каждым тестом.
    Создает все таблицы → тест работает → удаляет все таблицы.
    Гарантирует что тесты не влияют друг на друга.
    """
    import backend.app.models  # noqa: F401 — импорт регистрирует модели в Base.metadata

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Тестовая сессия БД. Используется и напрямую, и через client."""
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP-клиент для отправки запросов к API.

    КАК РАБОТАЕТ:
    1. Подменяет зависимость get_db — вместо реальной БД используется тестовая
    2. ASGITransport — запросы идут напрямую в приложение, без сети
    3. base_url="http://test" — фейковый URL, запросы не уходят в интернет
    4. После теста — очищает подмены
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
    """Создает тестового администратора в БД. telegram_id=111111111."""
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
    """Создает тестового работника в БД. telegram_id=222222222."""
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
    """Второй работник — для тестов совместного доступа и изоляции."""
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
