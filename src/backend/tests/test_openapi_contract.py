"""Regression checks for the public contract used by alternative backends."""

import json
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.error import AuthErrorCode, AuthException
from app.core.observability.health import ReadinessResponse
from app.core.realtime.contracts import RealtimeStreamEvent
from app.core.realtime.events import build_realtime_event, encode_sse_event
from app.deps import get_current_user
from app.main import create_app
from app.services.auth import AuthService

pytestmark = pytest.mark.api_test


@pytest.fixture
def contract_app():
    return create_app()


def test_openapi_references_resolve_and_generation_is_cached(contract_app):
    """Scenario: all shared event/error references resolve in the exported contract."""
    schema = contract_app.openapi()

    def visit(value):
        if isinstance(value, dict):
            reference = value.get("$ref")
            if reference and reference.startswith("#/"):
                target = schema
                for part in reference[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(schema)
    assert contract_app.openapi() == schema


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("GET", "/api/v1/auth/me", None),
        ("PATCH", "/api/v1/auth/me", {"name": "Tester"}),
        ("POST", "/api/v1/auth/logout", None),
        ("GET", "/api/v1/auth/admin/user-role-stats", None),
        ("GET", "/api/v1/api-keys", None),
        ("POST", "/api/v1/api-keys", {"name": "test"}),
        ("DELETE", "/api/v1/api-keys/1", None),
        ("PATCH", "/api/v1/api-keys/1/status", {"enabled": False}),
        ("GET", "/api/v1/events/stream", None),
    ],
)
def test_protected_routes_document_actual_auth_failures(contract_app, method, path, body):
    """Scenario: every protected endpoint exposes auth and API-key error alternatives."""
    # Given: the full router chain with no credentials, without starting infrastructure.
    client = TestClient(contract_app)
    # When: a protected route is requested.
    response = client.request(method, path, json=body)
    # Then: the actual failure and both authentication schemes are documented.
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"
    schema_path = path.replace("/api-keys/1", "/api-keys/{api_key_id}")
    operation = contract_app.openapi()["paths"][schema_path][method.lower()]
    responses = operation["responses"]
    assert {"401", "403", "404"} <= responses.keys()
    auth_schema = responses["401"]["content"]["application/json"]["schema"]
    assert {entry["$ref"] for entry in auth_schema["anyOf"]} == {
        "#/components/schemas/AuthErrorResponse",
        "#/components/schemas/APIKeyErrorResponse",
    }


def test_readiness_degraded_contract_matches_runtime(contract_app, monkeypatch):
    """Scenario: unavailable dependencies produce a documented 503 readiness payload."""

    async def degraded():
        return ReadinessResponse(status="degraded", checks={"database": "failed", "redis": "ok"})

    # Given: dependency checks fail without contacting external services.
    monkeypatch.setattr("app.main.get_readiness", degraded)
    # When: readiness is requested.
    response = TestClient(contract_app).get("/health/ready")
    # Then: the response matches the published status and model.
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    operation = contract_app.openapi()["paths"]["/health/ready"]["get"]
    assert operation["responses"]["503"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ReadinessResponse"
    }


def test_sse_and_oauth_describe_the_actual_transport(contract_app):
    """Scenario: streams and OAuth redirects are not described as successful JSON responses."""
    paths = contract_app.openapi()["paths"]
    stream = paths["/api/v1/events/stream"]["get"]
    content = stream["responses"]["200"]["content"]
    assert set(content) == {"text/event-stream"}
    assert content["text/event-stream"]["schema"] == {"type": "string"}
    assert content["text/event-stream"]["x-sse-event-schema"]["$ref"].endswith(
        "/RealtimeStreamEvent"
    )
    assert any(p["name"] == "last-event-id" for p in stream["parameters"])
    for suffix in ("start", "callback"):
        responses = paths[f"/api/v1/auth/oauth/{{provider}}/{suffix}"]["get"]["responses"]
        assert "200" not in responses
        assert "307" in responses
        assert "content" not in responses["307"]


def test_domain_and_unexpected_errors_preserve_both_envelopes(contract_app, sample_user):
    """Scenario: a domain 500 and an unexpected 500 retain their distinct existing payloads."""

    class FailingAuthService:
        failure = AuthException(AuthErrorCode.PROFILE_UPDATE_FAILED)

        async def update_profile(self, **kwargs):
            raise self.failure

    # Given: an authenticated route with controllable service failures.
    service = FailingAuthService()
    contract_app.dependency_overrides[get_current_user] = lambda: sample_user
    contract_app.dependency_overrides[AuthService] = lambda: service
    client = TestClient(contract_app, raise_server_exceptions=False)
    # When: domain and unexpected failures occur on the same endpoint.
    domain = client.patch("/api/v1/auth/me", json={"name": "Tester"})
    service.failure = RuntimeError("test failure")
    unexpected = client.patch("/api/v1/auth/me", json={"name": "Tester"})
    # Then: neither wire shape is silently changed or omitted from the schema.
    assert domain.status_code == unexpected.status_code == 500
    assert domain.json()["detail"]["error"] == "PROFILE_UPDATE_FAILED"
    assert unexpected.json()["error"] == "INTERNAL_ERROR"
    response = contract_app.openapi()["paths"]["/api/v1/auth/me"]["patch"]["responses"]["500"]
    assert len(response["content"]["application/json"]["schema"]["anyOf"]) == 2


@pytest.mark.parametrize(
    "event_type", ["api_key.created", "api_key.status_updated", "api_key.deleted"]
)
def test_sse_data_matches_typed_event_contract(event_type):
    """Scenario: API-key event frames carry the shared APIKeyResponse payload schema."""
    # Given: the public API-key fields used by the service publisher.
    event = build_realtime_event(
        event_type,
        {
            "api_key": {
                "id": 1,
                "name": "test",
                "key_prefix": "sk_live_test",
                "created_at": datetime.now(UTC).isoformat(),
                "request_count": 0,
            }
        },
    )
    # When: transport serializes the event into an SSE frame.
    frame = encode_sse_event(event)
    data = next(line[6:] for line in frame.splitlines() if line.startswith("data: "))
    # Then: the JSON data, not the whole stream, conforms to the event contract.
    parsed = RealtimeStreamEvent.model_validate_json(data).root
    assert parsed.type == event_type
    assert parsed.payload.api_key.id == 1
    assert json.loads(data)["id"] == event.id
