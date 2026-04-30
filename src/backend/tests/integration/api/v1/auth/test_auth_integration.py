import pytest
from fastapi.testclient import TestClient

from tests.fixtures.payload_data import (
    INVALID_EMAIL,
    VALID_PASSWORD,
    build_login_payload,
    build_signup_payload,
)
from tests.fixtures.scenario_seed_data import (
    SEEDED_PRIMARY_EMAIL,
    SEEDED_PRIMARY_NAME,
    SEEDED_PRIMARY_PASSWORD,
)


@pytest.mark.primary_data
def test_signup_and_login_flow(integration_client: TestClient):
    """Scenario: a new user can signup and login through real service+DB flow."""
    # Given: clean integration database from fixture.
    # When: user signs up with a valid payload.
    signup_response = integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="integration-user@example.com",
            name="Integration User",
            password=VALID_PASSWORD,
        ),
    )
    # Then: signup succeeds with user payload.
    assert signup_response.status_code == 200
    assert signup_response.json()["email"] == "integration-user@example.com"

    # When: same user logs in with valid credentials.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="integration-user@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    # Then: token contract is returned.
    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "integration-user@example.com"
    assert payload["access_token"]


@pytest.mark.primary_data
def test_me_with_bearer_token(integration_client: TestClient):
    """Scenario: /me returns current user when bearer token is valid."""
    # Given: a signed-up user.
    integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="me-user@example.com",
            name="Me User",
            password=VALID_PASSWORD,
        ),
    )
    # When: user logs in and gets an access token.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="me-user@example.com",
            password=VALID_PASSWORD,
            remember_me=False,
        ),
    )
    access_token = login_response.json()["access_token"]

    # And: token is used on protected /me.
    me_response = integration_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    # Then: user profile is returned.
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "me-user@example.com"


@pytest.mark.primary_data
def test_signup_duplicate_email_returns_409(integration_client: TestClient):
    """Scenario: signup returns domain conflict error for duplicate email."""
    payload = build_signup_payload(
        email="duplicate-user@example.com",
        name="Duplicate User",
        password=VALID_PASSWORD,
    )

    # Given: first signup is successful.
    first_response = integration_client.post("/api/v1/auth/signup", json=payload)
    assert first_response.status_code == 200

    # When: same email signs up again.
    second_response = integration_client.post("/api/v1/auth/signup", json=payload)
    # Then: auth domain error is returned.
    assert second_response.status_code == 409
    assert second_response.json()["detail"]["error"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.primary_data
def test_login_invalid_password_returns_401(integration_client: TestClient):
    """Scenario: login returns invalid credentials for wrong password."""
    # Given: existing user in DB.
    integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="wrong-pass@example.com",
            name="Wrong Pass User",
            password=VALID_PASSWORD,
        ),
    )

    # When: login is attempted with wrong password.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email="wrong-pass@example.com",
            password="InvalidPass1!",
            remember_me=False,
        ),
    )

    # Then: auth domain error is returned.
    assert login_response.status_code == 401
    assert login_response.json()["detail"]["error"] == "INVALID_CREDENTIALS"


@pytest.mark.primary_data
def test_signup_invalid_email_or_password_returns_422(integration_client: TestClient):
    """Scenario: schema-level validation rejects malformed signup payloads."""
    # Given/When: malformed email is submitted.
    invalid_email_response = integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email=INVALID_EMAIL,
            name="Invalid Email",
            password=VALID_PASSWORD,
        ),
    )
    # Then: validation error is returned.
    assert invalid_email_response.status_code == 422

    # Given/When: password policy-violating payload is submitted.
    invalid_password_response = integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email="invalid-password@example.com",
            name="Invalid Password",
            password="alllowercase1!",
        ),
    )
    # Then: validation error is returned.
    assert invalid_password_response.status_code == 422


@pytest.mark.mocked_data
def test_seeded_primary_user_can_login(seeded_integration_client: TestClient):
    """Scenario: seeded baseline user can login in production-like preloaded dataset."""
    # Given: integration fixture preloaded with baseline user + existing users.
    # When: login is attempted with seeded baseline credentials.
    login_response = seeded_integration_client.post(
        "/api/v1/auth/login",
        json=build_login_payload(
            email=SEEDED_PRIMARY_EMAIL,
            password=SEEDED_PRIMARY_PASSWORD,
            remember_me=False,
        ),
    )

    # Then: authentication succeeds and token contract is returned.
    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == SEEDED_PRIMARY_EMAIL


@pytest.mark.mocked_data
def test_seeded_dataset_duplicate_email_signup_returns_409(
    seeded_integration_client: TestClient,
):
    """Scenario: signup detects duplicate email against preloaded user dataset."""
    # Given: seeded baseline user already exists in DB.
    # When: signup is attempted with the same baseline email.
    duplicate_response = seeded_integration_client.post(
        "/api/v1/auth/signup",
        json=build_signup_payload(
            email=SEEDED_PRIMARY_EMAIL,
            name=SEEDED_PRIMARY_NAME,
            password=SEEDED_PRIMARY_PASSWORD,
        ),
    )

    # Then: domain conflict error is returned.
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"]["error"] == "EMAIL_ALREADY_EXISTS"
