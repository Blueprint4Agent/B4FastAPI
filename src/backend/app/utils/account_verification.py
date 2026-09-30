"""Atomic, user-bound email challenges stored as keyed hashes, never plaintext."""

import hashlib
import hmac
import json
import secrets

from redis.exceptions import WatchError

from app.core.cache.redis import RedisManager
from app.core.config.settings import SETTINGS


def _digest(user_id: int, nonce: str, code: str) -> str:
    return hmac.new(
        SETTINGS.SECRET_KEY.encode(),
        f"account-delete:{user_id}:{nonce}:{code}".encode(),
        hashlib.sha256,
    ).hexdigest()


async def issue_deletion_code(
    user_id: int,
    *,
    ttl: int,
    cooldown: int,
    request_limit: int,
    request_window: int,
    attempt_limit: int = 5,
) -> tuple[str | None, int]:
    redis = await RedisManager.get_client()
    prefix = f"account_delete:{user_id}"
    challenge, throttle, budget = (
        f"{prefix}:{part}" for part in ("challenge", "cooldown", "budget")
    )
    failures = f"{prefix}:failures"
    for _ in range(8):
        async with redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(challenge, throttle, budget, failures)
                if int(await pipe.get(failures) or 0) >= attempt_limit:
                    return None, max(1, await pipe.ttl(failures))
                remaining = await pipe.ttl(throttle)
                if remaining > 0:
                    return None, remaining
                requests = int(await pipe.get(budget) or 0)
                budget_ttl = await pipe.ttl(budget)
                if requests >= request_limit:
                    return None, max(1, budget_ttl)
                code = f"{secrets.randbelow(1_000_000):06d}"
                nonce = secrets.token_hex(16)
                payload = json.dumps({"nonce": nonce, "digest": _digest(user_id, nonce, code)})
                pipe.multi()
                pipe.set(challenge, payload, ex=ttl)
                pipe.set(throttle, "1", ex=cooldown)
                pipe.set(budget, requests + 1, ex=budget_ttl if budget_ttl > 0 else request_window)
                await pipe.execute()
                return code, cooldown
            except WatchError:
                continue
    raise RuntimeError("Deletion challenge contention")


async def consume_deletion_code(
    user_id: int, code: str, *, attempt_limit: int, window: int
) -> bool:
    redis = await RedisManager.get_client()
    prefix = f"account_delete:{user_id}"
    challenge, failures = f"{prefix}:challenge", f"{prefix}:failures"
    for _ in range(8):
        async with redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(challenge, failures)
                raw = await pipe.get(challenge)
                attempts = int(await pipe.get(failures) or 0)
                if attempts >= attempt_limit:
                    return False
                stored = json.loads(raw) if raw else None
                valid = stored is not None and hmac.compare_digest(
                    stored["digest"], _digest(user_id, stored["nonce"], code)
                )
                failure_ttl = await pipe.ttl(failures)
                pipe.multi()
                if valid:
                    pipe.delete(challenge)
                else:
                    pipe.set(failures, attempts + 1, ex=failure_ttl if failure_ttl > 0 else window)
                    if attempts + 1 >= attempt_limit:
                        pipe.delete(challenge)
                await pipe.execute()
                return valid
            except WatchError:
                continue
    raise RuntimeError("Deletion challenge contention")
