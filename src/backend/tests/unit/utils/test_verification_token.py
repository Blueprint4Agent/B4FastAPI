import asyncio
from unittest.mock import AsyncMock

import fakeredis.aioredis

from app.core.cache.redis import RedisManager
from app.utils.token import consume_email_verification_token, store_email_verification_token


def test_verification_token_has_one_winner_and_rejects_replaced_tokens(monkeypatch):
    async def scenario():
        # Given: a live challenge and overlapping reads, as concurrent HTTP requests allow.
        client = fakeredis.aioredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(RedisManager, "get_client", AsyncMock(return_value=client))
        await store_email_verification_token(123, "first-token")
        original_get = client.get

        async def overlapping_get(key):
            value = await original_get(key)
            await asyncio.sleep(0)
            return value

        monkeypatch.setattr(client, "get", overlapping_get)
        # When: two consumers try the same one-time token together.
        results = await asyncio.gather(
            consume_email_verification_token("first-token"),
            consume_email_verification_token("first-token"),
        )
        # Then: exactly one owns activation, and a resend invalidates the older link.
        assert results.count(123) == 1
        assert results.count(None) == 1
        await store_email_verification_token(123, "old-token")
        await store_email_verification_token(123, "new-token")
        assert await consume_email_verification_token("old-token") is None
        assert await consume_email_verification_token("new-token") == 123
        assert await consume_email_verification_token("new-token") is None
        await client.aclose()

    asyncio.run(scenario())
