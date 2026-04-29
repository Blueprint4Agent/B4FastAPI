from fastapi.testclient import TestClient


def test_signup_and_login_flow(integration_client: TestClient):
    """Scenario: a new user can signup and login through real service+DB flow."""
    # Given: clean integration database from fixture.
    # When: user signs up with a valid payload.
    signup_response = integration_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "integration-user@example.com",
            "name": "Integration User",
            "password": "ValidPass1!",
        },
    )
    # Then: signup succeeds with user payload.
    assert signup_response.status_code == 200
    assert signup_response.json()["email"] == "integration-user@example.com"

    # When: same user logs in with valid credentials.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json={
            "email": "integration-user@example.com",
            "password": "ValidPass1!",
            "remember_me": False,
        },
    )
    # Then: token contract is returned.
    assert login_response.status_code == 200
    payload = login_response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "integration-user@example.com"
    assert payload["access_token"]


def test_me_with_bearer_token(integration_client: TestClient):
    """Scenario: /me returns current user when bearer token is valid."""
    # Given: a signed-up user.
    integration_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "me-user@example.com",
            "name": "Me User",
            "password": "ValidPass1!",
        },
    )
    # When: user logs in and gets an access token.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json={
            "email": "me-user@example.com",
            "password": "ValidPass1!",
            "remember_me": False,
        },
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


def test_signup_duplicate_email_returns_409(integration_client: TestClient):
    """Scenario: signup returns domain conflict error for duplicate email."""
    payload = {
        "email": "duplicate-user@example.com",
        "name": "Duplicate User",
        "password": "ValidPass1!",
    }

    # Given: first signup is successful.
    first_response = integration_client.post("/api/v1/auth/signup", json=payload)
    assert first_response.status_code == 200

    # When: same email signs up again.
    second_response = integration_client.post("/api/v1/auth/signup", json=payload)
    # Then: auth domain error is returned.
    assert second_response.status_code == 409
    assert second_response.json()["detail"]["error"] == "EMAIL_ALREADY_EXISTS"


def test_login_invalid_password_returns_401(integration_client: TestClient):
    """Scenario: login returns invalid credentials for wrong password."""
    # Given: existing user in DB.
    integration_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrong-pass@example.com",
            "name": "Wrong Pass User",
            "password": "ValidPass1!",
        },
    )

    # When: login is attempted with wrong password.
    login_response = integration_client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong-pass@example.com",
            "password": "InvalidPass1!",
            "remember_me": False,
        },
    )

    # Then: auth domain error is returned.
    assert login_response.status_code == 401
    assert login_response.json()["detail"]["error"] == "INVALID_CREDENTIALS"


def test_signup_invalid_email_or_password_returns_422(integration_client: TestClient):
    """Scenario: schema-level validation rejects malformed signup payloads."""
    # Given/When: malformed email is submitted.
    invalid_email_response = integration_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "invalid-email",
            "name": "Invalid Email",
            "password": "ValidPass1!",
        },
    )
    # Then: validation error is returned.
    assert invalid_email_response.status_code == 422

    # Given/When: password policy-violating payload is submitted.
    invalid_password_response = integration_client.post(
        "/api/v1/auth/signup",
        json={
            "email": "invalid-password@example.com",
            "name": "Invalid Password",
            "password": "alllowercase1!",
        },
    )
    # Then: validation error is returned.
    assert invalid_password_response.status_code == 422
