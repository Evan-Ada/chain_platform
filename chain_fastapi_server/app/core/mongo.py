"""MongoDB 异步连接占位。仅当 settings.MONGO_URL 配置时连接，否则懒加载、不阻塞应用启动。"""
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient | None:
    global _client
    if not settings.MONGO_URL:
        return None
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URL, serverSelectionTimeoutMS=2000)
    return _client


async def check_mongo() -> bool:
    client = get_mongo_client()
    if client is None:
        return False
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        return False
