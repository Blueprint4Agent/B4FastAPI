import pytest
from fastapi.testclient import TestClient

from app.core.cache.redis import RedisManager
from tests.fixtures.payload_data import build_login_payload, build_signup_payload


@pytest.mark.primary_data
def test_cookie_refresh_requires_session_bound_proof(integration_client: TestClient):
    """Reject forged requests without mutating the session, then recover normally."""
    client = integration_client
    client.post("/api/v1/auth/signup", json=build_signup_payload())
    login = client.post("/api/v1/auth/login", json=build_login_payload())
    assert login.status_code == 200
    sid = client.cookies["template_refresh_sid"]
    refresh_token = login.json()["refresh_token"]

    assert client.get("/api/v1/auth/csrf").status_code == 403
    bootstrap = client.get("/api/v1/auth/csrf", headers={"X-CSRF-Bootstrap": "1"})
    assert bootstrap.status_code == 200
    proof = bootstrap.json()["csrf_token"]
    assert proof != refresh_token
    assert bootstrap.headers["cache-control"] == "no-store"
    assert (
        client.get("/api/v1/auth/csrf", headers={"X-CSRF-Bootstrap": "1"}).json()
        == bootstrap.json()
    )

    # Empty simple POST and partial explicit input cannot bypass cookie protection.
    for body in (None, {}, {"session_id": sid}, {"refresh_token": refresh_token}):
        denied = client.post("/api/v1/auth/refresh", json=body)
        assert denied.status_code == 403
        assert denied.json()["detail"]["error"] == "CSRF_INVALID"
    denied = client.post("/api/v1/auth/refresh", json={}, headers={"X-CSRF-Token": "forged"})
    assert denied.status_code == 403

    # A separate session of the same user must not accept the first session's proof.
    client.post("/api/v1/auth/login", json=build_login_payload())
    assert client.cookies["template_refresh_sid"] != sid
    assert (
        client.post("/api/v1/auth/refresh", json={}, headers={"X-CSRF-Token": proof}).status_code
        == 403
    )
    second = client.get("/api/v1/auth/csrf", headers={"X-CSRF-Bootstrap": "1"}).json()["csrf_token"]
    refreshed = client.post("/api/v1/auth/refresh", json={}, headers={"X-CSRF-Token": second})
    assert refreshed.status_code == 200
    assert refreshed.headers["cache-control"] == "no-store"
    assert (
        client.get("/api/v1/auth/csrf", headers={"X-CSRF-Bootstrap": "1"}).json()["csrf_token"]
        == second
    )

    # Fully explicit clients remain supported even with unrelated ambient cookies.
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"session_id": sid, "refresh_token": refresh_token}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
        ).status_code
        == 200
    )

    async def assert_revoked():
        redis = await RedisManager.get_client()
        assert await redis.get(f"refresh_csrf:{sid}") is None

    client.portal.call(assert_revoked)
    client.cookies.set("template_refresh_sid", sid)
    client.cookies.set("template_refresh_token", refresh_token)
    assert client.get("/api/v1/auth/csrf", headers={"X-CSRF-Bootstrap": "1"}).status_code == 401
    assert (
        client.post("/api/v1/auth/refresh", json={}, headers={"X-CSRF-Token": proof}).status_code
        == 403
    )


@pytest.mark.primary_data
def test_csrf_bootstrap_disallows_untrusted_preflight(integration_client: TestClient):
    """The bootstrap custom header cannot be sent by an untrusted browser origin."""
    assert (
        integration_client.get("/api/v1/auth/csrf", headers={"X-CSRF-Bootstrap": "1"}).status_code
        == 401
    )
    response = integration_client.options(
        "/api/v1/auth/csrf",
        headers={
            "Origin": "https://attacker.invalid",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-CSRF-Bootstrap",
        },
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
