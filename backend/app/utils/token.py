import secrets
from datetime import UTC, datetime, timedelta

from jose import jwt

from app.core.redis import RedisManager
from app.core.settings import SETTINGS


def create_access_token(subject: str, email: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "email": email, "exp": expire}
    return jwt.encode(payload, SETTINGS.SECRET_KEY, algorithm=SETTINGS.ALGORITHM)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)


async def store_refresh_token(user_id: int, refresh_token: str) -> None:
    redis = await RedisManager.get_client()
    await redis.setex(
        f"refresh_token:{user_id}",
        timedelta(days=SETTINGS.REFRESH_TOKEN_EXPIRE_DAYS),
        refresh_token,
    )


async def verify_refresh_token(user_id: int, refresh_token: str) -> bool:
    redis = await RedisManager.get_client()
    stored = await redis.get(f"refresh_token:{user_id}")
    return stored == refresh_token


async def delete_refresh_token(user_id: int) -> None:
    redis = await RedisManager.get_client()
    await redis.delete(f"refresh_token:{user_id}")
