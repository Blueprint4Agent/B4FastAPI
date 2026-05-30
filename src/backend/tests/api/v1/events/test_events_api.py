import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_user
from app.main import register_exception_handlers
from app.models.user import UserResponse
from app.routers.v1 import events
from app.services.realtime import RealtimeService

pytestmark = pytest.mark.api_test


class FakeRealtimeService:
    def stream_user_events(self, *, request, current_user, last_event_id):
        _ = request
        _ = current_user
        _ = last_event_id

        async def _stream():
            yield 'event: connected\ndata: {"ok":true}\n\n'

        return _stream()


def create_events_test_client(user: UserResponse, with_user_auth: bool = False) -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(events.router, prefix="/api/v1/events")
    app.dependency_overrides[RealtimeService] = lambda: FakeRealtimeService()
    if with_user_auth:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_events_stream_requires_authentication(sample_user: UserResponse):
    """Scenario: events stream denies access without auth dependency."""
    client = create_events_test_client(sample_user)

    # When: stream endpoint is requested without current-user override.
    response = client.get("/api/v1/events/stream")

    # Then: auth guard returns invalid token contract.
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"


def test_events_stream_returns_sse_contract(sample_user: UserResponse):
    """Scenario: events stream returns text/event-stream payload when authenticated."""
    client = create_events_test_client(sample_user, with_user_auth=True)

    # When: stream endpoint is requested with injected current user.
    response = client.get("/api/v1/events/stream")

    # Then: SSE transport headers and event framing are returned.
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: connected" in response.text
    assert "data:" in response.text
