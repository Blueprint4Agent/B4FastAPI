import asyncio
from unittest.mock import AsyncMock

import pytest

from app.core.config.settings import SETTINGS
from app.models.user import Users
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data


@pytest.fixture(autouse=True)
def isolated_cache(monkeypatch):
    monkeypatch.setattr(SETTINGS, "REDIS_IN_MEMORY", True)


def login(client, email="profile@example.com"):
    client.post("/api/v1/auth/signup", json=build_signup_payload(email=email))
    response = client.post("/api/v1/auth/login", json=build_login_payload(email=email))
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}, response.json()["user"][
        "id"
    ]


def test_profile_fields_are_private_bounded_and_patch_preserves_omissions(integration_client):
    """Scenario: own profile changes persist without exposing other accounts or private credentials."""
    client = integration_client
    # Given: two separate signed-in accounts.
    headers, _ = login(client)
    other, _ = login(client, "other@example.com")
    # When: optional fields are saved, a later name-only patch preserves them.
    response = client.patch(
        "/api/v1/auth/me", headers=headers, json={"bio": "  Hello\nworld  ", "location": "KR:11"}
    )
    assert response.status_code == 200
    assert response.json()["bio"] == "Hello\nworld"
    assert response.json()["location"] == "KR:11"
    assert response.json()["has_password"] is True
    assert "password_hash" not in response.json()
    assert "profile_photo" not in response.json()
    client.patch("/api/v1/auth/me", headers=headers, json={"name": "New Name"})
    assert client.get("/api/v1/auth/me", headers=headers).json()["bio"] == "Hello\nworld"
    # Then: another account sees only its own blank profile; invalid writes preserve saved data.
    assert client.get("/api/v1/auth/me", headers=other).json()["bio"] is None
    for body in ({"bio": "x" * 101}, {"location": "x" * 101}, {"location": "US:11"}):
        assert client.patch("/api/v1/auth/me", headers=headers, json=body).status_code == 422
    assert client.patch("/api/v1/auth/me", json={"bio": "anonymous"}).status_code == 401
    cleared = client.patch("/api/v1/auth/me", headers=headers, json={"bio": None, "location": "  "})
    assert cleared.json()["bio"] is None and cleared.json()["location"] is None


def test_password_change_requires_own_single_use_email_code(integration_client, monkeypatch):
    """Scenario: deletion/other-account codes cannot change passwords and a valid code works once."""
    client = integration_client
    headers, user_id = login(client)
    other, _ = login(client, "other@example.com")
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    sender = AsyncMock()
    monkeypatch.setattr("app.services.auth.MAIL_QUEUE_SERVICE.enqueue_password_change", sender)
    # Given: issuance only uses the authenticated account's registered address.
    assert client.post("/api/v1/auth/me/password/code", headers=headers).status_code == 200
    assert sender.call_args.kwargs["to_email"] == "profile@example.com"
    code = sender.call_args.kwargs["code"]
    assert client.post("/api/v1/auth/me/password/code", headers=headers).status_code == 429
    body = {"code": code, "password": "NewPassword123!"}
    # When: another user or a deletion challenge tries to authorize the change.
    assert client.post("/api/v1/auth/me/password", headers=other, json=body).status_code == 400
    deletion_sender = AsyncMock()
    monkeypatch.setattr(
        "app.services.auth.MAIL_QUEUE_SERVICE.enqueue_account_deletion", deletion_sender
    )
    assert client.post("/api/v1/auth/me/deletion-code", headers=headers).status_code == 200
    deletion = deletion_sender.call_args.kwargs["code"]
    assert (
        client.post(
            "/api/v1/auth/me/password", headers=headers, json={**body, "code": deletion}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/me/password", headers=headers, json={**body, "password": "weak"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/auth/me/password/code/verify", headers=other, json={"code": code}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/auth/me/password/code/verify", headers=headers, json={"code": code}
        ).status_code
        == 200
    )
    assert client.post("/api/v1/auth/me/password", headers=headers, json=body).status_code == 200
    assert client.post("/api/v1/auth/me/password", headers=headers, json=body).status_code == 400
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    assert (
        client.post(
            "/api/v1/auth/login", json=build_login_payload(email="profile@example.com")
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json=build_login_payload(email="profile@example.com", password=body["password"]),
        ).status_code
        == 200
    )


def test_email_disabled_blocks_all_email_proof_operations(integration_client):
    """Scenario: turning email off never creates an authentication bypass."""
    client = integration_client
    headers, _ = login(client)
    # Given/When: every proof-dependent endpoint is called with email disabled.
    operations = [
        ("POST", "/api/v1/auth/me/password/code", None),
        ("POST", "/api/v1/auth/me/password", {"code": "123456", "password": "NewPassword123!"}),
        ("POST", "/api/v1/auth/me/deletion-code", None),
        ("DELETE", "/api/v1/auth/me", {"email": "profile@example.com", "code": "123456"}),
        ("POST", "/api/v1/auth/forgot-password", {"email": "profile@example.com"}),
        ("POST", "/api/v1/auth/reset-password", {"token": "a" * 32, "password": "NewPassword123!"}),
    ]
    for method, path, body in operations:
        response = client.request(method, path, headers=headers, json=body)
        # Then: each request is rejected explicitly, while profile editing remains usable.
        assert response.json()["detail"]["error"] == "EMAIL_DISABLED"
    assert (
        client.patch("/api/v1/auth/me", headers=headers, json={"bio": "Still editable"}).status_code
        == 200
    )


def test_password_code_transport_rejects_anonymous_api_keys_and_mail_failure(
    integration_client, monkeypatch
):
    """Scenario: only bearer sessions can request proof and queue failures fail closed."""
    client = integration_client
    headers, user_id = login(client)
    key = client.post("/api/v1/api-keys", headers=headers, json={"name": "Profile test"})
    # Given: email is enabled but publication fails.
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(
        "app.services.auth.MAIL_QUEUE_SERVICE.enqueue_password_change",
        AsyncMock(side_effect=OSError("down")),
    )
    # When/Then: anonymous and key-only requests are unauthorized.
    assert client.post("/api/v1/auth/me/password/code").status_code == 401
    assert key.status_code == 200
    assert (
        client.post(
            "/api/v1/auth/me/password/code", headers={"X-API-Key": key.json()["api_key"]}
        ).status_code
        == 401
    )
    assert client.post("/api/v1/auth/me/password/code", headers=headers).status_code == 503
    assert asyncio.run(Users.get_auth_user_by_id(user_id)).password_hash
