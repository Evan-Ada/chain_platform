import sentry_sdk
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.scheduler import scheduler


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


async def _llm_batch_tag_job() -> None:
    """每分钟批量打标任务。"""
    from app.core.db import engine
    from app.services.llm_tag import LLMTagService
    from sqlmodel import Session

    with Session(engine) as db:
        service = LLMTagService()
        await service.batch_tag_pending(db, batch_size=20)


async def _push_pending_job() -> None:
    """每分钟推送扫描任务。"""
    from app.services.push_service import PushService

    await PushService.run_pending()


@app.on_event("startup")
async def _startup_scheduler() -> None:
    try:
        scheduler.start()
        from app.services.scheduler_v2 import ScheduledTaskService
        ScheduledTaskService.rehydrate()
    except Exception:
        pass
    try:
        scheduler.add_job(_llm_batch_tag_job, CronTrigger(minute="*/1"), id="llm_batch_tag", replace_existing=True)
        scheduler.add_job(_push_pending_job, CronTrigger(minute="*/1"), id="push_pending", replace_existing=True)
    except Exception:
        pass


@app.on_event("shutdown")
async def _shutdown_scheduler() -> None:
    scheduler.shutdown(wait=False)
