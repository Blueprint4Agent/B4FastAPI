from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_user
from app.models.oauth import OAuthProvider, OAuthProviderPublicConfig
from app.models.user import SignupForm, UserResponse
from app.routers.v1 import auth
from app.services.auth import AuthService


class FakeAuthService:
    def __init__(self, user: UserResponse):
        self._user = user

    async def signup(self, _form: SignupForm) -> UserResponse:
        return self._user

    def get_oauth_provider_public_configs(self) -> list[OAuthProviderPublicConfig]:
        return [
            OAuthProviderPublicConfig(
                provider=OAuthProvider.GOOGLE,
                start_path="/api/v1/auth/oauth/google/start",
            )
        ]


def create_auth_test_client(user: UserResponse, with_user_auth: bool = False) -> TestClient:
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.dependency_overrides[AuthService] = lambda: FakeAuthService(user)
    if with_user_auth:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_signup_success(sample_user: UserResponse):
    client = create_auth_test_client(sample_user)

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "tester@example.com",
            "name": "Tester",
            "password": "ValidPass1!",
        },
    )

    assert response.status_code == 200
    assert response.json()["email"] == "tester@example.com"


def test_signup_validation_error_returns_422(sample_user: UserResponse):
    client = create_auth_test_client(sample_user)

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "tester@example.com",
            "name": "Tester",
            "password": "weakpass",
        },
    )

    assert response.status_code == 422


def test_oauth_providers_success(sample_user: UserResponse):
    client = create_auth_test_client(sample_user)

    response = client.get("/api/v1/auth/oauth/providers")

    assert response.status_code == 200
    assert response.json()["providers"][0]["provider"] == "google"


def test_me_requires_authentication(sample_user: UserResponse):
    client = create_auth_test_client(sample_user)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"


def test_me_success_with_dependency_override(sample_user: UserResponse):
    client = create_auth_test_client(sample_user, with_user_auth=True)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == sample_user.id
