import asyncio

from app.core.observability import integration_health
from app.core.observability.integration_health import IntegrationHealth


def test_provider_checks_share_inflight_and_cache(monkeypatch):
    """Scenario: concurrent administrator reads reuse one check and retry after cache expiry."""

    async def scenario():
        health = IntegrationHealth()
        count = 0

        async def probe():
            nonlocal count
            count += 1
            await asyncio.sleep(0)

        # Given / When: concurrent requests for one configured provider.
        results = await asyncio.gather(*(health.check("email", True, probe) for _ in range(5)))
        # Then: only one probe runs and subsequent requests reuse it.
        assert count == 1
        assert all(result.status == "ok" for result in results)
        await health.check("email", True, probe)
        assert count == 1
        monkeypatch.setattr(integration_health, "CACHE_SECONDS", 0)
        await health.check("email", True, probe)
        assert count == 2
        await health.reset()

    asyncio.run(scenario())


def test_provider_timeout_does_not_duplicate_pending_work(monkeypatch):
    """Scenario: slow SMTP remains single-flight after a bounded response times out."""
    monkeypatch.setattr(integration_health, "RESPONSE_TIMEOUT_SECONDS", 0.001)

    async def scenario():
        health = IntegrationHealth()
        release = asyncio.Event()
        count = 0

        async def probe():
            nonlocal count
            count += 1
            await release.wait()

        # Given / When: two requests while the same network operation is pending.
        assert (await health.check("email", True, probe)).status == "timeout"
        assert (await health.check("email", True, probe)).status == "timeout"
        # Then: no duplicate is started and recovery can be observed later.
        assert count == 1
        release.set()
        await asyncio.sleep(0)
        assert (await health.check("email", True, probe)).status == "ok"
        await health.reset()

    asyncio.run(scenario())


def test_disabled_and_failed_checks_do_not_expose_provider_errors():
    """Scenario: disabled probes are skipped and provider failure strings never escape."""

    async def scenario():
        health = IntegrationHealth()
        count = 0

        async def probe():
            nonlocal count
            count += 1
            raise RuntimeError("smtp-secret-password")

        # Given / When / Then: disabled does not make a network request.
        assert (await health.check("email", False, probe)).status == "disabled"
        assert count == 0
        result = await health.check("email", True, probe)
        assert result.status == "failed"
        assert "secret" not in result.model_dump_json()
        await health.reset()

    asyncio.run(scenario())


def test_smtp_probe_authenticates_without_sending(monkeypatch):
    """Scenario: a periodic mail probe authenticates and closes without delivering a message."""
    from unittest.mock import MagicMock

    from app.core.config import Settings
    from app.core.mail.service import MailService

    # Given: an enabled SMTP provider with bounded probe settings.
    settings = Settings().model_copy(
        update={
            "EMAIL_ENABLED": True,
            "SMTP_HOST": "smtp.example.com",
            "SMTP_PORT": 587,
            "SMTP_USERNAME": "operator",
            "SMTP_PASSWORD": "private-password",
            "SMTP_USE_SSL": False,
            "SMTP_USE_STARTTLS": True,
            "EMAIL_FROM": "operator@example.com",
        }
    )
    client = MagicMock()
    factory = MagicMock(return_value=client)
    monkeypatch.setattr("app.core.mail.service.smtplib.SMTP", factory)
    # When: probing the connection.
    asyncio.run(MailService(settings).check_connection())
    # Then: the probe authenticates, applies a short socket timeout, and never sends email.
    assert factory.call_args.kwargs["timeout"] == 2
    client.login.assert_called_once_with("operator", "private-password")
    client.send_message.assert_not_called()
    client.__exit__.assert_called_once()


def test_stripe_probe_only_reads_checkout_sessions(monkeypatch):
    """Scenario: provider checks never create a customer, payment or checkout."""
    from contextlib import asynccontextmanager
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from app.services.billing import BillingService

    read = AsyncMock()
    client = SimpleNamespace(
        v1=SimpleNamespace(checkout=SimpleNamespace(sessions=SimpleNamespace(list_async=read)))
    )

    @asynccontextmanager
    async def provider():
        yield client

    # Given / When: a probe uses the existing authenticated provider boundary.
    service = BillingService()
    monkeypatch.setattr(service, "_provider", provider)
    asyncio.run(service.check_connection())
    # Then: one bounded read is performed and its customer data is discarded.
    read.assert_awaited_once_with(params={"limit": 1})
