import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import stripe

from app.core.config.settings import SETTINGS
from app.core.error.billing_exception import BillingException
from app.models.billing import BillingCustomers, BillingSetupForm
from app.services.billing import BillingService
from tests.fixtures.billing_data import SETUP_REQUEST, provider_stub, stripe_object


@pytest.fixture
def provider(monkeypatch):
    for key, value in {
        "STRIPE_ENABLED": True,
        "STRIPE_SECRET_KEY": "sk_test_fixture",
        "STRIPE_SETUP_SUCCESS_URL": "http://localhost:5173/settings?setup={CHECKOUT_SESSION_ID}",
        "STRIPE_SETUP_CANCEL_URL": "http://localhost:5173/settings",
    }.items():
        monkeypatch.setattr(SETTINGS, key, value)
    client = provider_stub()
    monkeypatch.setattr(stripe, "StripeClient", lambda *args, **kwargs: client)
    row = SimpleNamespace(
        stripe_customer_id="cus_fixture",
        livemode=False,
        creation_key="stable",
        created_at=datetime.now(UTC),
    )
    monkeypatch.setattr(BillingCustomers, "get", AsyncMock(return_value=row))
    monkeypatch.setattr(BillingCustomers, "reserve", AsyncMock(return_value=row))
    monkeypatch.setattr(BillingCustomers, "bind", AsyncMock(return_value="cus_fixture"))
    return client


def test_setup_has_no_charge_and_reuses_request_key(provider):
    """Scenario: setup retries preserve customer-scoped idempotency and enable card/Link."""
    # Given: the same logical request twice.
    service = BillingService()
    form = BillingSetupForm(**SETUP_REQUEST)
    # When: setup is retried.
    asyncio.run(service.create_setup(1, form))
    asyncio.run(service.create_setup(1, form))
    # Then: no payment amount is supplied and the remote key remains identical.
    calls = provider.v1.checkout.sessions.create_async.call_args_list
    assert calls[0] == calls[1]
    assert calls[0].kwargs["params"]["mode"] == "setup"
    assert calls[0].kwargs["params"]["payment_method_types"] == ["card", "link"]
    assert "line_items" not in calls[0].kwargs["params"]
    assert "cus_fixture" in calls[0].kwargs["options"]["idempotency_key"]
    provider.v1.customers.create_async.assert_not_called()


@pytest.mark.parametrize(
    "field,value",
    [
        ("customer", "cus_other"),
        ("client_reference_id", "2"),
        ("mode", "payment"),
        ("livemode", True),
    ],
)
def test_session_ownership_checked(provider, field, value):
    """Scenario: another customer's or mode's session cannot disclose registration state."""
    # Given: a session that does not match this registration owner.
    provider.v1.checkout.sessions.retrieve_async.return_value[field] = value
    # When/Then: retrieval fails with a nondisclosing not-found error.
    with pytest.raises(BillingException) as exc:
        asyncio.run(BillingService().setup_status(1, "cs_test_fixture"))
    assert exc.value.code.error == "BILLING_NOT_FOUND"


@pytest.mark.parametrize(
    "status,intent_status,registered",
    [
        ("open", "succeeded", False),
        ("complete", "processing", False),
        ("complete", "succeeded", True),
        ("expired", "requires_payment_method", False),
    ],
)
def test_registration_requires_successful_setup_intent(provider, status, intent_status, registered):
    """Scenario: a browser redirect or completed Checkout alone does not prove registration."""
    # Given: the authoritative Stripe states.
    session = provider.v1.checkout.sessions.retrieve_async.return_value
    session.status = status
    session.setup_intent.status = intent_status
    # When/Then: both completion conditions must hold.
    result = asyncio.run(BillingService().setup_status(1, session.id))
    assert result.registered is registered


def test_customer_retry_uses_persisted_identity(provider):
    """Scenario: ambiguous customer creation is retried with the persisted stable key."""
    # Given: an unbound durable reservation.
    BillingCustomers.reserve.return_value.stripe_customer_id = None
    # When: setup creates and binds the customer.
    asyncio.run(BillingService().create_setup(1, BillingSetupForm(**SETUP_REQUEST)))
    # Then: mutable email/name are absent from idempotent parameters.
    call = provider.v1.customers.create_async.call_args
    assert call.kwargs["options"]["idempotency_key"] == "billing-customer:stable"
    assert call.kwargs["params"] == {"metadata": {"billing_identity": "stable", "user_id": "1"}}
    BillingCustomers.bind.assert_awaited_once_with(1, False, "cus_fixture")


def test_expired_customer_retry_fails_closed(provider):
    """Scenario: expired Stripe idempotency retention cannot silently create duplicates."""
    # Given: an unresolved reservation older than the safe retry window.
    row = BillingCustomers.reserve.return_value
    row.stripe_customer_id = None
    row.created_at = datetime.now(UTC) - timedelta(days=2)
    # When/Then: reconciliation is required and Stripe receives no create request.
    with pytest.raises(BillingException) as exc:
        asyncio.run(BillingService().create_setup(1, BillingSetupForm(**SETUP_REQUEST)))
    assert exc.value.code.error == "BILLING_RECONCILIATION_REQUIRED"
    provider.v1.customers.create_async.assert_not_called()


@pytest.mark.parametrize(
    "error", [stripe.APIConnectionError("sensitive provider text"), TimeoutError()]
)
def test_provider_failure_is_sanitized(provider, error):
    """Scenario: Stripe/timeout errors use the domain envelope without sensitive text."""
    # Given: provider creation fails.
    provider.v1.checkout.sessions.create_async.side_effect = error
    # When/Then: a typed, sanitized failure propagates.
    with pytest.raises(BillingException) as exc:
        asyncio.run(BillingService().create_setup(1, BillingSetupForm(**SETUP_REQUEST)))
    assert exc.value.code.error == "BILLING_UNAVAILABLE"
    assert "sensitive" not in str(exc.value)


def test_list_is_customer_scoped_and_returns_safe_fields(provider):
    """Scenario: card lists are cursor-paginated and expose no full credentials."""
    # Given: the provider includes extra private fields.
    provider.v1.customers.payment_methods.list_async.return_value = stripe_object(
        has_more=True,
        data=[
            {
                "id": "pm_fixture",
                "type": "card",
                "billing_details": {"email": "private@example.com"},
                "card": {
                    "brand": "visa",
                    "last4": "4242",
                    "exp_month": 12,
                    "exp_year": 2030,
                    "fingerprint": "secret",
                },
            }
        ],
    )
    # When: a customer-scoped page is requested.
    result = asyncio.run(BillingService().list_payment_methods(1, "card", 20, "pm_previous"))
    # Then: pagination is explicit and only allowlisted fields survive.
    assert result.next_cursor == "pm_fixture"
    assert "fingerprint" not in result.model_dump_json()
    assert "private@" not in result.model_dump_json()
    provider.v1.customers.payment_methods.list_async.assert_awaited_once_with(
        "cus_fixture", params={"type": "card", "limit": 20, "starting_after": "pm_previous"}
    )


def test_link_summary_does_not_assume_card_shape(provider):
    """Scenario: Link returns a safe method identifier without invented card metadata."""
    # Given: a Link payment method with no card details.
    provider.v1.customers.payment_methods.list_async.return_value = stripe_object(
        has_more=False,
        data=[{"id": "pm_link", "type": "link", "link": {"email": "private@example.com"}}],
    )
    # When/Then: the summary tolerates absent card details and redacts email.
    result = asyncio.run(BillingService().list_payment_methods(1, "link", 20, None))
    assert result.items[0].last4 is None
    assert "private@" not in result.model_dump_json()


@pytest.mark.parametrize(
    "setting,value",
    [
        ("STRIPE_ENABLED", False),
        ("STRIPE_SECRET_KEY", ""),
        ("STRIPE_SETUP_SUCCESS_URL", "https://example.com/no-placeholder"),
        ("STRIPE_SETUP_CANCEL_URL", "javascript:alert(1)"),
        ("STRIPE_SECRET_KEY", "sk_live_requires_https"),
    ],
)
def test_invalid_configuration_disables_billing(provider, monkeypatch, setting, value):
    """Scenario: incomplete or unsafe configuration prevents provider traffic."""
    # Given: one invalid configuration value.
    monkeypatch.setattr(SETTINGS, setting, value)
    # When/Then: all mutation traffic fails closed.
    assert BillingService().config().enabled is False
    with pytest.raises(BillingException) as exc:
        asyncio.run(BillingService().create_setup(1, BillingSetupForm(**SETUP_REQUEST)))
    assert exc.value.code.error == "BILLING_DISABLED"
    provider.v1.checkout.sessions.create_async.assert_not_called()


@pytest.mark.parametrize("mode", [True, None])
def test_setup_requires_expanded_intent_mode(provider, mode):
    """Scenario: hosted setup verifies the expanded intent mode before reporting registration."""
    # Given: a complete owner-matched session with an inconsistent intent mode.
    provider.v1.checkout.sessions.retrieve_async.return_value.setup_intent.livemode = mode
    # When: the server confirms registration.
    result = asyncio.run(BillingService().setup_status(1, "cs_test_fixture"))
    # Then: the enclosing session alone cannot establish registration.
    assert result.registered is False
