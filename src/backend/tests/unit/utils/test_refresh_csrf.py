import asyncio
from unittest.mock import AsyncMock

import fakeredis.aioredis

from app.core.cache.redis import RedisManager
from app.utils.token import (
    delete_refresh_token,
    get_or_create_refresh_csrf,
    store_refresh_token,
    verify_refresh_csrf,
)


def test_csrf_concurrent_bootstrap_expiry_renewal_and_revocation(monkeypatch):
    async def scenario():
        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(RedisManager, "get_client", AsyncMock(return_value=redis))
        assert await get_or_create_refresh_csrf("missing") is None
        await store_refresh_token(1, "session", "refresh")
        await redis.expire("refresh_session:session", 30)
        proofs = await asyncio.gather(*(get_or_create_refresh_csrf("session") for _ in range(8)))
        assert len(set(proofs)) == 1
        proof = proofs[0]
        assert proof and len(proof) >= 32
        assert 0 < await redis.ttl("refresh_csrf:session") <= 30
        assert await verify_refresh_csrf("session", proof)
        for invalid in (None, "", "wrong", "한글", "a" * 129):
            assert not await verify_refresh_csrf("session", invalid)
        await store_refresh_token(1, "session", "refresh")
        assert await verify_refresh_csrf("session", proof)
        assert await redis.ttl("refresh_csrf:session") > 30
        await delete_refresh_token(1)
        assert await get_or_create_refresh_csrf("session") is None
        assert not await verify_refresh_csrf("session", proof)
        # Redis expiry invalidates a proof; a future session must get a new proof.
        await store_refresh_token(1, "session", "new-refresh")
        assert await get_or_create_refresh_csrf("session") != proof
        await redis.expire("refresh_csrf:session", 0)
        assert not await verify_refresh_csrf("session", proof)
        await redis.aclose()

    asyncio.run(scenario())
