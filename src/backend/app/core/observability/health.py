from pydantic import BaseModel
from sqlalchemy import text

from app.core.cache.redis import RedisManager
from app.core.db.session import get_session_factory


class HealthCheckResult(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


async def check_database() -> str:
    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return "failed"
    return "ok"


async def check_redis() -> str:
    try:
        redis = await RedisManager.get_client()
        await redis.ping()
    except Exception:
        return "failed"
    return "ok"


async def get_readiness() -> ReadinessResponse:
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
    }
    status = "ok" if all(result == "ok" for result in checks.values()) else "degraded"
    return ReadinessResponse(status=status, checks=checks)
