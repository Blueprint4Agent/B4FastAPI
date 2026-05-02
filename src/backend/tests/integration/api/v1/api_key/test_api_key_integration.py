import pytest
from fastapi.testclient import TestClient

from tests.fixtures.api_contract_data import API_KEY_CREATE_PAYLOAD
from tests.fixtures.payload_data import (
    VALID_PASSWORD,
    build_login_payload,
    build_signup_payload,
)

pytestmark = pytest.mark.primary_data


def _signup_and_login(client: TestClient, email: str, password: str) -> dict:
    """Create an integration user and return login token payload."""
    # Given/When: a user signs up.
    signup_response = client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(email=email, name="Integration User", password=password),
    )
    # Then: signup succeeds.
    assert signup_response.status_code == 200

    # When: the same user logs in.
    login_response = client.post(
        "/api/v1/auth/login",
        json=build_login_payload(email=email, password=password, remember_me=False),
    )
    # Then: login succeeds and returns token payload.
    assert login_response.status_code == 200
    return login_response.json()


def test_api_key_create_and_list_flow(integration_client: TestClient):
    """Scenario: authenticated user can create and list API keys."""
    # Given: an authenticated user.
    login_payload = _signup_and_login(
        integration_client,
        email="apikey-user@example.com",
        password=VALID_PASSWORD,
    )
    access_token = login_payload["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # When: the user creates an API key.
    create_response = integration_client.post(
        "/api/v1/api-keys",
        json={**API_KEY_CREATE_PAYLOAD, "name": "integration-key"},
        headers=auth_headers,
    )
    # Then: key creation contract is returned.
    assert create_response.status_code == 200
    create_payload = create_response.json()
    assert create_payload["api_key"].startswith("sk_live_")
    assert create_payload["key"]["name"] == "integration-key"
    assert create_payload["key"]["request_count"] == 0
    assert create_payload["key"]["expires_at"] is None

    # When: the user lists API keys.
    list_response = integration_client.get("/api/v1/api-keys", headers=auth_headers)
    # Then: one created key is present.
    assert list_response.status_code == 200
    assert len(list_response.json()["items"]) == 1
    assert list_response.json()["items"][0]["request_count"] == 0


def test_api_key_can_access_protected_route(integration_client: TestClient):
    """Scenario: issued API key can authenticate protected route access."""
    # Given: an authenticated user.
    login_payload = _signup_and_login(
        integration_client,
        email="key-auth-user@example.com",
        password=VALID_PASSWORD,
    )
    access_token = login_payload["access_token"]
    bearer_headers = {"Authorization": f"Bearer {access_token}"}

    # When: the user creates an API key.
    create_response = integration_client.post(
        "/api/v1/api-keys",
        json={**API_KEY_CREATE_PAYLOAD, "name": "key-auth"},
        headers=bearer_headers,
    )
    api_key_value = create_response.json()["api_key"]

    # And: the key is used for protected /me route.
    me_response = integration_client.get("/api/v1/auth/me", headers={"X-API-Key": api_key_value})
    # Then: request is authenticated by API key.
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "key-auth-user@example.com"

    # When: user lists keys after API-key-authenticated access.
    list_response = integration_client.get("/api/v1/api-keys", headers=bearer_headers)
    # Then: request counter has incremented.
    assert list_response.status_code == 200
    assert list_response.json()["items"][0]["request_count"] >= 1
