import asyncio
import json
import logging
import traceback
from unittest.mock import AsyncMock

import pytest
import stripe
from fastapi.testclient import TestClient

from app.core.config.settings import SETTINGS
from app.services.billing import BillingService


@pytest.fixture
def configured(monkeypatch):
    for key, value in {
        "STRIPE_ENABLED": True,
        "STRIPE_SECRET_KEY": "sk_test_privatefixture",
        "STRIPE_SETUP_SUCCESS_URL": "http://localhost:5173/settings?setup={CHECKOUT_SESSION_ID}",
        "STRIPE_SETUP_CANCEL_URL": "http://localhost:5173/settings",
    }.items():
        monkeypatch.setattr(SETTINGS, key, value)


@pytest.fixture
def transport(monkeypatch):
    mock = AsyncMock(
        return_value=(
            json.dumps(
                {"object": "list", "data": [], "has_more": False, "url": "/v1/checkout/sessions"}
            ).encode(),
            200,
            {"request-id": "req_startup"},
        )
    )
    monkeypatch.setattr(stripe.HTTPXClient, "request_async", mock)
    return mock


def test_disabled_startup_never_constructs_provider(monkeypatch):
    """Scenario: disabled billing ignores missing configuration and performs no Stripe I/O."""
    # Given: disabled Stripe and a constructor that must not be called.
    monkeypatch.setattr(SETTINGS, "STRIPE_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "STRIPE_SECRET_KEY", "")
    constructor = AsyncMock(side_effect=AssertionError("Provider must not be constructed"))
    monkeypatch.setattr(stripe, "StripeClient", constructor)
    # When/Then: initialization returns without touching the provider.
    asyncio.run(BillingService().initialize())
    constructor.assert_not_called()


@pytest.mark.parametrize(
    "name,value",
    [
        ("STRIPE_SECRET_KEY", ""),
        ("STRIPE_SECRET_KEY", "pk_test_wrong"),
        ("STRIPE_SECRET_KEY", "sk_test_"),
        ("STRIPE_SETUP_SUCCESS_URL", "https://example.com/no-placeholder"),
        ("STRIPE_SETUP_CANCEL_URL", "javascript:private"),
        ("STRIPE_SETUP_CANCEL_URL", "http://localhost:99999/settings"),
        ("STRIPE_SETUP_CANCEL_URL", "https://user:private@example.com"),
        ("STRIPE_SETUP_CANCEL_URL", "https://example.com/#private"),
    ],
)
def test_bad_config_aborts_before_network(configured, transport, monkeypatch, name, value):
    """Scenario: an invalid field is named without logging its secret or URL value."""
    # Given: enabled billing with one invalid setting.
    monkeypatch.setattr(SETTINGS, name, value)
    # When/Then: startup fails before calling Stripe, with a useful field name.
    with pytest.raises(RuntimeError, match=name) as exc:
        asyncio.run(BillingService().initialize())
    assert "private" not in str(exc.value)
    transport.assert_not_awaited()


@pytest.mark.parametrize(
    "key", ["sk_test_privatefixture", "rk_test_privatefixture", "sk_live_privatefixture"]
)
def test_enabled_startup_uses_read_only_sdk_probe(configured, transport, monkeypatch, caplog, key):
    """Scenario: valid test/restricted/live keys are checked through the real SDK without mutation."""
    # Given: valid local configuration; account activation is not a condition for sandbox use.
    monkeypatch.setattr(SETTINGS, "STRIPE_SECRET_KEY", key)
    monkeypatch.setattr(
        SETTINGS, "STRIPE_SETUP_SUCCESS_URL", "https://example.com/?setup={CHECKOUT_SESSION_ID}"
    )
    monkeypatch.setattr(SETTINGS, "STRIPE_SETUP_CANCEL_URL", "https://example.com/")
    close = AsyncMock()
    original_close = stripe.HTTPXClient.close_async

    async def close_client(client):
        await original_close(client)
        await close()

    monkeypatch.setattr(stripe.HTTPXClient, "close_async", close_client)
    # When: the actual SDK receives a synthetic successful HTTP response.
    with caplog.at_level(logging.INFO, logger="uvicorn"):
        asyncio.run(BillingService().initialize())
    # Then: the probe is one bounded read, logs only mode/result, and closes transport.
    transport.assert_awaited_once()
    method, url = transport.call_args.args[:2]
    assert method.lower() == "get"
    assert url == "https://api.stripe.com/v1/checkout/sessions?limit=1"
    assert key not in caplog.text
    assert "Stripe startup verification succeeded" in caplog.text
    close.assert_awaited_once()


@pytest.mark.parametrize(
    "http_status,error_type,expected",
    [
        (401, "invalid_request_error", "authentication rejected"),
        (403, "invalid_request_error", "read permission denied"),
        (500, "api_error", "request failed or timed out"),
    ],
)
def test_provider_errors_abort_with_sanitized_reason(
    configured, transport, monkeypatch, http_status, error_type, expected
):
    """Scenario: provider failures stop startup without printing raw provider data or keys."""
    # Given: a failed response from the real SDK transport (no retry delay in this test).
    transport.return_value = (
        json.dumps(
            {
                "error": {
                    "type": error_type,
                    "message": "PRIVATE_PROVIDER_DATA sk_test_privatefixture",
                }
            }
        ).encode(),
        http_status,
        {},
    )
    monkeypatch.setattr(stripe.HTTPXClient, "sleep_async", AsyncMock())
    # When/Then: failure is readable but sanitized even in the formatted startup traceback.
    with pytest.raises(RuntimeError, match=expected) as exc:
        asyncio.run(BillingService().initialize())
    formatted = "".join(traceback.format_exception(exc.value))
    assert "PRIVATE_PROVIDER_DATA" not in formatted
    assert "sk_test_privatefixture" not in formatted


@pytest.mark.parametrize(
    "error", [stripe.APIConnectionError("private connection failure"), TimeoutError()]
)
def test_network_timeout_aborts_startup(configured, transport, error):
    """Scenario: network failures and the outer timeout fail closed."""
    # Given: a failed transport.
    transport.side_effect = error
    # When/Then: no successful startup is possible.
    with pytest.raises(RuntimeError, match="request failed or timed out"):
        asyncio.run(BillingService().initialize())


def test_live_configuration_requires_https(configured, transport, monkeypatch):
    """Scenario: a live key with insecure return URLs fails before reaching Stripe."""
    # Given: the default HTTP fixture URLs with a live secret.
    monkeypatch.setattr(SETTINGS, "STRIPE_SECRET_KEY", "sk_live_privatefixture")
    # When/Then: local validation explains the required HTTPS return URLs.
    with pytest.raises(RuntimeError, match="live mode requires HTTPS"):
        asyncio.run(BillingService().initialize())
    transport.assert_not_awaited()


@pytest.mark.parametrize("reject", [False, True])
def test_lifespan_waits_for_stripe_before_migrations(configured, transport, monkeypatch, reject):
    """Scenario: FastAPI startup only proceeds after the actual Stripe initializer succeeds."""
    import app.main as main

    # Given: isolated application dependencies and the actual Stripe SDK probe.
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "OAUTH_ENABLED", False)
    monkeypatch.setattr(main.MAIL_SERVICE, "initialize", AsyncMock())
    migrations = AsyncMock()
    monkeypatch.setattr(main, "run_startup_schema_migrations", migrations)
    monkeypatch.setattr(main, "init_db", AsyncMock())
    monkeypatch.setattr(main, "dispose_db", AsyncMock())
    monkeypatch.setattr(main.RedisManager, "close", AsyncMock())
    if reject:
        transport.side_effect = TimeoutError()
    # When/Then: a failure prevents both serving requests and migrations.
    if reject:
        with pytest.raises(RuntimeError, match="Stripe startup verification failed"):
            with TestClient(main.create_app()):
                pytest.fail("Startup must not complete")
        migrations.assert_not_awaited()
    else:
        with TestClient(main.create_app()) as client:
            assert client.get("/ping").status_code == 200
        migrations.assert_awaited_once()
        transport.assert_awaited_once()
