"""Redis 异步连接占位。仅当 settings.REDIS_URL 配置时连接。"""
import redis.asyncio as redis_async

from app.core.config import settings

_client: redis_async.Redis | None = None


def get_redis_client() -> redis_async.Redis | None:
    global _client
    if not settings.REDIS_URL:
        return None
    if _client is None:
        _client = redis_async.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


async def check_redis() -> bool:
    client = get_redis_client()
    if client is None:
        return False
    try:
        return await client.ping()
    except Exception:
        return False
