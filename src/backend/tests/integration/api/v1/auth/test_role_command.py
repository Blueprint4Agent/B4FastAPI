import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.core.config.settings import SETTINGS
from app.core.db.session import get_db
from app.manage_user_role import change_role, main
from app.models.user import User, UserRole
from tests.fixtures.payload_data import build_login_payload, build_signup_payload


@pytest.mark.primary_data
def test_role_change_updates_authorization_and_protects_last_admin(integration_client):
    """Scenario: operator grants/revokes rights while the last active admin is protected."""
    # Given: two signed-up users and an existing bearer token.
    for email in ("first@example.com", "second@example.com"):
        assert (
            integration_client.post(
                "/api/v1/auth/signup", json=build_signup_payload(email=email)
            ).status_code
            == 200
        )
    login = integration_client.post(
        "/api/v1/auth/login", json=build_login_payload(email="first@example.com")
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    endpoint = "/api/v1/auth/admin/user-role-stats"
    assert integration_client.get(endpoint, headers=headers).status_code == 403
    # When: the operator promotes the user; the original token gains admin access.
    result = asyncio.run(change_role(" First@Example.com ", UserRole.ADMIN))
    assert result[1:] == ("user", "admin")
    assert integration_client.get(endpoint, headers=headers).status_code == 200
    assert asyncio.run(change_role("first@example.com", UserRole.ADMIN))[1:] == ("admin", "admin")
    with pytest.raises(ValueError, match="last active admin"):
        asyncio.run(change_role("first@example.com", UserRole.USER))
    # Then: another admin allows revocation, effective even with the original token.
    asyncio.run(change_role("second@example.com", UserRole.ADMIN))
    asyncio.run(change_role("first@example.com", UserRole.USER))
    assert integration_client.get(endpoint, headers=headers).status_code == 403


@pytest.mark.primary_data
def test_role_change_rejects_missing_and_inactive_accounts(integration_client):
    """Scenario: role management never creates users or changes inactive accounts."""
    # Given: a missing account and an inactive account.
    with pytest.raises(ValueError, match="Active user not found"):
        asyncio.run(change_role("missing@example.com", UserRole.ADMIN))
    integration_client.post(
        "/api/v1/auth/signup", json=build_signup_payload(email="inactive@example.com")
    )

    async def deactivate():
        async with get_db() as db:
            user = await db.scalar(select(User).where(User.email == "inactive@example.com"))
            user.is_active = False
            await db.commit()

    asyncio.run(deactivate())
    # When/Then: inactive accounts are rejected too.
    with pytest.raises(ValueError, match="Active user not found"):
        asyncio.run(change_role("inactive@example.com", UserRole.ADMIN))


def test_role_change_rejects_disabled_login(monkeypatch):
    """Scenario: bootstrap mode does not accept ordinary role changes."""
    # Given/When/Then: disabled login is rejected before database access.
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", False)
    with pytest.raises(ValueError, match="LOGIN_ENABLED=true"):
        asyncio.run(change_role("demo@example.com", UserRole.USER))


@pytest.mark.parametrize("role", ["owner", "", "ADMIN"])
def test_command_rejects_invalid_roles(monkeypatch, role):
    """Scenario: invalid environment arguments fail before connecting to the database."""
    # Given/When/Then: Make-style environment arguments must use a known role.
    monkeypatch.setenv("EMAIL", "operator@example.com")
    monkeypatch.setenv("ROLE", role)
    monkeypatch.setattr("sys.argv", ["manage_user_role"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2


@pytest.mark.primary_data
@pytest.mark.parametrize("role", ["admin", "manager"])
def test_role_module_runs_in_fresh_process(integration_client, role):
    """A real CLI process must register related models without server imports."""
    # Given: an existing account in the isolated migrated SQLite database.
    email = "standalone@example.com"
    assert (
        integration_client.post(
            "/api/v1/auth/signup", json=build_signup_payload(email=email)
        ).status_code
        == 200
    )
    env = {
        **os.environ,
        "DB_DRIVER": "sqlite+aiosqlite",
        "DB_NAME": make_url(SETTINGS.DATABASE_URL).database,
        "APP_MODE": "development",
        "LOGIN_ENABLED": "true",
        "EMAIL_ENABLED": "false",
        "OAUTH_ENABLED": "false",
        "TRACING_ENABLED": "false",
        "LOGS_ENABLED": "false",
        "EMAIL": email,
        "ROLE": role,
    }
    backend = Path(__file__).resolve().parents[5]
    # When: invoking the same standalone module used by Make, without app.main imports.
    result = subprocess.run(
        [sys.executable, "-m", "app.manage_user_role"],
        cwd=backend,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    # Then: role and audit persist, and the real command retains last-admin protection.
    assert result.returncode == 0, result.stderr
    assert f"user -> {role}" in result.stdout
    import sqlite3

    with sqlite3.connect(env["DB_NAME"]) as db:
        assert db.execute("SELECT role FROM users WHERE email=?", (email,)).fetchone() == (role,)
        assert db.execute("SELECT previous_role,new_role FROM role_change_audit").fetchall() == [
            ("user", role)
        ]
    if role == "admin":
        env["ROLE"] = "manager"
        denied = subprocess.run(
            [sys.executable, "-m", "app.manage_user_role"],
            cwd=backend,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert denied.returncode == 1
        assert "last active admin" in denied.stderr
