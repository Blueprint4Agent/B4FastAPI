"""Audit authentication mechanisms separately from feature and role authorization."""

import asyncio

import pytest

from app.models.user import UserRole, Users
from app.services.realtime import RealtimeService
from tests.fixtures.billing_data import SETUP_REQUEST
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data

SESSION_ONLY = [
    ("POST", "/api/v1/auth/me/deletion-code", None),
    ("DELETE", "/api/v1/auth/me", {"email": "tester@example.com", "code": "123456"}),
    ("GET", "/api/v1/billing/config", None),
    ("POST", "/api/v1/billing/setup-sessions", SETUP_REQUEST),
    ("GET", "/api/v1/billing/setup-sessions/cs_test_fixture", None),
    ("GET", "/api/v1/billing/payment-methods", None),
]
ADMIN_PATHS = ["/api/v1/auth/admin/users", "/api/v1/auth/admin/user-role-stats"]


@pytest.fixture
def credentials(integration_client):
    client = integration_client
    assert client.post("/api/v1/auth/signup", json=build_signup_payload()).status_code == 200
    result = client.post("/api/v1/auth/login", json=build_login_payload())
    assert result.status_code == 200
    bearer = {"Authorization": f"Bearer {result.json()['access_token']}"}
    key = client.post("/api/v1/api-keys", json={"name": "policy-audit"}, headers=bearer)
    assert key.status_code == 200
    return bearer, {"X-API-Key": key.json()["api_key"]}, result.json()["user"]["id"]


@pytest.mark.parametrize("method,path,body", SESSION_ONLY)
def test_issued_api_key_cannot_substitute_for_session(
    integration_client, credentials, method, path, body
):
    """Scenario: all six session-only operations reject a real otherwise-valid API key."""
    # Given: a genuine key that authenticates the general user endpoint.
    bearer, key, _ = credentials
    assert integration_client.get("/api/v1/auth/me", headers=key).status_code == 200
    # When: the key is used on a session-only route.
    rejected = integration_client.request(method, path, json=body, headers=key)
    # Then: the key is rejected for authentication, while bearer gets past that guard.
    assert rejected.status_code == 401
    assert rejected.json()["detail"]["error"] == "INVALID_TOKEN"
    accepted = integration_client.request(method, path, json=body, headers=bearer)
    assert accepted.status_code in {200, 400, 403, 404, 503}
    if accepted.status_code != 200:
        assert accepted.json()["detail"]["error"] not in {"INVALID_TOKEN", "API_KEY_INVALID"}
    template = path.replace("cs_test_fixture", "{session_id}")
    assert integration_client.app.openapi()["paths"][template][method.lower()]["security"] == [
        {"OAuth2PasswordBearer": []}
    ]


@pytest.mark.parametrize("path", ADMIN_PATHS)
def test_admin_routes_accept_keys_but_enforce_owner_role(integration_client, credentials, path):
    """Scenario: the same key gets 403 for a user and succeeds after its owner becomes admin."""
    # Given: a valid API key owned by a regular user.
    _, key, user_id = credentials
    response = integration_client.get(path, headers=key)
    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "INSUFFICIENT_ROLE"
    # When: the database role changes without reissuing the key.
    asyncio.run(Users.update_user_role(user_id=user_id, role=UserRole.ADMIN))
    # Then: role is read from the current owner, not embedded in the key.
    assert integration_client.get(path, headers=key).status_code == 200
    assert {"APIKeyHeader": []} in integration_client.app.openapi()["paths"][path]["get"][
        "security"
    ]


def test_general_routes_accept_api_key_and_mixed_invalid_bearer_is_rejected(
    integration_client, credentials
):
    """Scenario: a key supports profile, key management, events and logout but cannot bypass bad bearer."""
    # Given: a real key; only the infinite SSE source is replaced with a finite stream.
    _, key, _ = credentials

    class FiniteEvents:
        def stream_user_events(self, **kwargs):
            async def stream():
                yield "event: connected\ndata: {}\n\n"

            return stream()

    integration_client.app.dependency_overrides[RealtimeService] = FiniteEvents
    # When/Then: the ordinary operations accept API-key authentication.
    client = integration_client
    assert client.get("/api/v1/auth/me", headers=key).status_code == 200
    assert (
        client.patch("/api/v1/auth/me", headers=key, json={"name": "Audit User"}).status_code == 200
    )
    assert client.get("/api/v1/api-keys", headers=key).status_code == 200
    created = client.post("/api/v1/api-keys", headers=key, json={"name": "second-audit"})
    assert created.status_code == 200
    key_id = created.json()["key"]["id"]
    assert (
        client.patch(
            f"/api/v1/api-keys/{key_id}/status", headers=key, json={"enabled": False}
        ).status_code
        == 200
    )
    assert client.delete(f"/api/v1/api-keys/{key_id}", headers=key).status_code == 200
    assert client.get("/api/v1/events/stream", headers=key).status_code == 200
    rejected = client.get("/api/v1/auth/me", headers={**key, "Authorization": "Bearer invalid"})
    assert rejected.status_code == 401
    assert client.post("/api/v1/auth/logout", headers=key).status_code == 200


def test_openapi_session_only_inventory_is_explicit(integration_client):
    """Scenario: all session-only paths are audited so new undocumented exceptions cannot hide."""
    # Given: the runtime OpenAPI used by Swagger.
    schema = integration_client.app.openapi()
    # When: only-bearer operations are collected.
    actual = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
        if isinstance(operation, dict)
        and operation.get("security") == [{"OAuth2PasswordBearer": []}]
    }
    # Then: it exactly matches the six known policy exceptions.
    expected = {
        (method, path.replace("cs_test_fixture", "{session_id}"))
        for method, path, _ in SESSION_ONLY
    }
    assert actual == expected
