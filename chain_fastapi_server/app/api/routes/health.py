from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import SessionDep
from app.core.config import settings
from app.core.mongo import check_mongo
from app.core.redis import check_redis
from app.models import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthStatus)
async def health_check(session: SessionDep) -> HealthStatus:
    pg_ok = False
    try:
        session.exec(select(1))
        pg_ok = True
    except Exception:
        pg_ok = False
    mongo_ok = await check_mongo()
    redis_ok = await check_redis()
    return HealthStatus(
        status="ok",
        pg=pg_ok,
        mongo=mongo_ok,
        redis=redis_ok,
        version=settings.VERSION,
    )
