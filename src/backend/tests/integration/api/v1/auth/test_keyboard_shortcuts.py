import pytest

from tests.fixtures.payload_data import build_login_payload, build_signup_payload

BINDINGS = {
    "toggleSidebar": ["b"],
    "openSettings": ["mod", ","],
    "openProfile": ["mod", "shift", "p"],
}


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


def test_legacy_keyboard_binding_model_remains_accepted():
    from app.models.user import KeyboardShortcuts

    legacy = KeyboardShortcuts.model_validate(
        {"toggleSidebar": ["b"], "openSettings": ["mod", "shift", "p"]}
    )
    assert legacy.openProfile is None


@pytest.mark.primary_data
def test_invalid_keyboard_update_preserves_confirmed_bindings(integration_client):
    """A rejected schema update never overwrites the previously persisted bindings."""
    integration_client.post("/api/v1/auth/signup", json=build_signup_payload())
    login = integration_client.post("/api/v1/auth/login", json=build_login_payload())
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (
        integration_client.patch(
            "/api/v1/auth/me", headers=headers, json={"keyboard_shortcuts": BINDINGS}
        ).status_code
        == 200
    )
    rejected = integration_client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"keyboard_shortcuts": {"toggleSidebar": [], "openSettings": ["b"]}},
    )
    assert rejected.status_code == 422
    assert (
        integration_client.get("/api/v1/auth/me", headers=headers).json()["keyboard_shortcuts"]
        == BINDINGS
    )
