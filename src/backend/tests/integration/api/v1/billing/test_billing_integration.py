import asyncio
from unittest.mock import AsyncMock

import pytest
import stripe
from sqlalchemy import delete

from app.core.config.settings import SETTINGS
from app.core.db.session import get_db
from app.models.billing import BillingCustomers
from app.models.user import User
from tests.fixtures.billing_data import SETUP_REQUEST, provider_stub
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data


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
    return client


def login(client, email="billing@example.com"):
    assert (
        client.post("/api/v1/auth/signup", json=build_signup_payload(email=email)).status_code
        == 200
    )
    response = client.post("/api/v1/auth/login", json=build_login_payload(email=email))
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.mark.parametrize("auth_mode", ["bearer", "api_key"])
def test_card_setup_from_empty_state_reuses_customer(integration_client, provider, auth_mode):
    """Scenario: migrated empty DB stores one customer and reads confirmed Stripe state."""
    # Given: a new user with no billing profile.
    client = integration_client
    headers = login(client)
    if auth_mode == "api_key":
        issued = client.post("/api/v1/api-keys", headers=headers, json={"name": "billing"})
        assert issued.status_code == 200
        headers = {"X-API-Key": issued.json()["api_key"]}
    assert client.get("/api/v1/billing/config", headers=headers).json()["enabled"] is True
    user_id = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    provider.v1.checkout.sessions.retrieve_async.return_value.client_reference_id = str(user_id)
    assert client.get("/api/v1/billing/payment-methods", headers=headers).json()["items"] == []
    provider.v1.customers.create_async.assert_not_called()
    # When: setup is created and the same request is retried.
    for _ in range(2):
        result = client.post("/api/v1/billing/setup-sessions", headers=headers, json=SETUP_REQUEST)
        assert result.status_code == 201, result.text
    # Then: one customer mapping is persisted and real service status validates ownership.
    provider.v1.customers.create_async.assert_awaited_once()
    row = asyncio.run(BillingCustomers.get(user_id, False))
    assert row.stripe_customer_id == "cus_fixture"
    result = client.get("/api/v1/billing/setup-sessions/cs_test_fixture", headers=headers)
    assert result.status_code == 200
    assert result.json()["registered"] is True
    assert client.get("/api/v1/billing/payment-methods", headers=headers).status_code == 200
    provider.v1.customers.payment_methods.list_async.assert_awaited_once()
    assert provider.v1.customers.payment_methods.list_async.call_args.args[0] == "cus_fixture"
    # When/Then: another user cannot read the session and GET creates no customer.
    other = login(client, "other-billing@example.com")
    if auth_mode == "api_key":
        issued = client.post("/api/v1/api-keys", headers=other, json={"name": "other-billing"})
        other = {"X-API-Key": issued.json()["api_key"]}
    result = client.get("/api/v1/billing/setup-sessions/cs_test_fixture", headers=other)
    assert result.status_code == 404
    provider.v1.customers.create_async.assert_awaited_once()


def test_customer_reservation_is_concurrent_and_mode_isolated(integration_client, provider):
    """Scenario: concurrent reservations converge and test/live customers remain separate."""
    # Given: a migrated database and one user.
    headers = login(integration_client)
    user_id = integration_client.get("/api/v1/auth/me", headers=headers).json()["id"]

    async def exercise():
        # When: requests race before either has created a remote customer.
        rows = await asyncio.gather(*[BillingCustomers.reserve(user_id, False) for _ in range(4)])
        live = await BillingCustomers.reserve(user_id, True)
        # Then: the durable idempotency identity is shared only within the same mode.
        assert len({row.creation_key for row in rows}) == 1
        assert live.creation_key != rows[0].creation_key
        await BillingCustomers.bind(user_id, False, "cus_first")
        assert await BillingCustomers.bind(user_id, False, "cus_late") == "cus_first"
        # When/Then: deleting an owner cascades the local identities without remote calls.
        async with get_db() as db:
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()
        assert await BillingCustomers.get(user_id, False) is None
        assert await BillingCustomers.get(user_id, True) is None

    asyncio.run(exercise())


def test_provider_failure_retains_retry_identity(integration_client, provider):
    """Scenario: failure before binding preserves the same remote idempotency identity."""
    # Given: an ambiguous first provider failure followed by successful retry.
    headers = login(integration_client)
    success = provider.v1.customers.create_async.return_value
    provider.v1.customers.create_async = AsyncMock(
        side_effect=[stripe.APIConnectionError("lost"), success]
    )
    # When: the same setup is retried after a provider error.
    first = integration_client.post(
        "/api/v1/billing/setup-sessions", headers=headers, json=SETUP_REQUEST
    )
    second = integration_client.post(
        "/api/v1/billing/setup-sessions", headers=headers, json=SETUP_REQUEST
    )
    # Then: the failed request does not lose or rotate the stored identity.
    assert first.status_code == 502
    assert second.status_code == 201
    calls = provider.v1.customers.create_async.call_args_list
    assert calls[0] == calls[1]


@pytest.mark.mocked_data
def test_existing_account_can_add_billing_identity(seeded_integration_client, provider):
    """Scenario: existing seeded accounts can register without replacing auth identity."""
    from tests.fixtures.scenario_seed_data import DEFAULT_SEED_PROFILE

    # Given: an existing seeded account with its original authentication identity.
    client = seeded_integration_client
    primary = DEFAULT_SEED_PROFILE.primary_user
    response = client.post(
        "/api/v1/auth/login",
        json=build_login_payload(email=primary.email, password=primary.password),
    )
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    before = client.get("/api/v1/auth/me", headers=headers).json()
    # When: the existing account requests charge-free registration.
    result = client.post("/api/v1/billing/setup-sessions", headers=headers, json=SETUP_REQUEST)
    # Then: the billing mapping is added and authentication/profile data is unchanged.
    assert result.status_code == 201
    after = client.get("/api/v1/auth/me", headers=headers).json()
    assert before == after
    row = asyncio.run(BillingCustomers.get(before["id"], False))
    assert row.stripe_customer_id == "cus_fixture"
