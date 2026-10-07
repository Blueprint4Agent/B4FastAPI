"""Disabled features fail before persistence, token consumption or external I/O."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.core.config.settings import SETTINGS
from app.core.error import AuthException
from app.core.error.billing_exception import BillingException
from app.main import create_app
from app.models.oauth import OAuthProvider
from app.models.user import SignupForm
from app.services.auth import AuthService
from app.services.billing import BillingService


@pytest.mark.parametrize(
    "billing,subscriptions", [(False, False), (False, True), (True, False), (True, True)]
)
def test_public_config_effective_billing_flags(monkeypatch, billing, subscriptions):
    # Given: independently configured billing flags; no lifespan or provider is needed.
    monkeypatch.setattr(SETTINGS, "STRIPE_ENABLED", billing)
    monkeypatch.setattr(SETTINGS, "STRIPE_SUBSCRIPTIONS_ENABLED", subscriptions)
    # When: the public bootstrap configuration is requested.
    data = TestClient(create_app()).get("/config").json()
    # Then: subscriptions cannot be effective without billing.
    assert data["billing_enabled"] is billing
    assert data["subscriptions_enabled"] is (billing and subscriptions)


@pytest.mark.parametrize(
    "operation", ["signup", "refresh", "verify", "reset", "forgot", "resend", "oauth"]
)
def test_login_disabled_blocks_entry_operations(monkeypatch, operation):
    # Given: disabled login and repository/token/provider tripwires.
    import app.services.auth as auth

    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", False)
    forbidden = AsyncMock(side_effect=AssertionError("Disabled operation reached I/O"))
    monkeypatch.setattr(auth.Users, "create_signup_user", forbidden)
    monkeypatch.setattr(auth.Users, "get_auth_user_by_email", forbidden)
    monkeypatch.setattr(auth, "verify_refresh_token", forbidden)
    monkeypatch.setattr(auth, "consume_email_verification_token", forbidden)
    monkeypatch.setattr(auth, "consume_password_reset_token", forbidden)
    service = AuthService()
    monkeypatch.setattr(service, "consume_oauth_state", forbidden)
    operations = {
        "signup": lambda: service.signup(
            SignupForm(email="fixture@example.com", name="Fixture", password="Password123!")
        ),
        "refresh": lambda: service.refresh_access_token(1, "sid", "token"),
        "verify": lambda: service.verify_email("token"),
        "reset": lambda: service.reset_password("token", "Password123!"),
        "forgot": lambda: service.request_password_reset("fixture@example.com"),
        "resend": lambda: service.resend_verification_email("fixture@example.com"),
        "oauth": lambda: service.oauth_callback_login(
            OAuthProvider.GOOGLE, "code", "state", "https://example.com", Mock(), "sid"
        ),
    }
    # When/Then: all entry operations reject before side effects.
    with pytest.raises(AuthException) as error:
        asyncio.run(operations[operation]())
    assert error.value.code.error == "LOGIN_DISABLED"
    forbidden.assert_not_awaited()


def test_email_disabled_preserves_verification_token(monkeypatch):
    import app.services.auth as auth

    # Given: email is off but ordinary login remains available.
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    consume = AsyncMock()
    monkeypatch.setattr(auth, "consume_email_verification_token", consume)
    # When/Then: direct verification cannot consume a token or change a user.
    with pytest.raises(AuthException) as error:
        asyncio.run(AuthService().verify_email("token"))
    assert error.value.code.error == "EMAIL_DISABLED"
    consume.assert_not_awaited()


def test_oauth_disabled_preserves_state_and_skips_provider(monkeypatch):
    # Given: OAuth is off independently of password login.
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "OAUTH_ENABLED", False)
    service = AuthService()
    consume = AsyncMock()
    exchange = AsyncMock()
    monkeypatch.setattr(service, "consume_oauth_state", consume)
    monkeypatch.setattr(service, "_exchange_oauth_code", exchange)
    # When/Then: a previously issued callback cannot start a provider exchange.
    with pytest.raises(AuthException) as error:
        asyncio.run(
            service.oauth_callback_login(
                OAuthProvider.GOOGLE, "code", "state", "https://example.com", Mock(), "sid"
            )
        )
    assert error.value.code.error == "OAUTH_PROVIDER_NOT_ENABLED"
    consume.assert_not_awaited()
    exchange.assert_not_awaited()


@pytest.mark.parametrize("operation", ["subscription", "checkout_status"])
def test_subscriptions_disabled_skips_provider(monkeypatch, operation):
    # Given: payments may be enabled independently of subscriptions.
    monkeypatch.setattr(SETTINGS, "STRIPE_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_SUBSCRIPTIONS_ENABLED", False)
    service = BillingService()
    provider = Mock(side_effect=AssertionError("Provider must not be constructed"))
    monkeypatch.setattr(service, "_provider", provider)
    # When/Then: subscription reads and checkout returns reject without provider I/O.
    with pytest.raises(BillingException) as error:
        asyncio.run(
            service.subscription(1)
            if operation == "subscription"
            else service.checkout_status(1, "cs_fixture")
        )
    assert error.value.code.error == "BILLING_PLAN_UNAVAILABLE"
    provider.assert_not_called()
