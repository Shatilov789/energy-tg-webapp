"""Central API router — aggregates all endpoint routers."""

from fastapi import APIRouter

from backend.app.api.endpoints import admin, auth, deals, notifications, users

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(notifications.router)
api_router.include_router(users.router)
api_router.include_router(deals.router)
