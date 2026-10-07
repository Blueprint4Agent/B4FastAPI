import asyncio

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from app.core.config.settings import SETTINGS, Settings
from app.core.db.session import get_db
from app.manage_user_role import change_role
from app.models.user import RoleChangeAudit, UserRole, Users
from app.services.bootstrap import BootstrapService
from app.utils.token import create_access_token
from tests.fixtures.payload_data import build_login_payload, build_signup_payload


def test_production_requires_login_and_known_mode():
    """Configuration cannot enable login-free production or accept a misspelled mode."""
    with pytest.raises(ValueError, match="requires LOGIN_ENABLED"):
        Settings(APP_MODE="production", LOGIN_ENABLED=False)
    with pytest.raises(ValidationError):
        Settings(APP_MODE="prod")
    assert Settings(APP_MODE="production", LOGIN_ENABLED=True).APP_MODE == "production"


@pytest.mark.primary_data
def test_bootstrap_never_promotes_existing_account(integration_client, monkeypatch):
    """A matching normal email must not become a password-free administrator."""
    email = "existing@example.com"
    integration_client.post("/api/v1/auth/signup", json=build_signup_payload(email=email))
    monkeypatch.setattr(SETTINGS, "APP_MODE", "development")
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "BOOTSTRAP_USER_EMAIL", email)
    with pytest.raises(ValueError, match="identity conflict"):
        asyncio.run(BootstrapService().initialize())
    user = asyncio.run(Users.get_user_response_by_email(email))
    assert user.role == UserRole.USER


@pytest.mark.primary_data
def test_bootstrap_is_dedicated_and_blocked_in_production(integration_client, monkeypatch):
    """Mode transition rejects old bootstrap sessions and application API keys."""
    monkeypatch.setattr(SETTINGS, "APP_MODE", "development")
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "BOOTSTRAP_USER_EMAIL", "dev-only@example.com")
    user = asyncio.run(BootstrapService().initialize())
    assert asyncio.run(BootstrapService().initialize()).id == user.id
    identity = asyncio.run(Users.get_auth_user_by_identity("bootstrap", user.email))
    assert identity.password_hash is None
    token = create_access_token(subject=str(user.id), email=user.email)
    headers = {"Authorization": f"Bearer {token}"}
    assert integration_client.get("/api/v1/auth/me", headers=headers).status_code == 200
    issued = integration_client.post(
        "/api/v1/api-keys", headers=headers, json={"name": "mode-test"}
    )
    assert issued.status_code == 200
    key_headers = {"X-API-Key": issued.json()["api_key"]}
    assert integration_client.get("/api/v1/auth/me", headers=key_headers).status_code == 200
    # Production public config cannot expose a development identity/token.
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "APP_MODE", "production")
    assert integration_client.get("/api/v1/auth/me", headers=headers).status_code == 403
    assert integration_client.get("/api/v1/auth/me", headers=key_headers).status_code == 403
    config = integration_client.get("/config").json()
    assert config["app_mode"] == "production"
    assert config["bootstrap_user"] is None
    assert config["bootstrap_access_token"] is None
    with pytest.raises(ValueError, match="requires development"):
        asyncio.run(BootstrapService().initialize())


@pytest.mark.primary_data
def test_manager_directory_audit_and_last_admin(integration_client):
    """Manager grant/revoke uses current DB roles; admin demotion stays protected."""
    for email in ("operator@example.com", "manager@example.com"):
        assert (
            integration_client.post(
                "/api/v1/auth/signup", json=build_signup_payload(email=email)
            ).status_code
            == 200
        )
    login = integration_client.post(
        "/api/v1/auth/login", json=build_login_payload(email="manager@example.com")
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    endpoint = "/api/v1/auth/admin/users"
    assert integration_client.get(endpoint, headers=headers).status_code == 403
    asyncio.run(change_role("operator@example.com", UserRole.ADMIN))
    with pytest.raises(ValueError, match="last active admin"):
        asyncio.run(change_role("operator@example.com", UserRole.MANAGER))
    asyncio.run(change_role("manager@example.com", UserRole.MANAGER))
    response = integration_client.get(endpoint, params={"role": "manager"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["summary"]["manager_users"] == 1
    # No role mutation endpoint is exposed to managers (or ordinary HTTP clients).
    assert (
        integration_client.patch(endpoint, headers=headers, json={"role": "admin"}).status_code
        == 405
    )
    asyncio.run(change_role("manager@example.com", UserRole.USER))
    assert integration_client.get(endpoint, headers=headers).status_code == 403

    async def audit():
        async with get_db() as db:
            return list(
                (await db.scalars(select(RoleChangeAudit).order_by(RoleChangeAudit.id))).all()
            )

    events = asyncio.run(audit())
    assert [(event.previous_role, event.new_role) for event in events] == [
        ("user", "admin"),
        ("user", "manager"),
        ("manager", "user"),
    ]
    assert all(event.operator.startswith("cli:") for event in events)


@pytest.mark.primary_data
def test_config_renews_bootstrap_token_after_time_passes(integration_client, monkeypatch):
    """Config recovery must mint a usable token instead of replaying an expired startup token."""
    import importlib
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    main = importlib.import_module("app.main")
    token_module = importlib.import_module("app.utils.token")
    monkeypatch.setattr(SETTINGS, "APP_MODE", "development")
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "BOOTSTRAP_USER_EMAIL", "renewal@example.com")
    user = asyncio.run(BootstrapService().initialize())
    monkeypatch.setattr(main, "BOOTSTRAP_USER", user)
    now = datetime.now(UTC)

    class EarlierClock:
        @staticmethod
        def now(tz):
            return now - timedelta(minutes=SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES + 1)

    monkeypatch.setattr(token_module, "datetime", EarlierClock)
    old = integration_client.get("/config").json()["bootstrap_access_token"]
    assert jwt.get_unverified_claims(old)["exp"] < now.timestamp()
    monkeypatch.setattr(token_module, "datetime", datetime)
    response = integration_client.get("/config")
    new = response.json()["bootstrap_access_token"]
    assert response.headers["cache-control"] == "no-store"
    assert new != old
    assert (
        integration_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {new}"}
        ).status_code
        == 200
    )
