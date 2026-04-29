from fastapi.testclient import TestClient

from app.main import app


def test_app_boot_and_ping() -> None:
    """Scenario: app boots and the minimal health-like endpoint responds."""
    # Given: the application is created and started by TestClient.
    with TestClient(app) as client:
        # When: a request is sent to the smoke endpoint.
        response = client.get("/ping")

    # Then: boot succeeds and endpoint contract matches.
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "pong"}
