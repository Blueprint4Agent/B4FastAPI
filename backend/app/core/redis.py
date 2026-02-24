import redis.asyncio as redis

from app.core.settings import SETTINGS


class RedisManager:
    _client: redis.Redis | None = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._client is None:
            if SETTINGS.REDIS_IN_MEMORY:
                import fakeredis.aioredis as fakeredis

                client = fakeredis.FakeRedis(encoding="utf-8", decode_responses=True)
            else:
                client = redis.from_url(
                    SETTINGS.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                )
            await client.ping()
            cls._client = client
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
