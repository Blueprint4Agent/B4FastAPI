"""Subscription checkout keeps prices and owner identity on the server."""

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import stripe
from sqlalchemy import update

from app.core.config.settings import SETTINGS
from app.core.db.session import get_db
from app.models.billing import BillingCheckout, BillingCheckouts
from app.services.billing import BillingService
from tests.fixtures.billing_data import SETUP_REQUEST, provider_stub, stripe_object
from tests.integration.api.v1.billing.test_billing_integration import login

pytestmark = pytest.mark.primary_data
FORM = {**SETUP_REQUEST, "plan": "monthly", "currency": "krw"}


def recurring_price(price_id):
    _, plan, currency = price_id.split("_")
    return stripe_object(
        id=price_id,
        active=True,
        livemode=False,
        currency=currency,
        unit_amount=3990 if currency == "krw" else 399,
        billing_scheme="per_unit",
        recurring={
            "interval": "month" if plan == "monthly" else "year",
            "interval_count": 1,
            "usage_type": "licensed",
        },
    )


def subscription(status="active"):
    return stripe_object(
        id="sub_fixture",
        livemode=False,
        customer="cus_fixture",
        status=status,
        currency="krw",
        cancel_at_period_end=False,
        items={"data": [{"price": {"id": "price_monthly_krw"}, "current_period_end": 1900000000}]},
    )


@pytest.fixture
def provider(monkeypatch):
    for key, value in {
        "STRIPE_ENABLED": True,
        "STRIPE_SECRET_KEY": "sk_test_fixture",
        "STRIPE_SETUP_SUCCESS_URL": "http://localhost/settings?billing_setup={CHECKOUT_SESSION_ID}",
        "STRIPE_SETUP_CANCEL_URL": "http://localhost/settings?billing_setup=cancelled",
        "STRIPE_CHECKOUT_SUCCESS_URL": "http://localhost/settings?billing_checkout={CHECKOUT_SESSION_ID}",
        "STRIPE_CHECKOUT_CANCEL_URL": "http://localhost/settings?billing_checkout=cancelled",
        **{
            f"STRIPE_{plan.upper()}_{currency.upper()}_PRICE_ID": f"price_{plan}_{currency}"
            for plan in ("monthly", "annual")
            for currency in ("krw", "usd")
        },
    }.items():
        monkeypatch.setattr(SETTINGS, key, value)
    client = provider_stub()
    client.v1.prices = SimpleNamespace(retrieve_async=AsyncMock(side_effect=recurring_price))
    client.v1.subscriptions = SimpleNamespace(
        list_async=AsyncMock(return_value=stripe_object(data=[], has_more=False))
    )
    client.v1.checkout.sessions.list_async = AsyncMock()
    client.v1.checkout.sessions.create_async.return_value = stripe_object(
        id="cs_test_checkout", status="open", url="https://checkout.stripe.com/c/pay/fixture"
    )
    client.v1.checkout.sessions.retrieve_async.return_value = stripe_object(
        id="cs_test_checkout",
        status="complete",
        mode="subscription",
        customer="cus_fixture",
        client_reference_id="1",
        livemode=False,
        payment_status="paid",
        subscription=subscription(),
    )
    monkeypatch.setattr(stripe, "StripeClient", lambda *args, **kwargs: client)
    return client


@pytest.mark.parametrize("auth_mode", ["bearer", "api_key"])
def test_catalog_checkout_and_verified_return(integration_client, provider, auth_mode):
    # Given: a real authenticated owner and a server-controlled catalog.
    client = integration_client
    headers = login(client)
    owner = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    provider.v1.checkout.sessions.retrieve_async.return_value.client_reference_id = str(owner)
    if auth_mode == "api_key":
        issued = client.post(
            "/api/v1/api-keys", headers=headers, json={"name": "billing-subscription"}
        )
        headers = {"X-API-Key": issued.json()["api_key"]}
    assert client.get("/api/v1/billing/subscription", headers=headers).json()["plan"] == "free"
    catalog = client.get("/api/v1/billing/plans", headers=headers)
    assert catalog.status_code == 200
    assert len(catalog.json()["prices"]) == 4
    # When: duplicate actions, including another client UUID, create checkout.
    for request_id in (FORM["request_id"], "ba0e57ca-066b-4dc3-bdd5-e25fa94fdf74"):
        result = client.post(
            "/api/v1/billing/checkout-sessions",
            headers=headers,
            json={**FORM, "request_id": request_id},
        )
        assert result.status_code == 201, result.text
    calls = provider.v1.checkout.sessions.create_async.call_args_list
    assert calls[0] == calls[1]
    assert calls[0].kwargs["params"]["line_items"] == [
        {"price": "price_monthly_krw", "quantity": 1}
    ]
    # Then: return is verified, and active subscriptions prevent a second purchase.
    provider.v1.subscriptions.list_async.return_value = stripe_object(
        data=[subscription()], has_more=False
    )
    result = client.get("/api/v1/billing/checkout-sessions/cs_test_checkout", headers=headers)
    assert result.json()["paid"] is True
    current = client.get("/api/v1/billing/subscription", headers=headers).json()
    assert current["plan"] == "monthly" and current["has_subscription"]
    assert (
        client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM).status_code
        == 409
    )


def test_wrong_owner_mode_and_unpaid_return(integration_client, provider):
    # Given: an existing owner checkout.
    client = integration_client
    headers = login(client)
    owner = client.get("/api/v1/auth/me", headers=headers).json()["id"]
    client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM)
    session = provider.v1.checkout.sessions.retrieve_async.return_value
    session.client_reference_id = str(owner)
    # When/Then: completed but unpaid sessions never confirm payment.
    session.payment_status = "unpaid"
    assert (
        client.get("/api/v1/billing/checkout-sessions/cs_test_checkout", headers=headers).json()[
            "paid"
        ]
        is False
    )
    for field, value in [
        ("customer", "cus_other"),
        ("client_reference_id", "999999"),
        ("livemode", True),
        ("mode", "setup"),
    ]:
        before = session[field]
        session[field] = value
        assert (
            client.get(
                "/api/v1/billing/checkout-sessions/cs_test_checkout", headers=headers
            ).status_code
            == 404
        )
        session[field] = before


def test_reservation_races_and_ambiguous_retry(integration_client, provider):
    # Given: multiple workers race on one authenticated account.
    client = integration_client
    headers = login(client)
    owner = client.get("/api/v1/auth/me", headers=headers).json()["id"]

    async def reserve():
        return await asyncio.gather(
            *[BillingCheckouts.reserve(owner, False, "price_monthly_krw") for _ in range(4)]
        )

    rows = asyncio.run(reserve())
    assert len({row.creation_key for row in rows}) == 1
    success = provider.v1.checkout.sessions.create_async.return_value
    provider.v1.checkout.sessions.create_async.side_effect = [
        stripe.APIConnectionError("ambiguous"),
        success,
    ]
    # When/Then: failed provider creation reuses all parameters and rejects a different plan.
    assert (
        client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM).status_code
        == 502
    )
    assert (
        client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM).status_code
        == 201
    )
    calls = provider.v1.checkout.sessions.create_async.call_args_list
    assert calls[0] == calls[1]
    assert (
        client.post(
            "/api/v1/billing/checkout-sessions", headers=headers, json={**FORM, "plan": "annual"}
        ).status_code
        == 409
    )

    async def age():
        async with get_db() as db:
            await db.execute(
                update(BillingCheckout).values(expires_at=datetime.now(UTC) + timedelta(minutes=20))
            )
            await db.commit()

    asyncio.run(age())
    assert (
        client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM).status_code
        == 409
    )


@pytest.mark.parametrize(
    "override",
    [
        {"currency": "usd"},
        {"active": False},
        {"livemode": True},
        {"unit_amount": None},
        {"recurring": {"interval": "week", "interval_count": 1, "usage_type": "licensed"}},
    ],
)
def test_wrong_provider_price_fails_closed(integration_client, provider, override):
    # Given/When: configured pricing no longer matches its server allowlist slot.
    headers = login(integration_client)
    price = recurring_price("price_monthly_krw")
    for key, value in override.items():
        price[key] = stripe_object(**value) if isinstance(value, dict) else value
    provider.v1.prices.retrieve_async.side_effect = None
    provider.v1.prices.retrieve_async.return_value = price
    result = integration_client.post(
        "/api/v1/billing/checkout-sessions", headers=headers, json=FORM
    )
    # Then: no customer or checkout resource is created.
    assert result.status_code == 503
    provider.v1.customers.create_async.assert_not_called()
    provider.v1.checkout.sessions.create_async.assert_not_called()


def test_unknown_subscription_and_pagination_never_look_free(integration_client, provider):
    # Given: an existing customer, including a Stripe-side subscription outside this catalog.
    headers = login(integration_client)
    integration_client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM)
    item = subscription("past_due")
    item["items"].data[0].price.id = "price_other"
    provider.v1.subscriptions.list_async.return_value = stripe_object(data=[item], has_more=False)
    result = integration_client.get("/api/v1/billing/subscription", headers=headers).json()
    assert result["plan"] == "unknown" and result["has_subscription"]
    provider.v1.subscriptions.list_async.return_value.has_more = True
    # Provider changes are reconciled by synchronization, not every GET.
    owner = integration_client.get("/api/v1/auth/me", headers=headers).json()["id"]
    from app.core.error.billing_exception import BillingException

    with pytest.raises(BillingException):
        asyncio.run(BillingService().sync_subscription(owner))
    # A failed synchronization cannot turn the last known unknown plan into Free.
    assert (
        integration_client.get("/api/v1/billing/subscription", headers=headers).json()["plan"]
        == "unknown"
    )


def test_startup_validates_recurring_prices(provider):
    # Given/When: subscription-enabled startup performs read-only price validation.
    asyncio.run(BillingService().initialize())
    # Then: every price is checked and no customer or checkout is created.
    assert provider.v1.prices.retrieve_async.await_count == 4
    provider.v1.customers.create_async.assert_not_called()
    provider.v1.checkout.sessions.create_async.assert_not_called()


def test_checkout_history_blocks_account_deletion(integration_client, provider):
    from app.core.error.auth_exception import AuthException
    from app.models.user import Users

    # Given: an owner who has started subscription checkout.
    client = integration_client
    headers = login(client)
    owner = client.get("/api/v1/auth/me", headers=headers).json()
    assert (
        client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM).status_code
        == 201
    )
    # When/Then: local deletion cannot orphan recurring billing; operator review is required.
    with pytest.raises(AuthException) as error:
        asyncio.run(Users.delete_account(owner["id"], owner["email"]))
    assert error.value.code.error == "ACCOUNT_BILLING_REVIEW_REQUIRED"
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200


@pytest.mark.parametrize("mode", [True, None])
def test_checkout_requires_expanded_subscription_mode(integration_client, provider, mode):
    """Scenario: a valid session cannot confirm a subscription with a mismatched or absent mode."""
    # Given: an authenticated checkout with a valid enclosing session.
    headers = login(integration_client)
    owner = integration_client.get("/api/v1/auth/me", headers=headers).json()["id"]
    integration_client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM)
    session = provider.v1.checkout.sessions.retrieve_async.return_value
    session.client_reference_id = str(owner)
    session.subscription.livemode = mode
    # When: the return URL triggers server verification.
    response = integration_client.get(
        "/api/v1/billing/checkout-sessions/cs_test_checkout", headers=headers
    )
    # Then: it never claims payment from the session alone.
    assert response.status_code == 200
    assert response.json()["paid"] is False


def test_multiple_subscriptions_persist_nonpurchasable_unknown(integration_client, provider):
    """Scenario: ambiguous provider subscriptions cannot advertise absence of a subscription."""
    # Given: two active subscriptions belonging to the same customer.
    headers = login(integration_client)
    integration_client.post("/api/v1/billing/checkout-sessions", headers=headers, json=FORM)
    second = subscription()
    second.id = "sub_second"
    provider.v1.subscriptions.list_async.return_value = stripe_object(
        data=[subscription(), second], has_more=False
    )
    # When: synchronization persists the reconciliation state.
    response = integration_client.get("/api/v1/billing/subscription", headers=headers)
    # Then: both the snapshot and purchase guard reject a new purchase.
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["plan"] == "unknown"
    assert snapshot["status"] == "reconciliation_required"
    assert snapshot["has_subscription"] is True
    assert snapshot["can_manage"] is False
    assert (
        integration_client.get("/api/v1/billing/subscription", headers=headers).json() == snapshot
    )
    assert (
        integration_client.post(
            "/api/v1/billing/checkout-sessions", headers=headers, json=FORM
        ).status_code
        == 409
    )
