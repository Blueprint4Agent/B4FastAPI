import pytest
from fastapi.testclient import TestClient

from app.core.config.settings import SETTINGS
from app.utils.cookies import REFRESH_SID_COOKIE_NAME
from tests.fixtures.payload_data import build_login_payload, build_signup_payload
from tests.fixtures.scenario_flow_data import DEFAULT_FULL_SYSTEM_SCENARIO

pytestmark = [pytest.mark.mocked_data, pytest.mark.scenario_flow]


def _login_seeded_primary_user(client: TestClient) -> tuple[dict[str, object], dict[str, str]]:
    """Login the seeded primary user and return token payload with bearer headers."""
    scenario = DEFAULT_FULL_SYSTEM_SCENARIO

    # Given/When: seeded primary user logs in with known credentials.
    login_response = client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email=scenario.login_email,
            password=scenario.login_password,
            remember_me=False,
        ),
    )
    # Then: token contract is returned.
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["user"]["email"] == scenario.login_email
    assert login_payload["user"]["role"] == scenario.expected_principal_role
    bearer_headers = {"Authorization": f"Bearer {login_payload['access_token']}"}
    return login_payload, bearer_headers


def test_seeded_auth_domain_main_flow(seeded_integration_client: TestClient):
    """Scenario: seeded dataset executes auth domain success and failure branches in sequence."""
    scenario = DEFAULT_FULL_SYSTEM_SCENARIO

    # Given: seeded integration dataset with baseline primary user.
    # When: baseline user logs in.
    login_payload, bearer_headers = _login_seeded_primary_user(seeded_integration_client)
    refresh_session_id = seeded_integration_client.cookies.get(REFRESH_SID_COOKIE_NAME)
    assert refresh_session_id is not None

    # When: oauth provider list is requested.
    oauth_providers_response = seeded_integration_client.get("/api/v1/auth/oauth/providers")
    # Then: route responds with provider list contract.
    assert oauth_providers_response.status_code == 200
    assert "providers" in oauth_providers_response.json()

    # When: authenticated user requests /me.
    me_response = seeded_integration_client.get("/api/v1/auth/me", headers=bearer_headers)
    # Then: current user payload is returned.
    assert me_response.status_code == 200
    assert me_response.json()["email"] == scenario.login_email
    assert me_response.json()["role"] == scenario.expected_principal_role

    # When: admin user requests user-role stats endpoint.
    admin_stats_response = seeded_integration_client.get(
        "/api/v1/auth/admin/user-role-stats",
        headers=bearer_headers,
    )
    # Then: admin-only role stats contract is returned.
    assert admin_stats_response.status_code == 200
    assert admin_stats_response.json()["admin_users"] >= 1

    # When: authenticated user updates profile name.
    update_response = seeded_integration_client.patch(
        "/api/v1/auth/me",
        json={"name": scenario.profile_update_name},
        headers=bearer_headers,
    )
    # Then: profile update contract is returned.
    assert update_response.status_code == 200
    assert update_response.json()["name"] == scenario.profile_update_name

    # When: refresh token flow is requested with session context.
    refresh_response = seeded_integration_client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": login_payload["refresh_token"],
            "user_id": login_payload["user"]["id"],
            "session_id": refresh_session_id,
        },
    )
    # Then: refresh succeeds with bearer token contract.
    assert refresh_response.status_code == 200
    refreshed_access_token = refresh_response.json()["access_token"]
    assert refreshed_access_token

    # When: logout is requested.
    logout_response = seeded_integration_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {refreshed_access_token}"},
    )
    # Then: logout success message is returned.
    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Successfully logged out."

    # When: the same refresh context is used after logout.
    refresh_after_logout_response = seeded_integration_client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": login_payload["refresh_token"],
            "user_id": login_payload["user"]["id"],
            "session_id": refresh_session_id,
        },
    )
    # Then: refresh is rejected because the session was invalidated on logout.
    assert refresh_after_logout_response.status_code == 401
    assert refresh_after_logout_response.json()["detail"]["error"] == "INVALID_TOKEN"

    # When: signup is retried with an already-seeded email.
    duplicate_signup_response = seeded_integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email=scenario.login_email,
            name=scenario.profile_update_name,
            password=scenario.login_password,
        ),
    )
    # Then: duplicate email conflict is returned.
    assert duplicate_signup_response.status_code == 409
    assert duplicate_signup_response.json()["detail"]["error"] == "EMAIL_ALREADY_EXISTS"

    # When: login is attempted with an invalid password.
    invalid_login_response = seeded_integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email=scenario.login_email,
            password=scenario.invalid_login_password,
            remember_me=False,
        ),
    )
    # Then: invalid credentials error is returned.
    assert invalid_login_response.status_code == 401
    assert invalid_login_response.json()["detail"]["error"] == "INVALID_CREDENTIALS"

    # When: signup is attempted with malformed email.
    malformed_signup_response = seeded_integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email=scenario.malformed_signup_email,
            name="Malformed Email",
            password=scenario.login_password,
        ),
    )
    # Then: schema validation rejects the request.
    assert malformed_signup_response.status_code == 422

    # When: resend verification endpoint is called.
    resend_verification_response = seeded_integration_client.post(
        "/api/v1/auth/resend-verification",
        json={"email": scenario.login_email},
    )
    # Then: resend endpoint returns generic success contract.
    assert resend_verification_response.status_code == 200

    # When: forgot-password endpoint is called.
    forgot_password_response = seeded_integration_client.post(
        "/api/v1/auth/forgot-password",
        json={"email": scenario.login_email},
    )
    # Then: behavior follows email feature toggle.
    if SETTINGS.EMAIL_ENABLED:
        assert forgot_password_response.status_code == 200
    else:
        assert forgot_password_response.status_code == 403
        assert forgot_password_response.json()["detail"]["error"] == "EMAIL_DISABLED"


def test_seeded_api_key_domain_main_flow(seeded_integration_client: TestClient):
    """Scenario: seeded dataset executes API key domain full flow including failure branches."""
    scenario = DEFAULT_FULL_SYSTEM_SCENARIO

    # Given: seeded primary user is authenticated.
    # When: baseline user logs in for bearer token issuance.
    _, bearer_headers = _login_seeded_primary_user(seeded_integration_client)

    # When: the user creates an API key.
    create_response = seeded_integration_client.post(
        "/api/v1/api-keys",
        json={"name": scenario.api_key_name},
        headers=bearer_headers,
    )
    # Then: API key is issued.
    assert create_response.status_code == 200
    create_payload = create_response.json()
    assert create_payload["api_key"].startswith("sk_live_")
    assert create_payload["key"]["name"] == scenario.api_key_name
    assert create_payload["key"]["request_count"] == 0
    assert create_payload["key"]["expires_at"] is None
    created_key_id = create_payload["key"]["id"]
    raw_api_key = create_payload["api_key"]

    if scenario.expect_duplicate_api_key_name_rejected:
        # When: duplicate API key name is requested by same user.
        duplicate_name_response = seeded_integration_client.post(
            "/api/v1/api-keys",
            json={"name": scenario.api_key_name},
            headers=bearer_headers,
        )
        # Then: duplicate-name conflict is returned.
        assert duplicate_name_response.status_code == 409
        assert duplicate_name_response.json()["detail"]["error"] == "API_KEY_NAME_ALREADY_EXISTS"

    # When: key list is requested.
    list_response = seeded_integration_client.get("/api/v1/api-keys", headers=bearer_headers)
    # Then: created key appears in list.
    assert list_response.status_code == 200
    names = [item["name"] for item in list_response.json()["items"]]
    assert scenario.api_key_name in names

    # When: issued API key is used for protected /me.
    me_with_key_response = seeded_integration_client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": raw_api_key},
    )
    # Then: API key authentication succeeds.
    assert me_with_key_response.status_code == 200
    assert me_with_key_response.json()["email"] == scenario.login_email

    # And: API key usage count is incremented after authenticated access.
    list_after_key_use_response = seeded_integration_client.get(
        "/api/v1/api-keys",
        headers=bearer_headers,
    )
    assert list_after_key_use_response.status_code == 200
    key_row = next(
        item for item in list_after_key_use_response.json()["items"] if item["id"] == created_key_id
    )
    assert key_row["request_count"] >= 1

    # When: key is disabled.
    disable_response = seeded_integration_client.patch(
        f"/api/v1/api-keys/{created_key_id}/status",
        json={"enabled": False},
        headers=bearer_headers,
    )
    # Then: key is marked revoked.
    assert disable_response.status_code == 200
    assert disable_response.json()["revoked_at"] is not None

    if scenario.expect_disabled_api_key_rejected:
        # When: disabled key is reused.
        me_with_disabled_key_response = seeded_integration_client.get(
            "/api/v1/auth/me",
            headers={"X-API-Key": raw_api_key},
        )
        # Then: API key auth is rejected.
        assert me_with_disabled_key_response.status_code == 401
        assert me_with_disabled_key_response.json()["detail"]["error"] == "API_KEY_INVALID"

    # When: key is enabled again.
    enable_response = seeded_integration_client.patch(
        f"/api/v1/api-keys/{created_key_id}/status",
        json={"enabled": True},
        headers=bearer_headers,
    )
    # Then: revoked state is cleared.
    assert enable_response.status_code == 200
    assert enable_response.json()["revoked_at"] is None

    # When: re-enabled key is reused.
    me_with_reenabled_key_response = seeded_integration_client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": raw_api_key},
    )
    # Then: API key authentication succeeds again.
    assert me_with_reenabled_key_response.status_code == 200
    assert me_with_reenabled_key_response.json()["email"] == scenario.login_email

    # When: key is deleted.
    delete_response = seeded_integration_client.delete(
        f"/api/v1/api-keys/{created_key_id}",
        headers=bearer_headers,
    )
    # Then: deleted key contract is returned.
    assert delete_response.status_code == 200
    assert delete_response.json()["id"] == created_key_id

    # When: same key is deleted again.
    delete_missing_response = seeded_integration_client.delete(
        f"/api/v1/api-keys/{created_key_id}",
        headers=bearer_headers,
    )
    # Then: domain not-found error payload is returned.
    assert delete_missing_response.status_code == 404
    assert delete_missing_response.json()["detail"]["error"] == "API_KEY_NOT_FOUND"
