import asyncio
from unittest.mock import AsyncMock

import fakeredis.aioredis
import pytest

from app.utils.account_verification import consume_deletion_code, issue_deletion_code


@pytest.mark.parametrize("purpose", ["account_delete", "password_change"])
def test_codes_are_user_bound_expiring_single_use_and_attempt_limited(monkeypatch, purpose):
    """Scenario: email possession is checked atomically and cannot be bypassed by replay or resend."""

    async def scenario():
        # Given: isolated Redis and a user-bound challenge.
        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(
            "app.utils.account_verification.RedisManager.get_client", AsyncMock(return_value=redis)
        )

        def issue(user):
            return issue_deletion_code(
                user, ttl=600, cooldown=60, request_limit=5, request_window=3600, purpose=purpose
            )

        def consume(user, code):
            return consume_deletion_code(user, code, attempt_limit=5, window=600, purpose=purpose)

        code, _ = await issue(1)
        assert len(code) == 6 and code.isascii() and code.isdigit()
        assert code not in await redis.get(f"{purpose}:1:challenge")
        assert not await consume(2, code)
        # When: two requests race with the same correct code.
        outcomes = await asyncio.gather(consume(1, code), consume(1, code))
        # Then: only one may proceed to deletion; cooldown and attempts survive resends.
        assert outcomes.count(True) == 1
        assert (await issue(1))[0] is None
        for user_id in (3, 4):
            candidate, _ = await issue(user_id)
            if user_id == 3:
                await redis.delete(f"{purpose}:{user_id}:challenge")
                assert not await consume(user_id, candidate)
            else:
                wrong = "000000" if candidate != "000000" else "111111"
                for _ in range(5):
                    assert not await consume(user_id, wrong)
                assert not await consume(user_id, candidate)
                await redis.delete(f"{purpose}:4:cooldown")
                new_code, wait = await issue(4)
                assert new_code is None and wait > 60
        await redis.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("purpose", ["account_delete", "password_change"])
def test_resends_invalidate_previous_code_and_request_budget_is_bounded(monkeypatch, purpose):
    """Scenario: only the latest code works and repeated requests cannot flood a mailbox."""

    async def scenario():
        # Given: deterministic distinct codes and isolated storage.
        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(
            "app.utils.account_verification.RedisManager.get_client", AsyncMock(return_value=redis)
        )
        values = iter(range(123450, 123460))
        monkeypatch.setattr(
            "app.utils.account_verification.secrets.randbelow", lambda _: next(values)
        )
        first = None
        for _ in range(5):
            await redis.delete(f"{purpose}:1:cooldown")
            code, _ = await issue_deletion_code(
                1, ttl=600, cooldown=60, request_limit=5, request_window=3600, purpose=purpose
            )
            first = first or code
        # When: a sixth request arrives after the per-send cooldown.
        await redis.delete(f"{purpose}:1:cooldown")
        blocked, wait = await issue_deletion_code(
            1, ttl=600, cooldown=60, request_limit=5, request_window=3600, purpose=purpose
        )
        # Then: the hourly budget rejects it; the original code is invalid.
        assert blocked is None and wait > 60
        assert not await consume_deletion_code(
            1, first, attempt_limit=5, window=600, purpose=purpose
        )
        assert await consume_deletion_code(1, code, attempt_limit=5, window=600, purpose=purpose)
        await redis.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("purpose", ["account_delete", "password_change"])
def test_check_preserves_expiry_and_consumption_and_resend_resets_ttl(monkeypatch, purpose):
    """Scenario: checking does not extend a code; resending replaces it for ten minutes."""

    async def scenario():
        redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        monkeypatch.setattr(
            "app.utils.account_verification.RedisManager.get_client", AsyncMock(return_value=redis)
        )
        values = iter([123450, 123451])
        monkeypatch.setattr(
            "app.utils.account_verification.secrets.randbelow", lambda _: next(values)
        )
        first, wait = await issue_deletion_code(
            1, ttl=600, cooldown=30, request_limit=5, request_window=3600, purpose=purpose
        )
        assert wait == 30
        key = f"{purpose}:1:challenge"
        await redis.expire(key, 120)
        assert await consume_deletion_code(
            1, first, attempt_limit=5, window=600, purpose=purpose, consume=False
        )
        assert 0 < await redis.ttl(key) <= 120
        await redis.delete(f"{purpose}:1:cooldown")
        second, _ = await issue_deletion_code(
            1, ttl=600, cooldown=30, request_limit=5, request_window=3600, purpose=purpose
        )
        assert 590 <= await redis.ttl(key) <= 600
        assert not await consume_deletion_code(
            1, first, attempt_limit=5, window=600, purpose=purpose, consume=False
        )
        assert await consume_deletion_code(
            1, second, attempt_limit=5, window=600, purpose=purpose, consume=False
        )
        assert await consume_deletion_code(1, second, attempt_limit=5, window=600, purpose=purpose)
        assert not await consume_deletion_code(
            1, second, attempt_limit=5, window=600, purpose=purpose
        )
        await redis.aclose()

    asyncio.run(scenario())
