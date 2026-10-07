"""Native forms preserve owner boundaries and never accept raw card data."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.config.settings import SETTINGS
from tests.fixtures.billing_data import SETUP_REQUEST, stripe_object
from tests.integration.api.v1.billing.test_billing_integration import login
from tests.integration.api.v1.billing.test_plan_management import (
    managed as managed_fixture,
    provider_fixture,
)

pytestmark = pytest.mark.primary_data


@pytest.fixture
def native(monkeypatch):
    provider = provider_fixture.__wrapped__(monkeypatch)
    managed = managed_fixture.__wrapped__(provider, monkeypatch)
    monkeypatch.setattr(SETTINGS, "STRIPE_PUBLISHABLE_KEY", "pk_test_fixture")
    customer = provider.v1.customers.retrieve_async.return_value

    async def update_customer(customer_id, params, options):
        assert customer_id == "cus_fixture"
        for key, value in params.items():
            setattr(customer, key, stripe_object(**value) if isinstance(value, dict) else value)
        return customer

    provider.v1.customers.update_async = AsyncMock(side_effect=update_customer)
    method = stripe_object(id="pm_fixture", type="card", customer="cus_fixture", livemode=False)
    provider.v1.payment_methods = SimpleNamespace(
        retrieve_async=AsyncMock(return_value=method), detach_async=AsyncMock()
    )
    provider.v1.setup_intents = SimpleNamespace(
        create_async=AsyncMock(
            return_value=stripe_object(id="seti_fixture", client_secret="seti_fixture_secret_test")
        ),
        retrieve_async=AsyncMock(
            return_value=stripe_object(
                id="seti_fixture",
                customer="cus_fixture",
                livemode=False,
                status="succeeded",
                payment_method="pm_fixture",
            )
        ),
    )
    provider.v1.subscriptions.update_async = AsyncMock(return_value=managed[1]["subscription"])
    return provider


def mapped(client):
    headers = login(client)
    assert (
        client.post(
            "/api/v1/billing/setup-sessions", headers=headers, json=SETUP_REQUEST
        ).status_code
        == 201
    )
    return headers


def test_profile_edit_returns_structured_address_and_rejects_owner_override(
    integration_client, native
):
    client = integration_client
    headers = mapped(client)
    form = {
        **SETUP_REQUEST,
        "email": "invoice@example.com",
        "name": "Billing Name",
        "address": {
            "country": "KR",
            "city": "Seoul",
            "line1": "Street",
            "line2": "Unit",
            "postal_code": "06943",
        },
    }
    response = client.put("/api/v1/billing/profile", headers=headers, json=form)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["email"] == "invoice@example.com"
    assert response.json()["address_fields"]["line2"] == "Unit"
    assert (
        client.put(
            "/api/v1/billing/profile", headers=headers, json={**form, "customer": "cus_other"}
        ).status_code
        == 422
    )
    assert (
        client.put(
            "/api/v1/billing/profile", headers=headers, json={**form, "email": "invalid"}
        ).status_code
        == 422
    )


def test_default_and_remove_enforce_ownership_and_active_default(integration_client, native):
    client = integration_client
    headers = mapped(client)
    form = {**SETUP_REQUEST, "action": "remove"}
    response = client.post("/api/v1/billing/payment-methods/pm_fixture", headers=headers, json=form)
    assert response.status_code == 409
    native.v1.payment_methods.detach_async.assert_not_called()
    response = client.post(
        "/api/v1/billing/payment-methods/pm_fixture",
        headers=headers,
        json={**form, "action": "default"},
    )
    assert response.status_code == 200, response.text
    assert native.v1.subscriptions.update_async.call_args.kwargs["params"] == {
        "default_payment_method": "pm_fixture"
    }
    native.v1.payment_methods.retrieve_async.return_value.customer = "cus_other"
    assert (
        client.post(
            "/api/v1/billing/payment-methods/pm_fixture", headers=headers, json=form
        ).status_code
        == 404
    )
    native.v1.payment_methods.retrieve_async.return_value.customer = "cus_fixture"
    native.v1.subscriptions.list_async.return_value = stripe_object(data=[], has_more=False)
    assert (
        client.post(
            "/api/v1/billing/payment-methods/pm_fixture", headers=headers, json=form
        ).status_code
        == 200
    )
    native.v1.payment_methods.detach_async.assert_awaited_once()


@pytest.mark.parametrize("auth_mode", ["bearer", "api_key"])
def test_card_setup_owner_mode_and_server_confirmation(integration_client, native, auth_mode):
    client = integration_client
    headers = mapped(client)
    if auth_mode == "api_key":
        key = client.post(
            "/api/v1/api-keys", headers=headers, json={"name": "native billing"}
        ).json()["api_key"]
        headers = {"X-API-Key": key}
    response = client.post("/api/v1/billing/card-setups", headers=headers, json=SETUP_REQUEST)
    assert response.status_code == 201, response.text
    assert response.headers["cache-control"] == "no-store"
    assert native.v1.setup_intents.create_async.call_args.kwargs["params"][
        "payment_method_types"
    ] == ["card"]
    assert (
        client.get("/api/v1/billing/card-setups/seti_fixture", headers=headers).json()["registered"]
        is True
    )
    native.v1.setup_intents.retrieve_async.return_value.status = "requires_action"
    assert (
        client.get("/api/v1/billing/card-setups/seti_fixture", headers=headers).json()["registered"]
        is False
    )
    native.v1.setup_intents.retrieve_async.return_value.customer = "cus_other"
    assert (
        client.get("/api/v1/billing/card-setups/seti_fixture", headers=headers).status_code == 404
    )
    assert (
        client.post(
            "/api/v1/billing/card-setups",
            headers=headers,
            json={**SETUP_REQUEST, "card_number": "4242424242424242"},
        ).status_code
        == 422
    )


def test_optional_public_key_and_mode_validation(monkeypatch):
    from app.services.billing import BillingService

    monkeypatch.setattr(SETTINGS, "STRIPE_PUBLISHABLE_KEY", "")
    assert BillingService().config().publishable_key is None
    monkeypatch.setattr(SETTINGS, "STRIPE_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_SECRET_KEY", "sk_test_fixture")
    monkeypatch.setattr(SETTINGS, "STRIPE_PUBLISHABLE_KEY", "pk_live_wrongmode")
    assert not BillingService().config().enabled


def test_invoice_history_paging_and_detail_are_customer_scoped(integration_client, native):
    headers = mapped(integration_client)
    invoice = stripe_object(
        id="in_detail",
        customer="cus_fixture",
        livemode=False,
        number="INV-2",
        created=1,
        status="paid",
        currency="krw",
        subtotal=3990,
        total=3990,
        amount_paid=3990,
        amount_due=0,
        hosted_invoice_url="https://invoice.stripe.com/i/example",
        invoice_pdf=None,
        lines={"data": [{"description": "Plus", "amount": 3990, "quantity": 1}], "has_more": False},
    )
    native.v1.invoices.retrieve_async = AsyncMock(return_value=invoice)
    response = integration_client.get("/api/v1/billing/invoices/in_detail", headers=headers)
    assert response.status_code == 200
    assert response.json()["lines"][0]["description"] == "Plus"
    response = integration_client.get(
        "/api/v1/billing/invoices?limit=20&starting_after=in_detail", headers=headers
    )
    assert response.status_code == 200
    assert native.v1.invoices.list_async.call_args.kwargs["params"]["customer"] == "cus_fixture"
    invoice.customer = "cus_other"
    assert (
        integration_client.get("/api/v1/billing/invoices/in_detail", headers=headers).status_code
        == 404
    )
    assert (
        integration_client.get(
            "/api/v1/billing/invoices?starting_after=in_detail", headers=headers
        ).status_code
        == 404
    )
