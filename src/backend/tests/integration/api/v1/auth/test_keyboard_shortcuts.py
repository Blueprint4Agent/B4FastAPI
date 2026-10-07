import pytest

from tests.fixtures.payload_data import build_login_payload, build_signup_payload

BINDINGS = {"toggleSidebar": ["b"], "openSettings": ["mod", ","]}


@pytest.mark.primary_data
def test_keyboard_shortcuts_persist_per_account_and_reset(integration_client):
    """Scenario: shortcut writes survive login, isolate accounts and reset without changing name."""
    # Given: two independent accounts in the real database.
    headers = []
    for email in ("keys-a@example.com", "keys-b@example.com"):
        assert (
            integration_client.post(
                "/api/v1/auth/signup", json=build_signup_payload(email=email)
            ).status_code
            == 200
        )
        login = integration_client.post("/api/v1/auth/login", json=build_login_payload(email=email))
        assert login.status_code == 200
        headers.append({"Authorization": f"Bearer {login.json()['access_token']}"})
    # When: the first user saves custom keys.
    saved = integration_client.patch(
        "/api/v1/auth/me", headers=headers[0], json={"keyboard_shortcuts": BINDINGS}
    )
    # Then: both fresh profile reads and fresh logins reflect the DB, without leaking to user B.
    assert saved.status_code == 200
    assert saved.json()["keyboard_shortcuts"] == BINDINGS
    assert (
        integration_client.get("/api/v1/auth/me", headers=headers[0]).json()["keyboard_shortcuts"]
        == BINDINGS
    )
    assert (
        integration_client.get("/api/v1/auth/me", headers=headers[1]).json()["keyboard_shortcuts"]
        is None
    )
    login = integration_client.post(
        "/api/v1/auth/login", json=build_login_payload(email="keys-a@example.com")
    )
    assert login.status_code == 200
    assert login.json()["user"]["keyboard_shortcuts"] == BINDINGS
    renamed = integration_client.patch(
        "/api/v1/auth/me", headers=headers[0], json={"name": "New name"}
    )
    assert renamed.status_code == 200
    assert renamed.json()["keyboard_shortcuts"] == BINDINGS
    reset = integration_client.patch(
        "/api/v1/auth/me", headers=headers[0], json={"keyboard_shortcuts": None}
    )
    assert reset.status_code == 200
    assert reset.json()["keyboard_shortcuts"] is None
    assert reset.json()["name"] == "New name"
    assert (
        integration_client.get("/api/v1/auth/me", headers=headers[0]).json()["keyboard_shortcuts"]
        is None
    )


@pytest.mark.primary_data
@pytest.mark.parametrize(
    "keys",
    [
        {"toggleSidebar": [], "openSettings": ["b"]},
        {"toggleSidebar": ["shift"], "openSettings": ["b"]},
        {"toggleSidebar": ["b"], "openSettings": ["b"]},
        {"toggleSidebar": ["mod", "b"], "openSettings": ["ctrl", "b"]},
        {"toggleSidebar": ["mod", "ctrl", "b"], "openSettings": [","]},
        {"toggleSidebar": ["b"]},
        {"toggleSidebar": ["b"], "openSettings": [","], "other": ["x"]},
        {"toggleSidebar": ["x" * 33], "openSettings": [","]},
    ],
)
def test_keyboard_shortcuts_reject_invalid_payload(integration_client, keys):
    """Scenario: malformed or cross-platform conflicting bindings never reach the database."""
    # Given: a real authenticated account.
    integration_client.post("/api/v1/auth/signup", json=build_signup_payload())
    login = integration_client.post("/api/v1/auth/login", json=build_login_payload())
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    # When: submitting an invalid binding map.
    response = integration_client.patch(
        "/api/v1/auth/me", headers=headers, json={"keyboard_shortcuts": keys}
    )
    # Then: reject the request and retain defaults.
    assert response.status_code == 422
    assert response.json()["detail"]
    assert (
        integration_client.get("/api/v1/auth/me", headers=headers).json()["keyboard_shortcuts"]
        is None
    )


@pytest.mark.primary_data
def test_keyboard_shortcuts_require_authentication(integration_client):
    """Scenario: anonymous clients cannot persist shortcut settings."""
    # Given/When: no authentication headers on a shortcut update.
    response = integration_client.patch("/api/v1/auth/me", json={"keyboard_shortcuts": BINDINGS})
    # Then: the normal profile authentication boundary applies.
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"
