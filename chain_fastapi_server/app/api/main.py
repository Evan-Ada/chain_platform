from fastapi import APIRouter

from app.api.routes import (
    health,
    items,
    login,
    private,
    users,
    utils,
    LLMConfig,
    Subscription,
    DataSourceConfig,
    Tag,
    ScheduledTask,
    Push,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(health.router)
api_router.include_router(LLMConfig.router)
api_router.include_router(Subscription.router)
api_router.include_router(DataSourceConfig.router)
api_router.include_router(Tag.router)
api_router.include_router(ScheduledTask.router)
api_router.include_router(Push.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
