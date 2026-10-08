"""Audit authentication mechanisms separately from feature and role authorization."""

import asyncio

import pytest

from app.models.user import UserRole, Users
from app.services.realtime import RealtimeService
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data

SESSION_ONLY = [
    ("POST", "/api/v1/auth/me/password/code/verify", {"code": "123456"}),
    ("POST", "/api/v1/auth/me/deletion-code/verify", {"code": "123456"}),
    ("POST", "/api/v1/auth/me/password/code", None),
    ("POST", "/api/v1/auth/me/password", {"code": "123456", "password": "NewPassword123!"}),
    ("POST", "/api/v1/auth/me/deletion-code", None),
    ("DELETE", "/api/v1/auth/me", {"email": "tester@example.com", "code": "123456"}),
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
    """Scenario: all session-only operations reject a real otherwise-valid API key."""
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
    template = template.replace("pm_fixture", "{method_id}").replace("seti_fixture", "{intent_id}")
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
    # Then: it exactly matches the explicit session policy exceptions.
    expected = {
        (method, path.replace("cs_test_fixture", "{session_id}"))
        for method, path, _ in SESSION_ONLY
    }
    assert actual == expected


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("GET", "/api/v1/billing/config", None),
        (
            "POST",
            "/api/v1/billing/setup-sessions",
            {"request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29"},
        ),
        ("GET", "/api/v1/billing/setup-sessions/cs_test_fixture", None),
        ("GET", "/api/v1/billing/payment-methods", None),
        ("GET", "/api/v1/billing/plans", None),
        ("GET", "/api/v1/billing/subscription", None),
        ("GET", "/api/v1/billing/profile", None),
        (
            "PUT",
            "/api/v1/billing/profile",
            {
                "request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29",
                "email": "invoice@example.com",
                "name": "Name",
                "address": {},
            },
        ),
        (
            "POST",
            "/api/v1/billing/payment-methods/pm_fixture",
            {"request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29", "action": "default"},
        ),
        (
            "POST",
            "/api/v1/billing/card-setups",
            {"request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29"},
        ),
        ("GET", "/api/v1/billing/card-setups/seti_fixture", None),
        ("GET", "/api/v1/billing/invoices", None),
        (
            "POST",
            "/api/v1/billing/portal-sessions",
            {"request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29"},
        ),
        (
            "POST",
            "/api/v1/billing/subscription/change",
            {
                "request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29",
                "plan": "free",
                "expected_version": "a" * 64,
            },
        ),
        ("GET", "/api/v1/billing/checkout-sessions/cs_test_fixture", None),
        (
            "POST",
            "/api/v1/billing/checkout-sessions",
            {
                "request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29",
                "plan": "monthly",
                "currency": "krw",
            },
        ),
    ],
)
def test_billing_api_key_guards(integration_client, credentials, method, path, body):
    """Scenario: billing accepts owner keys and rejects invalid, disabled and mixed credentials."""
    # Given: an issued owner key and a second authenticated user.
    client = integration_client
    bearer, key, _ = credentials
    assert (
        client.post(
            "/api/v1/auth/signup", json=build_signup_payload(email="other@example.com")
        ).status_code
        == 200
    )
    other = client.post("/api/v1/auth/login", json=build_login_payload(email="other@example.com"))
    other_bearer = {"Authorization": f"Bearer {other.json()['access_token']}"}
    # When/Then: invalid and conflicting credentials fail before Stripe I/O.
    for headers, status_code, error in [
        ({"X-API-Key": "invalid"}, 401, "API_KEY_INVALID"),
        ({**key, "Authorization": "Bearer invalid"}, 401, "INVALID_TOKEN"),
        ({**key, **other_bearer}, 403, "API_KEY_USER_MISMATCH"),
    ]:
        response = client.request(method, path, headers=headers, json=body)
        assert response.status_code == status_code
        assert response.json()["detail"]["error"] == error
    for headers in [key, {**key, **bearer}]:
        accepted = client.request(method, path, headers=headers, json=body)
        assert accepted.status_code in {200, 503}
    keys = client.get("/api/v1/api-keys", headers=bearer).json()
    key_id = keys["items"][0]["id"]
    assert (
        client.patch(
            f"/api/v1/api-keys/{key_id}/status", headers=bearer, json={"enabled": False}
        ).status_code
        == 200
    )
    rejected = client.request(method, path, headers=key, json=body)
    assert rejected.status_code == 401
    assert rejected.json()["detail"]["error"] == "API_KEY_INVALID"
    template = path.replace("cs_test_fixture", "{session_id}")
    template = template.replace("pm_fixture", "{method_id}").replace("seti_fixture", "{intent_id}")
    operation = client.app.openapi()["paths"][template][method.lower()]
    assert operation["security"] == [{"OAuth2PasswordBearer": []}, {"APIKeyHeader": []}]
    assert "403" in operation["responses"]
