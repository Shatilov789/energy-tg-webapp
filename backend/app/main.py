"""Energy CRM — Telegram Web App backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.router import api_router
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import async_session, engine
from backend.app.processes.catalog import seed_process_catalog
from backend.app.services.bot import start_bot, stop_bot
from backend.app.services.scheduler import start_scheduler, stop_scheduler
from backend.app.services.seed import ensure_configured_admin, seed_dev_admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Energy CRM [%s]", settings.app_env)

    # In dev mode tables come from the models; everywhere else from `alembic upgrade head`.
    if settings.is_development:
        # Import all models so Base.metadata knows about them
        import backend.app.models  # noqa: F401

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

        async with async_session() as db:
            await seed_dev_admin(db)

    async with async_session() as db:
        await ensure_configured_admin(db)
        await seed_process_catalog(db)

    start_scheduler()
    await start_bot()

    yield

    await stop_bot()
    stop_scheduler()
    await engine.dispose()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Energy CRM",
    description="Telegram Web App for energy infrastructure inspections",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,  # Authentication is a header, never a cookie.
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
