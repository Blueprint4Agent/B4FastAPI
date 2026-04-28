from fastapi.testclient import TestClient

from app.main import app


def test_app_boot_and_ping() -> None:
    with TestClient(app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "pong"}
