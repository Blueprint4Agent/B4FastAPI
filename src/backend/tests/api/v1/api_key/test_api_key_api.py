from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.deps import get_current_user
from app.models.api_key import (
    APIKeyCreateForm,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeysResponse,
    APIKeyStatusUpdateForm,
)
from app.models.user import UserResponse
from app.routers.v1 import api_key
from app.services.api_key import APIKeyService
from tests.fixtures.api_contract_data import API_KEY_CREATE_PAYLOAD

pytestmark = pytest.mark.api_test


class FakeAPIKeyService:
    def __init__(self):
        now = datetime.now(UTC)
        self._key = APIKeyResponse(
            id=1,
            name="local-dev",
            key_prefix="sk_live_abcd",
            created_at=now,
            request_count=0,
            last_used_at=None,
            expires_at=None,
            revoked_at=None,
        )

    async def create_api_key(self, *, user_id: int, form: APIKeyCreateForm) -> APIKeyCreateResponse:
        return APIKeyCreateResponse(
            api_key="sk_live_secret_for_test",
            key=APIKeyResponse(
                id=self._key.id,
                name=form.name,
                key_prefix=self._key.key_prefix,
                created_at=self._key.created_at,
                request_count=self._key.request_count,
                last_used_at=self._key.last_used_at,
                expires_at=self._key.expires_at,
                revoked_at=self._key.revoked_at,
            ),
        )

    async def list_api_keys(self, *, user_id: int) -> APIKeysResponse:
        return APIKeysResponse(items=[self._key])

    async def delete_api_key(self, *, user_id: int, api_key_id: int) -> APIKeyResponse:
        return self._key

    async def update_api_key_status(
        self, *, user_id: int, api_key_id: int, form: APIKeyStatusUpdateForm
    ) -> APIKeyResponse:
        return APIKeyResponse(
            id=self._key.id,
            name=self._key.name,
            key_prefix=self._key.key_prefix,
            created_at=self._key.created_at,
            request_count=self._key.request_count,
            last_used_at=self._key.last_used_at,
            expires_at=self._key.expires_at,
            revoked_at=None if form.enabled else datetime.now(UTC),
        )


def create_api_key_test_client(user: UserResponse, with_user_auth: bool = True) -> TestClient:
    app = FastAPI()
    app.include_router(api_key.router, prefix="/api/v1/api-keys")
    app.dependency_overrides[APIKeyService] = lambda: FakeAPIKeyService()
    if with_user_auth:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def test_create_api_key_success(sample_user: UserResponse):
    """Scenario: create API key route returns generated key payload."""
    client = create_api_key_test_client(sample_user)

    # Given/When: authenticated user requests key creation.
    response = client.post("/api/v1/api-keys", json=API_KEY_CREATE_PAYLOAD)

    # Then: created key contract is returned.
    assert response.status_code == 200
    assert response.json()["key"]["name"] == "local-dev"


def test_list_api_keys_success(sample_user: UserResponse):
    """Scenario: list route returns API key collection."""
    client = create_api_key_test_client(sample_user)

    # When: authenticated user requests key list.
    response = client.get("/api/v1/api-keys")

    # Then: list payload includes one fake key.
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


def test_update_api_key_status_success(sample_user: UserResponse):
    """Scenario: status update route returns revoked timestamp when disabled."""
    client = create_api_key_test_client(sample_user)

    # Given/When: authenticated user disables key.
    response = client.patch("/api/v1/api-keys/1/status", json={"enabled": False})

    # Then: response reflects disabled state.
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["revoked_at"] is not None


def test_delete_api_key_success(sample_user: UserResponse):
    """Scenario: delete route returns deleted API key payload."""
    client = create_api_key_test_client(sample_user)

    # Given/When: authenticated user deletes key id=1.
    response = client.delete("/api/v1/api-keys/1")

    # Then: deleted key contract is returned.
    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "local-dev"


def test_api_key_routes_require_authentication(sample_user: UserResponse):
    """Scenario: protected API key route rejects unauthenticated request."""
    client = create_api_key_test_client(sample_user, with_user_auth=False)

    # When: list endpoint is called without auth dependency override.
    response = client.get("/api/v1/api-keys")

    # Then: invalid token domain error is returned.
    assert response.status_code == 401
    assert response.json()["detail"]["error"] == "INVALID_TOKEN"
