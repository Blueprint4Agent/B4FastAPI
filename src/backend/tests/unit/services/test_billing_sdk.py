"""Exercise the installed SDK's actual services/serialization with an in-memory transport."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlsplit

import stripe

from app.core.config.settings import SETTINGS
from app.models.billing import BillingCustomers, BillingSetupForm
from app.services.billing import BillingService
from tests.fixtures.billing_data import SETUP_REQUEST


def test_actual_sdk_setup_status_and_customer_method_protocol(monkeypatch):
    """Scenario: real SDK services serialize setup, expansion and customer-scoped lists correctly."""
    # Given: real StripeClient services with only the HTTP transport replaced.
    for key, value in {
        "STRIPE_ENABLED": True,
        "STRIPE_SECRET_KEY": "sk_test_fixture",
        "STRIPE_SETUP_SUCCESS_URL": "http://localhost:5173/settings?setup={CHECKOUT_SESSION_ID}",
        "STRIPE_SETUP_CANCEL_URL": "http://localhost:5173/settings",
    }.items():
        monkeypatch.setattr(SETTINGS, key, value)
    row = SimpleNamespace(stripe_customer_id="cus_fixture", livemode=False)
    monkeypatch.setattr(BillingCustomers, "get", AsyncMock(return_value=row))
    monkeypatch.setattr(BillingCustomers, "reserve", AsyncMock(return_value=row))
    requests = []

    async def transport(self, method, url, headers, post_data=None, **kwargs):
        requests.append((method, url, headers, post_data))
        path = urlsplit(url).path
        if path == "/v1/checkout/sessions":
            result = {
                "object": "checkout.session",
                "id": "cs_test_fixture",
                "url": "https://checkout.stripe.com/x",
            }
        elif path == "/v1/checkout/sessions/cs_test_fixture":
            result = {
                "object": "checkout.session",
                "id": "cs_test_fixture",
                "customer": "cus_fixture",
                "client_reference_id": "1",
                "livemode": False,
                "mode": "setup",
                "status": "complete",
                "setup_intent": {
                    "object": "setup_intent",
                    "id": "seti_fixture",
                    "customer": "cus_fixture",
                    "status": "succeeded",
                    "payment_method": "pm_fixture",
                },
            }
        elif path == "/v1/customers/cus_fixture/payment_methods":
            result = {
                "object": "list",
                "url": path,
                "has_more": False,
                "data": [
                    {
                        "object": "payment_method",
                        "id": "pm_fixture",
                        "type": "card",
                        "card": {
                            "brand": "visa",
                            "last4": "4242",
                            "exp_month": 12,
                            "exp_year": 2030,
                        },
                    }
                ],
            }
        else:
            raise AssertionError(f"Unexpected SDK route: {path}")
        return json.dumps(result).encode(), 200, {"request-id": "req_fixture"}

    monkeypatch.setattr(stripe.HTTPXClient, "request_async", transport)

    async def exercise():
        # When: all registration operations use the actual installed Stripe SDK.
        service = BillingService()
        setup = await service.create_setup(1, BillingSetupForm(**SETUP_REQUEST))
        status = await service.setup_status(1, setup.id)
        methods = await service.list_payment_methods(1, "card", 20, "pm_previous")
        # Then: SDK objects map to the public response correctly.
        assert status.registered is True
        assert methods.items[0].last4 == "4242"

    asyncio.run(exercise())
    # Then: HTTP parameters preserve ownership, idempotency, setup mode and pagination.
    assert len(requests) == 3
    assert parse_qs(requests[0][3])["mode"] == ["setup"]
    assert parse_qs(requests[0][3])["payment_method_types[1]"] == ["link"]
    assert requests[0][2]["Idempotency-Key"].endswith(SETUP_REQUEST["request_id"])
    assert parse_qs(urlsplit(requests[1][1]).query)["expand[0]"] == ["setup_intent"]
    assert parse_qs(urlsplit(requests[2][1]).query) == {
        "type": ["card"],
        "limit": ["20"],
        "starting_after": ["pm_previous"],
    }
