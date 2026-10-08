"""Owner-scoped period-end changes preserve paid time and provider truth."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.config.settings import SETTINGS
from app.models.billing import BillingCustomers
from tests.fixtures.billing_data import SETUP_REQUEST, stripe_object
from tests.integration.api.v1.billing.test_billing_integration import login
from tests.integration.api.v1.billing.test_subscription_integration import (
    provider as subscription_provider,
)

pytestmark = pytest.mark.primary_data


@pytest.fixture(name="provider")
def provider_fixture(monkeypatch):
    return subscription_provider.__wrapped__(monkeypatch)


@pytest.fixture
def managed(provider, monkeypatch):
    now = int(datetime.now(UTC).timestamp())
    sub = stripe_object(
        id="sub_fixture",
        customer="cus_fixture",
        livemode=False,
        status="active",
        currency="krw",
        cancel_at_period_end=False,
        schedule=None,
        items={
            "data": [
                {
                    "id": "si_fixture",
                    "price": {"id": "price_monthly_krw"},
                    "quantity": 1,
                    "current_period_end": now + 86400,
                    "current_period_start": now - 86400,
                }
            ]
        },
    )
    state = {"subscription": sub, "schedule": None}
    provider.v1.subscriptions.list_async.return_value = stripe_object(data=[sub], has_more=False)
    provider.v1.subscriptions.retrieve_async = AsyncMock(side_effect=lambda *_: sub)

    async def update_sub(_id, params, options):
        sub.cancel_at_period_end = params["cancel_at_period_end"]
        return sub

    provider.v1.subscriptions.update_async = AsyncMock(side_effect=update_sub)

    async def create_schedule(params, options):
        schedule = stripe_object(
            id="sub_sched_fixture",
            customer="cus_fixture",
            metadata={},
            current_phase={"start_date": now - 86400},
            phases=[],
        )
        state["schedule"] = schedule
        sub.schedule = schedule.id
        return schedule

    async def update_schedule(_id, params, options):
        schedule = state["schedule"]
        schedule.metadata = stripe_object(**params["metadata"])
        schedule.phases = [stripe_object(**phase) for phase in params["phases"]]
        return schedule

    async def release(_id, params, options):
        sub.schedule = None
        return state["schedule"]

    provider.v1.subscription_schedules = SimpleNamespace(
        create_async=AsyncMock(side_effect=create_schedule),
        retrieve_async=AsyncMock(side_effect=lambda *_: state["schedule"]),
        update_async=AsyncMock(side_effect=update_schedule),
        release_async=AsyncMock(side_effect=release),
    )
    monkeypatch.setattr(SETTINGS, "STRIPE_PORTAL_CONFIGURATION_ID", "bpc_fixture")
    provider.v1.customers.retrieve_async = AsyncMock(
        return_value=stripe_object(
            id="cus_fixture",
            livemode=False,
            preferred_locales=["ko-KR"],
            email="billing@example.com",
            name="Billing User",
            address={"city": "Seoul", "country": "KR"},
            invoice_settings={"default_payment_method": "pm_fixture"},
        )
    )
    provider.v1.invoices = SimpleNamespace(
        list_async=AsyncMock(
            return_value=stripe_object(
                data=[
                    {
                        "id": "in_fixture",
                        "number": "INV-1",
                        "created": now,
                        "status": "paid",
                        "amount_paid": 3990,
                        "amount_due": 3990,
                        "currency": "krw",
                        "hosted_invoice_url": "https://invoice.stripe.com/i/fixture",
                    }
                ],
                has_more=False,
            )
        )
    )
    provider.v1.billing_portal = SimpleNamespace(
        configurations=SimpleNamespace(
            retrieve_async=AsyncMock(
                return_value=stripe_object(
                    id="bpc_fixture",
                    active=True,
                    livemode=False,
                    features={
                        "customer_update": {
                            "enabled": True,
                            "allowed_updates": ["email", "name", "address"],
                        },
                        "payment_method_update": {"enabled": True},
                        "invoice_history": {"enabled": True},
                        "subscription_cancel": {"enabled": False},
                        "subscription_update": {"enabled": False},
                    },
                )
            )
        ),
        sessions=SimpleNamespace(
            create_async=AsyncMock(
                return_value=stripe_object(
                    id="bps_fixture", url="https://billing.stripe.com/p/session/fixture"
                )
            )
        ),
    )
    return provider, state


def ready(client):
    headers = login(client)
    assert (
        client.post(
            "/api/v1/billing/setup-sessions", headers=headers, json=SETUP_REQUEST
        ).status_code
        == 201
    )
    return headers


def change(client, headers, plan, version=None):
    snapshot = client.get("/api/v1/billing/subscription", headers=headers).json()
    return client.post(
        "/api/v1/billing/subscription/change",
        headers=headers,
        json={
            "plan": plan,
            "expected_version": version or snapshot["change_version"],
            "request_id": str(uuid4()),
        },
    )


def test_period_end_switch_cancel_and_restore(integration_client, managed):
    client = integration_client
    provider, state = managed
    headers = ready(client)
    before = client.get("/api/v1/billing/subscription", headers=headers).json()
    response = change(client, headers, "annual")
    assert response.status_code == 200, response.text
    assert response.json()["plan"] == "monthly"
    assert response.json()["pending_plan"] == "annual"
    assert response.json()["pending_effective_at"] == before["current_period_end"]
    params = provider.v1.subscription_schedules.update_async.call_args.kwargs["params"]
    assert params["proration_behavior"] == "none"
    assert params["phases"][0]["items"][0]["price"] == "price_monthly_krw"
    assert params["phases"][1]["items"][0]["price"] == "price_annual_krw"
    assert change(client, headers, "free", before["change_version"]).status_code == 409
    restored = change(client, headers, "keep")
    assert restored.status_code == 200 and restored.json()["pending_plan"] is None
    cancelled = change(client, headers, "free")
    assert cancelled.status_code == 200 and cancelled.json()["pending_plan"] == "free"
    assert cancelled.json()["plan"] == "monthly"
    assert change(client, headers, "keep").json()["cancel_at_period_end"] is False


def test_unknown_schedule_and_inactive_subscription_fail_closed(integration_client, managed):
    client = integration_client
    provider, state = managed
    headers = ready(client)
    state["subscription"].schedule = "sub_sched_external"
    state["schedule"] = stripe_object(
        id="sub_sched_external", customer="cus_fixture", metadata={}, phases=[]
    )
    assert client.get("/api/v1/billing/subscription", headers=headers).json()["can_manage"] is False
    assert change(client, headers, "free").status_code == 409
    provider.v1.subscriptions.update_async.assert_not_called()
    state["subscription"].schedule = None
    state["subscription"].status = "past_due"
    assert change(client, headers, "annual").status_code == 409


def test_profile_invoice_and_restricted_portal(integration_client, managed):
    client = integration_client
    provider, state = managed
    headers = ready(client)
    profile = client.get("/api/v1/billing/profile", headers=headers)
    assert profile.json()["default_payment_method"] == "pm_fixture"
    invoices = client.get("/api/v1/billing/invoices", headers=headers)
    assert invoices.json()["items"][0]["amount"] == 3990
    assert provider.v1.invoices.list_async.call_args.kwargs["params"]["customer"] == "cus_fixture"
    portal = client.post(
        "/api/v1/billing/portal-sessions",
        headers=headers,
        json={**SETUP_REQUEST, "flow": "customer_update"},
    )
    assert portal.status_code == 201
    args = provider.v1.billing_portal.sessions.create_async.call_args.kwargs["params"]
    assert args["customer"] == "cus_fixture" and args["return_url"].endswith("section=billing")
    provider.v1.billing_portal.configurations.retrieve_async.return_value.features.subscription_cancel.enabled = True
    assert (
        client.post(
            "/api/v1/billing/portal-sessions", headers=headers, json=SETUP_REQUEST
        ).status_code
        == 503
    )


def test_management_cannot_access_unmapped_customer(integration_client, managed):
    client = integration_client
    provider, state = managed
    headers = login(client)
    assert client.get("/api/v1/billing/invoices", headers=headers).json()["items"] == []
    assert (
        client.post(
            "/api/v1/billing/subscription/change",
            headers=headers,
            json={**SETUP_REQUEST, "plan": "free", "expected_version": "a" * 64},
        ).status_code
        == 404
    )
    provider.v1.subscriptions.update_async.assert_not_called()


def test_cancellation_is_available_near_renewal(integration_client, managed):
    client = integration_client
    _, state = managed
    headers = ready(client)
    state["subscription"]["items"].data[0].current_period_end = (
        int(datetime.now(UTC).timestamp()) + 30
    )
    assert change(client, headers, "annual").status_code == 409
    response = change(client, headers, "free")
    assert response.status_code == 200
    assert response.json()["pending_plan"] == "free"


def test_tier_catalog_preserves_legacy_plus_and_upgrades_pro(
    integration_client, managed, monkeypatch
):
    """Existing Plus prices remain recognized while new tiers use provider-owned prices."""
    from tests.integration.api.v1.billing.test_subscription_integration import recurring_price

    provider, state = managed
    for interval in ("monthly", "annual"):
        for currency in ("krw", "usd"):
            monkeypatch.setattr(
                SETTINGS,
                f"STRIPE_PRO_{interval.upper()}_{currency.upper()}_PRICE_ID",
                f"price_pro_{interval}_{currency}",
            )
    monkeypatch.setattr(SETTINGS, "STRIPE_PLUS_ANNUAL_KRW_PRICE_ID", "price_plus_annual_krw")

    def price(price_id):
        interval, currency = price_id.split("_")[-2:]
        result = recurring_price(f"price_{interval}_{currency}")
        result.id = price_id
        result.unit_amount = (
            (129276 if currency == "krw" else 12928)
            if interval == "annual"
            else (11970 if currency == "krw" else 1197)
        )
        return result

    provider.v1.prices.retrieve_async.side_effect = price
    headers = ready(integration_client)
    catalog = integration_client.get("/api/v1/billing/plans", headers=headers).json()
    assert len(catalog["prices"]) == 8
    assert any(
        item["plan"] == "pro_annual" and item["amount"] == 129276 for item in catalog["prices"]
    )
    state["subscription"]["items"].data[0].price.id = "price_annual_krw"
    old = integration_client.get("/api/v1/billing/subscription", headers=headers).json()
    assert old["plan"] == "annual" and old["can_manage"]

    async def upgrade(_id, params, options):
        state["subscription"]["items"].data[0].price.id = params["items"][0]["price"]
        return state["subscription"]

    provider.v1.subscriptions.update_async.side_effect = upgrade
    changed = change(integration_client, headers, "pro_monthly")
    assert changed.status_code == 200, changed.text
    assert changed.json()["plan"] == "pro_monthly"
    assert changed.json()["pending_plan"] is None
    owner = integration_client.get("/api/v1/auth/me", headers=headers).json()["id"]
    stored = asyncio.run(BillingCustomers.get(owner, False))
    assert stored.stripe_subscription_id == state["subscription"].id
    assert stored.subscription_snapshot == changed.json()
    params = provider.v1.subscriptions.update_async.call_args.kwargs["params"]
    assert params["items"][0] == {
        "id": "si_fixture",
        "price": "price_pro_monthly_krw",
        "quantity": 1,
    }
    assert params["payment_behavior"] == "pending_if_incomplete"
    assert params["proration_behavior"] == "always_invoice"
    provider.v1.subscription_schedules.create_async.assert_not_called()


def test_unconfigured_pro_cannot_be_purchased(integration_client, managed):
    headers = ready(integration_client)
    managed[0].v1.checkout.sessions.create_async.reset_mock()
    response = integration_client.post(
        "/api/v1/billing/checkout-sessions",
        headers=headers,
        json={"plan": "pro_annual", "currency": "usd", "request_id": str(uuid4())},
    )
    assert response.status_code >= 400
    assert response.json()["detail"]["error"] == "BILLING_PLAN_UNAVAILABLE"
    managed[0].v1.checkout.sessions.create_async.assert_not_called()


@pytest.mark.parametrize(
    "invoice_url", ["https://invoice.stripe.com/i/fixture", "https://evil.example/invoice"]
)
def test_upgrade_waits_for_payment_and_keeps_current_tier(
    integration_client, managed, monkeypatch, invoice_url
):
    from tests.integration.api.v1.billing.test_subscription_integration import recurring_price

    provider, state = managed
    monkeypatch.setattr(SETTINGS, "STRIPE_PRO_MONTHLY_KRW_PRICE_ID", "price_pro_monthly_krw")
    provider.v1.prices.retrieve_async.side_effect = lambda price_id: recurring_price(
        "price_monthly_krw"
    )
    headers = ready(integration_client)

    async def pending(_id, params, options):
        state["subscription"].pending_update = stripe_object(
            expires_at=1900000000,
            subscription_items=[{"price": {"unit_amount_decimal": Decimal("11970")}}],
        )
        state["subscription"].latest_invoice = "in_upgrade"
        return state["subscription"]

    provider.v1.subscriptions.update_async.side_effect = pending
    provider.v1.invoices.retrieve_async = AsyncMock(
        return_value=stripe_object(
            customer="cus_fixture", livemode=False, hosted_invoice_url=invoice_url
        )
    )
    response = change(integration_client, headers, "pro_monthly")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["plan"] == "monthly"
    assert body["payment_required"] and not body["can_manage"]
    assert body["payment_url"] == (invoice_url if "invoice.stripe.com" in invoice_url else None)
    assert change(integration_client, headers, "pro_monthly").status_code == 409
    provider.v1.subscriptions.update_async.assert_awaited_once()


def test_pro_downgrade_keeps_paid_tier_until_period_end(integration_client, managed, monkeypatch):
    provider, state = managed
    monkeypatch.setattr(SETTINGS, "STRIPE_PRO_MONTHLY_KRW_PRICE_ID", "price_pro_monthly_krw")
    headers = ready(integration_client)
    state["subscription"]["items"].data[0].price.id = "price_pro_monthly_krw"
    response = change(integration_client, headers, "monthly")
    assert response.status_code == 200, response.text
    assert response.json()["plan"] == "pro_monthly"
    assert response.json()["pending_plan"] == "monthly"
    provider.v1.subscriptions.update_async.assert_not_called()


def test_same_request_recovers_schedule_creation_after_update_failure(integration_client, managed):
    import stripe

    provider, state = managed
    headers = ready(integration_client)
    before = integration_client.get("/api/v1/billing/subscription", headers=headers).json()
    form = {
        "plan": "annual",
        "expected_version": before["change_version"],
        "request_id": str(uuid4()),
    }
    create = provider.v1.subscription_schedules.create_async.side_effect
    update = provider.v1.subscription_schedules.update_async.side_effect
    accepted = {}

    async def idempotent_create(params, options):
        key = options["idempotency_key"]
        if key in accepted:
            return accepted[key]
        if state["subscription"].schedule:
            raise stripe.InvalidRequestError("already scheduled", "from_subscription")
        accepted[key] = await create(params, options)
        return accepted[key]

    provider.v1.subscription_schedules.create_async.side_effect = idempotent_create
    provider.v1.subscription_schedules.update_async.side_effect = stripe.APIConnectionError(
        "offline"
    )
    assert (
        integration_client.post(
            "/api/v1/billing/subscription/change", headers=headers, json=form
        ).status_code
        == 502
    )
    provider.v1.subscription_schedules.update_async.side_effect = update
    result = integration_client.post(
        "/api/v1/billing/subscription/change", headers=headers, json=form
    )
    assert result.status_code == 200
    assert result.json()["pending_plan"] == "annual"
    assert len(accepted) == 1


def test_subscription_reads_use_db_and_mutations_replace_snapshot(integration_client, managed):
    provider, _state = managed
    headers = ready(integration_client)
    first = integration_client.get("/api/v1/billing/subscription", headers=headers)
    assert first.json()["plan"] == "monthly"
    reads = provider.v1.subscriptions.list_async.await_count
    for _ in range(3):
        assert (
            integration_client.get("/api/v1/billing/subscription", headers=headers).json()
            == first.json()
        )
    assert provider.v1.subscriptions.list_async.await_count == reads
    changed = change(integration_client, headers, "free")
    assert changed.status_code == 200
    provider.v1.subscriptions.list_async.reset_mock()
    snapshot = integration_client.get("/api/v1/billing/subscription", headers=headers).json()
    assert snapshot["pending_plan"] == "free"
    provider.v1.subscriptions.list_async.assert_not_called()


def test_webhook_syncs_without_email_and_ignores_obsolete_event_plan(
    integration_client, managed, monkeypatch
):
    import hashlib
    import hmac
    import json
    import time

    provider, state = managed
    headers = ready(integration_client)
    assert (
        integration_client.get("/api/v1/billing/subscription", headers=headers).json()["status"]
        == "active"
    )
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    state["subscription"].status = "past_due"
    payload = json.dumps(
        {
            "id": "evt_duplicate",
            "type": "customer.subscription.updated",
            "livemode": False,
            "data": {"object": {"customer": "cus_fixture", "status": "active"}},
        }
    ).encode()
    timestamp = str(int(time.time()))
    signature = hmac.new(
        b"whsec_fixture", timestamp.encode() + b"." + payload, hashlib.sha256
    ).hexdigest()
    webhook_headers = {"stripe-signature": f"t={timestamp},v1={signature}"}
    for _ in range(2):
        response = integration_client.post(
            "/api/v1/billing/webhook", content=payload, headers=webhook_headers
        )
        assert response.status_code == 200, response.text
    provider.v1.subscriptions.list_async.reset_mock()
    snapshot = integration_client.get("/api/v1/billing/subscription", headers=headers).json()
    assert snapshot["status"] == "past_due"
    assert not snapshot["can_manage"]
    provider.v1.subscriptions.list_async.assert_not_called()
    assert (
        integration_client.post(
            "/api/v1/billing/webhook", content=payload + b" ", headers=webhook_headers
        ).status_code
        == 400
    )


def test_server_reconciliation_repairs_missing_webhook(integration_client, managed):
    import asyncio

    from sqlalchemy import update

    from app.core.db.session import get_db
    from app.models.billing import BillingCustomer
    from app.services.billing_reconciliation import reconcile_subscriptions

    provider, _state = managed
    headers = ready(integration_client)
    assert (
        integration_client.get("/api/v1/billing/subscription", headers=headers).json()["plan"]
        == "monthly"
    )
    provider.v1.subscriptions.list_async.return_value = stripe_object(data=[], has_more=False)

    async def scenario():
        async with get_db() as db:
            await db.execute(update(BillingCustomer).values(subscription_synced_at=None))
            await db.commit()
        await reconcile_subscriptions()

    asyncio.run(scenario())
    provider.v1.subscriptions.list_async.reset_mock()
    assert (
        integration_client.get("/api/v1/billing/subscription", headers=headers).json()["plan"]
        == "free"
    )
    provider.v1.subscriptions.list_async.assert_not_called()


def signed_event(client, event):
    import hashlib
    import hmac
    import json
    import time

    payload = json.dumps(event).encode()
    stamp = str(int(time.time()))
    signature = hmac.new(
        b"whsec_fixture", stamp.encode() + b"." + payload, hashlib.sha256
    ).hexdigest()
    return client.post(
        "/api/v1/billing/webhook",
        content=payload,
        headers={"stripe-signature": f"t={stamp},v1={signature}"},
    )


def test_webhook_failure_keeps_snapshot_and_redelivery_repairs_it(
    integration_client, managed, monkeypatch
):
    """Scenario: provider outage returns retryable failure without overwriting confirmed state."""
    import stripe

    # Given: a stored active subscription and an incoming failure event.
    provider, state = managed
    headers = ready(integration_client)
    before = integration_client.get("/api/v1/billing/subscription", headers=headers).json()
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    event = {
        "id": "evt_retry",
        "type": "invoice.payment_failed",
        "livemode": False,
        "data": {"object": {"customer": "cus_fixture"}},
    }
    # When: the provider is unavailable, then recovers for the same event.
    provider.v1.subscriptions.list_async.side_effect = stripe.APIConnectionError("offline")
    assert signed_event(integration_client, event).status_code == 502
    assert integration_client.get("/api/v1/billing/subscription", headers=headers).json() == before
    provider.v1.subscriptions.list_async.side_effect = None
    state["subscription"].status = "past_due"
    assert signed_event(integration_client, event).status_code == 200
    # Then: redelivery persists the current provider state and disables management.
    after = integration_client.get("/api/v1/billing/subscription", headers=headers).json()
    assert after["status"] == "past_due" and not after["can_manage"]


def test_billing_mail_deduplicates_and_ignores_obsolete_plan_event(
    integration_client, managed, monkeypatch
):
    """Scenario: duplicate starts and plan events queue once; delayed obsolete changes queue nothing."""
    from sqlalchemy import select

    from app.core.db.session import get_db
    from app.models.notification import Notification

    # Given: real DB outbox and signed events, without broker or SMTP I/O.
    _provider, state = managed
    headers = ready(integration_client)
    integration_client.get("/api/v1/billing/subscription", headers=headers)
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    monkeypatch.setattr("app.services.notifications.wake_notifications", AsyncMock())
    event = {
        "id": "evt_start",
        "type": "invoice.paid",
        "livemode": False,
        "data": {
            "object": {
                "customer": "cus_fixture",
                "status": "paid",
                "billing_reason": "subscription_create",
                "lines": {"data": [{"pricing": {"price_details": {"price": "price_monthly_krw"}}}]},
                "parent": {"subscription_details": {"subscription": "sub_fixture"}},
            }
        },
    }
    for _ in range(2):
        assert signed_event(integration_client, event).status_code == 200
    # When: an applied annual change is repeated, then a stale monthly event arrives.
    state["subscription"]["items"].data[0].price.id = "price_annual_krw"
    event = {
        "id": "evt_change",
        "created": 1900000000,
        "type": "customer.subscription.updated",
        "livemode": False,
        "data": {
            "object": state["subscription"].to_dict(),
            "previous_attributes": {"items": {"data": [{"price": {"id": "price_monthly_krw"}}]}},
        },
    }
    for _ in range(2):
        assert signed_event(integration_client, event).status_code == 200
    event["id"] = "evt_old"
    event["created"] -= 60
    event["data"]["object"]["items"]["data"][0]["price"]["id"] = "price_monthly_krw"
    event["data"]["previous_attributes"]["items"]["data"][0]["price"]["id"] = "price_annual_krw"
    assert signed_event(integration_client, event).status_code == 200

    # Then: only one start and one applied change are durably reserved.
    async def kinds():
        async with get_db() as db:
            return list((await db.scalars(select(Notification.kind))).all())

    assert sorted(asyncio.run(kinds())) == ["plan_changed", "subscription_started"]
    assert (
        integration_client.get("/api/v1/billing/subscription", headers=headers).json()["plan"]
        == "annual"
    )


@pytest.mark.parametrize("legacy", [False, True])
def test_late_initial_invoice_does_not_announce_a_later_plan(
    integration_client, managed, monkeypatch, legacy
):
    """Scenario: a delayed initial invoice cannot label a later subscription plan as newly purchased."""
    from sqlalchemy import select

    from app.core.db.session import get_db
    from app.models.notification import Notification

    # Given: the customer has already changed from monthly to annual.
    _provider, state = managed
    ready(integration_client)
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    state["subscription"]["items"].data[0].price.id = "price_annual_krw"
    line = (
        {"price": {"id": "price_monthly_krw"}}
        if legacy
        else {"pricing": {"price_details": {"price": "price_monthly_krw"}}}
    )
    # When: the initial monthly paid invoice arrives late.
    result = signed_event(
        integration_client,
        {
            "id": "evt_late_initial",
            "type": "invoice.paid",
            "livemode": False,
            "data": {
                "object": {
                    "customer": "cus_fixture",
                    "status": "paid",
                    "billing_reason": "subscription_create",
                    "subscription": "sub_fixture",
                    "lines": {"data": [line]},
                }
            },
        },
    )
    assert result.status_code == 200

    # Then: no inaccurate start email is reserved (the Stripe receipt remains authoritative).
    async def inspect():
        async with get_db() as db:
            assert await db.scalar(select(Notification)) is None

    asyncio.run(inspect())


@pytest.mark.parametrize(
    "locales, expected", [(["ko-KR"], "ko"), (["fr", "en-US"], "en"), ([], "en")]
)
def test_same_second_plan_events_keep_distinct_identity_and_customer_locale(
    integration_client, managed, monkeypatch, locales, expected
):
    """Scenario: real changes in one second are distinct, redelivery is deduplicated, and locale is durable."""
    import json

    from sqlalchemy import select

    from app.core.db.session import get_db
    from app.models.notification import Notification
    from app.services.notifications import cipher

    # Given: provider preference survives independently of subscription/invoice metadata.
    provider, state = managed
    ready(integration_client)
    provider.v1.customers.retrieve_async.return_value.preferred_locales = locales
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    # When: three real price changes share an event timestamp, each delivered twice.
    old = "price_monthly_krw"
    for number, price in enumerate(["price_annual_krw", "price_monthly_krw", "price_annual_krw"]):
        state["subscription"]["items"].data[0].price.id = price
        event = {
            "id": f"evt_change_{number}",
            "created": 1900000000,
            "type": "customer.subscription.updated",
            "livemode": False,
            "data": {
                "object": state["subscription"].to_dict(),
                "previous_attributes": {"items": {"data": [{"price": {"id": old}}]}},
            },
        }
        for _ in range(2):
            assert signed_event(integration_client, event).status_code == 200
        old = price

    # Then: three legitimate notices survive and repeated events add none.
    async def inspect():
        async with get_db() as db:
            rows = list((await db.scalars(select(Notification))).all())
            assert len(rows) == 3
            assert all(
                json.loads(cipher().decrypt(row.payload.encode()))["language"] == expected
                for row in rows
            )

    asyncio.run(inspect())


@pytest.mark.parametrize("replacement", [False, True])
def test_cancellation_notice_requires_no_replacement_subscription(
    integration_client, managed, monkeypatch, replacement
):
    """Scenario: requested cancellation sends Free only if no newer subscription is active."""
    import json

    from sqlalchemy import select

    from app.core.db.session import get_db
    from app.models.notification import Notification
    from app.services.notifications import cipher

    # Given: a signed cancellation completion and an optional replacement subscription.
    provider, _state = managed
    ready(integration_client)
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    if not replacement:
        provider.v1.subscriptions.list_async.return_value = stripe_object(data=[], has_more=False)
    event = {
        "id": "evt_deleted",
        "type": "customer.subscription.deleted",
        "livemode": False,
        "data": {
            "object": {
                "id": "sub_old",
                "customer": "cus_fixture",
                "status": "canceled",
                "cancellation_details": {"reason": "cancellation_requested"},
            }
        },
    }
    # When: cancellation completion is redelivered.
    for _ in range(2):
        assert signed_event(integration_client, event).status_code == 200

    # Then: no replacement can be described as Free; otherwise one completion is queued.
    async def inspect():
        async with get_db() as db:
            rows = list((await db.scalars(select(Notification))).all())
            assert len(rows) == (0 if replacement else 1)
            if rows:
                assert json.loads(cipher().decrypt(rows[0].payload.encode()))["plan"] == "Free"

    asyncio.run(inspect())
