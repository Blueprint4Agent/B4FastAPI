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


def create_email_verification_token() -> str:
    return secrets.token_urlsafe(32)


def create_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


async def store_refresh_token(user_id: int, refresh_token: str) -> None:
    redis = await RedisManager.get_client()
    await redis.setex(
        f"refresh_token:{user_id}",
        timedelta(days=SETTINGS.REFRESH_TOKEN_EXPIRE_DAYS),
        refresh_token,
    )


async def store_email_verification_token(user_id: int, token: str) -> None:
    redis = await RedisManager.get_client()
    ttl = timedelta(minutes=SETTINGS.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    user_token_key = f"email_verify_user_token:{user_id}"

    previous_token = await redis.get(user_token_key)
    if previous_token:
        await redis.delete(f"email_verify_token:{previous_token}")

    await redis.setex(f"email_verify_token:{token}", ttl, str(user_id))
    await redis.setex(user_token_key, ttl, token)


async def store_password_reset_token(user_id: int, token: str) -> None:
    redis = await RedisManager.get_client()
    ttl = timedelta(minutes=SETTINGS.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    user_token_key = f"password_reset_user_token:{user_id}"

    previous_token = await redis.get(user_token_key)
    if previous_token:
        await redis.delete(f"password_reset_token:{previous_token}")

    await redis.setex(f"password_reset_token:{token}", ttl, str(user_id))
    await redis.setex(user_token_key, ttl, token)


async def verify_refresh_token(user_id: int, refresh_token: str) -> bool:
    redis = await RedisManager.get_client()
    stored = await redis.get(f"refresh_token:{user_id}")
    return stored == refresh_token


async def consume_email_verification_token(token: str) -> int | None:
    redis = await RedisManager.get_client()
    key = f"email_verify_token:{token}"
    stored_user_id = await redis.get(key)
    if stored_user_id is None:
        return None

    try:
        user_id = int(stored_user_id)
    except (TypeError, ValueError):
        return None

    current_token = await redis.get(f"email_verify_user_token:{user_id}")
    if current_token != token:
        return None

    await redis.delete(key)
    await redis.delete(f"email_verify_user_token:{user_id}")
    return user_id


async def consume_password_reset_token(token: str) -> int | None:
    redis = await RedisManager.get_client()
    key = f"password_reset_token:{token}"
    stored_user_id = await redis.get(key)
    if stored_user_id is None:
        return None

    try:
        user_id = int(stored_user_id)
    except (TypeError, ValueError):
        return None

    current_token = await redis.get(f"password_reset_user_token:{user_id}")
    if current_token != token:
        return None

    await redis.delete(key)
    await redis.delete(f"password_reset_user_token:{user_id}")
    return user_id


async def delete_refresh_token(user_id: int) -> None:
    redis = await RedisManager.get_client()
    await redis.delete(f"refresh_token:{user_id}")
