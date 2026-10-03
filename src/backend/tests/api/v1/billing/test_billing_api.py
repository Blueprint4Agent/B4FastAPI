from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_user
from app.main import register_exception_handlers
from app.models.billing import BillingConfigResponse, BillingSetupResponse
from app.routers.v1.billing import router
from app.services.billing import BillingService
from tests.fixtures.billing_data import SETUP_REQUEST

pytestmark = pytest.mark.api_test


@pytest.fixture
def billing_app():
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/billing")
    return app


def test_setup_success_passes_session_owner(billing_app, sample_user):
    """Scenario: the route uses the authenticated owner and disables response caching."""
    # Given: a fake domain service and an authenticated principal.
    service = BillingService()
    service.create_setup = AsyncMock(
        return_value=BillingSetupResponse(id="cs_test_fixture", url="https://checkout.stripe.com/x")
    )
    billing_app.dependency_overrides[get_current_user] = lambda: sample_user
    billing_app.dependency_overrides[BillingService] = lambda: service
    # When: a valid setup request is posted.
    response = TestClient(billing_app).post("/api/v1/billing/setup-sessions", json=SETUP_REQUEST)
    # Then: a hosted URL is returned and no caller-selected user is used.
    assert response.status_code == 201
    assert response.headers["cache-control"] == "no-store"
    assert service.create_setup.call_args.args[0] == sample_user.id


@pytest.mark.parametrize("path", ["config", "payment-methods", "setup-sessions/cs_test_fixture"])
def test_billing_requires_authentication(billing_app, path):
    """Scenario: billing reads reject anonymous requests."""
    # Given/When: no bearer principal is supplied.
    response = TestClient(billing_app).get(f"/api/v1/billing/{path}", headers={})
    # Then: normal domain authentication failure is returned.
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"


def test_setup_mutation_requires_authentication(billing_app):
    """Scenario: unauthenticated requests cannot create Stripe resources."""
    # Given/When: setup creation is requested without a session.
    response = TestClient(billing_app).post("/api/v1/billing/setup-sessions", json=SETUP_REQUEST)
    # Then: authentication fails before service invocation.
    assert response.status_code == 401


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"request_id": "bad"},
        {**SETUP_REQUEST, "customer": "cus_other"},
        {**SETUP_REQUEST, "success_url": "https://evil.example"},
    ],
)
def test_setup_rejects_untrusted_request_fields(billing_app, sample_user, body):
    """Scenario: invalid UUIDs and caller-selected customer/return URLs are rejected."""
    # Given: a session principal.
    billing_app.dependency_overrides[get_current_user] = lambda: sample_user
    # When: malformed or additional fields are supplied.
    response = TestClient(billing_app).post("/api/v1/billing/setup-sessions", json=body)
    # Then: validation rejects the request.
    assert response.status_code == 422


@pytest.mark.parametrize(
    "path",
    [
        "payment-methods?limit=101",
        "payment-methods?method_type=bank",
        "payment-methods?starting_after=bad",
        "setup-sessions/not-a-session",
    ],
)
def test_billing_read_validation(billing_app, sample_user, path):
    """Scenario: invalid page parameters and session identifiers cannot reach Stripe."""
    # Given: a session principal.
    billing_app.dependency_overrides[get_current_user] = lambda: sample_user
    # When/Then: malformed paths/queries fail validation.
    assert TestClient(billing_app).get(f"/api/v1/billing/{path}").status_code == 422


def test_config_never_exposes_secrets(billing_app, sample_user):
    """Scenario: configuration contains only enablement and Stripe mode flags."""
    # Given: a configured service stub.
    service = BillingService()
    service.config = lambda: BillingConfigResponse(enabled=True, livemode=False)
    billing_app.dependency_overrides[get_current_user] = lambda: sample_user
    billing_app.dependency_overrides[BillingService] = lambda: service
    # When/Then: configuration contains no key, customer or redirect information.
    response = TestClient(billing_app).get("/api/v1/billing/config")
    assert response.json() == {"enabled": True, "livemode": False}


@pytest.mark.parametrize(
    "body",
    [
        {**SETUP_REQUEST, "plan": "free", "currency": "krw"},
        {**SETUP_REQUEST, "plan": "monthly", "currency": "eur"},
        {**SETUP_REQUEST, "plan": "monthly", "currency": "krw", "price": "price_untrusted"},
        {**SETUP_REQUEST, "plan": "monthly", "currency": "krw", "amount": 1},
    ],
)
def test_checkout_rejects_untrusted_pricing(billing_app, sample_user, body):
    # Given/When: a caller tries to override the server-owned catalog.
    billing_app.dependency_overrides[get_current_user] = lambda: sample_user
    response = TestClient(billing_app).post("/api/v1/billing/checkout-sessions", json=body)
    # Then: no provider call is made.
    assert response.status_code == 422
