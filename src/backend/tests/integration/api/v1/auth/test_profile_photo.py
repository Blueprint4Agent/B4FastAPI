import asyncio
from io import BytesIO
from unittest.mock import AsyncMock

import pytest
from PIL import Image
from sqlalchemy.exc import OperationalError

from app.core.config.settings import SETTINGS
from app.core.object_storage import StorageError, StorageErrorCode
from app.models.profile_photo import ProfilePhotos
from app.models.user import Users
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data


def login(client, email="photo@example.com"):
    client.post("/api/v1/auth/signup", json=build_signup_payload(email=email))
    response = client.post("/api/v1/auth/login", json=build_login_payload(email=email))
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}, response.json()["user"][
        "id"
    ]


def png(width=1000, height=500):
    buffer = BytesIO()
    image = Image.new("RGBA", (width, height), (255, 0, 0, 128))
    exif = Image.Exif()
    exif[270] = "private metadata"
    image.save(buffer, "PNG", exif=exif)
    return buffer.getvalue()


def test_photo_binary_lifecycle_and_private_ownership(integration_client):
    """Scenario: files are normalized, privately read, replaced and removed without Base64 DB writes."""
    client = integration_client
    # Given: an authenticated user and an image with metadata and transparency.
    headers, user_id = login(client)
    # When: the browser uploads raw image bytes.
    upload = client.put("/api/v1/auth/me/photo", content=png(), headers=headers)
    assert upload.status_code == 200
    url = upload.json()["profile_image_url"]
    snapshot = asyncio.run(ProfilePhotos.get(user_id))
    assert snapshot.reference["key"].startswith(f"profile-photos/{user_id}/")
    assert not url.startswith("data:")
    # Then: the authenticated binary read strips metadata and preserves bounded alpha pixels.
    photo = client.get(url, headers=headers)
    assert photo.status_code == 200
    assert photo.headers["cache-control"] == "private, no-store"
    with Image.open(BytesIO(photo.content)) as image:
        assert image.format == "WEBP" and image.size == (512, 256)
        assert not image.getexif()
        assert image.getpixel((10, 10))[3] == 128
    assert client.get(url).status_code == 401
    other, _ = login(client, "other-photo@example.com")
    assert client.get(url, headers=other).status_code == 404
    replacement = client.put("/api/v1/auth/me/photo", content=png(10, 10), headers=headers)
    assert replacement.status_code == 200
    assert client.get(url, headers=headers).status_code == 404
    assert len(list(SETTINGS.OBJECT_STORAGE_LOCAL_ROOT.glob("*.object"))) == 1
    removed = client.delete("/api/v1/auth/me/photo", headers=headers)
    assert removed.status_code == 200 and removed.json()["profile_image_url"] is None
    assert list(SETTINGS.OBJECT_STORAGE_LOCAL_ROOT.glob("*.object")) == []
    assert client.delete("/api/v1/auth/me/photo", headers=headers).status_code == 200


@pytest.mark.parametrize(
    "payload,status", [(b"not an image", 422), (b"x" * (8 * 1024 * 1024 + 1), 413)]
)
def test_invalid_upload_preserves_confirmed_photo(integration_client, payload, status):
    """Scenario: invalid and oversized requests cannot replace a valid profile photo."""
    client = integration_client
    # Given: a previously saved photo.
    headers, _ = login(client)
    old = client.put("/api/v1/auth/me/photo", content=png(10, 10), headers=headers).json()
    # When: malformed/oversized bytes arrive.
    result = client.put("/api/v1/auth/me/photo", content=payload, headers=headers)
    # Then: validation rejects the body while the old photo remains readable.
    assert result.status_code == status
    assert (
        client.get("/api/v1/auth/me", headers=headers).json()["profile_image_url"]
        == old["profile_image_url"]
    )
    assert client.get(old["profile_image_url"], headers=headers).status_code == 200


@pytest.mark.parametrize("failure", ["storage", "db", "conflict"])
def test_failed_replacement_preserves_old_reference_and_cleans_new_object(
    integration_client, monkeypatch, failure
):
    """Scenario: storage/DB failure and concurrent modification never destroy the confirmed photo."""
    client = integration_client
    # Given: a persisted old photo and an injected failure at one boundary.
    headers, _ = login(client)
    old = client.put("/api/v1/auth/me/photo", content=png(10, 10), headers=headers).json()
    if failure == "storage":
        monkeypatch.setattr(
            client.app.state.object_storage,
            "put",
            AsyncMock(side_effect=StorageError(StorageErrorCode.UNAVAILABLE)),
        )
    elif failure == "db":
        monkeypatch.setattr(
            ProfilePhotos,
            "replace",
            AsyncMock(side_effect=OperationalError("test", {}, Exception())),
        )
    else:
        monkeypatch.setattr(ProfilePhotos, "replace", AsyncMock(return_value=False))
    # When: replacement fails.
    result = client.put("/api/v1/auth/me/photo", content=png(20, 20), headers=headers)
    # Then: the old reference/file survives and the unreferenced new key is removed.
    assert result.status_code == {"storage": 503, "db": 500, "conflict": 409}[failure]
    assert (
        client.get("/api/v1/auth/me", headers=headers).json()["profile_image_url"]
        == old["profile_image_url"]
    )
    assert client.get(old["profile_image_url"], headers=headers).status_code == 200
    assert len(list(SETTINGS.OBJECT_STORAGE_LOCAL_ROOT.glob("*.object"))) == 1


def test_cleanup_failure_does_not_reverse_success(integration_client, monkeypatch, caplog):
    """Scenario: post-commit cleanup failure leaves a traceable orphan and a working new photo."""
    client = integration_client
    # Given: an old photo and an unavailable delete operation.
    headers, _ = login(client)
    client.put("/api/v1/auth/me/photo", content=png(10, 10), headers=headers)
    monkeypatch.setattr(
        client.app.state.object_storage,
        "delete",
        AsyncMock(side_effect=StorageError(StorageErrorCode.UNAVAILABLE)),
    )
    # When: replacement commits successfully.
    result = client.put("/api/v1/auth/me/photo", content=png(20, 20), headers=headers)
    # Then: success is truthful; old-object cleanup is recorded separately.
    assert result.status_code == 200
    assert client.get(result.json()["profile_image_url"], headers=headers).status_code == 200
    assert "cleanup deferred" in caplog.text


def test_compare_and_swap_rejects_stale_revision(integration_client):
    """Scenario: a stale mutation cannot overwrite a newer DB photo revision."""
    # Given: two writers observed the initial null revision.
    _, user_id = login(integration_client)
    # When: one revision commits first.
    assert asyncio.run(ProfilePhotos.replace(user_id, None, "first", None))
    # Then: the second writer cannot overwrite it with the same old expectation.
    assert not asyncio.run(ProfilePhotos.replace(user_id, None, "second", None))
    assert asyncio.run(ProfilePhotos.get(user_id)).url == "first"


def test_legacy_patch_cannot_reintroduce_base64(integration_client):
    """Scenario: legacy stored photos remain readable, but PATCH cannot write new Base64."""
    # Given: an authenticated user.
    headers, _ = login(integration_client)
    # When: the obsolete transport attempts a new data URL.
    result = integration_client.patch(
        "/api/v1/auth/me", json={"profile_image_url": "data:image/png;base64,eA=="}, headers=headers
    )
    # Then: the API explicitly requires dedicated photo endpoints.
    assert result.status_code == 422


def test_account_delete_returns_reference_for_cleanup(integration_client):
    """Scenario: committed account deletion retains its final photo reference for cleanup."""
    # Given: an account with a managed photo.
    headers, user_id = login(integration_client)
    integration_client.put("/api/v1/auth/me/photo", content=png(10, 10), headers=headers)
    photo = asyncio.run(ProfilePhotos.get(user_id)).reference
    # When: the repository deletes the user transactionally.
    result = asyncio.run(Users.delete_account(user_id, "photo@example.com"))
    # Then: the service receives the exact key to clean, not a stale pre-delete snapshot.
    assert result == photo


def test_ambiguous_commit_does_not_delete_current_image(integration_client, monkeypatch):
    """Scenario: a lost DB acknowledgment cannot cause compensation to delete committed data."""
    client = integration_client
    # Given: commit succeeds but its acknowledgment fails.
    headers, user_id = login(client)
    replace = ProfilePhotos.replace

    async def commit_then_fail(*args):
        await replace(*args)
        raise OperationalError("test", {}, Exception())

    monkeypatch.setattr(ProfilePhotos, "replace", commit_then_fail)
    # When: the upload receives an ambiguous DB failure.
    response = client.put("/api/v1/auth/me/photo", content=png(10, 10), headers=headers)
    # Then: server truth still points at an intact photo; reload can reconcile the error.
    assert response.status_code == 500
    current = asyncio.run(ProfilePhotos.get(user_id))
    assert current.reference is not None
    assert client.get(current.url, headers=headers).status_code == 200


@pytest.mark.parametrize("method", ["put", "get", "delete"])
def test_photo_endpoints_require_authentication(integration_client, method):
    """Scenario: every photo operation rejects an unauthenticated caller."""
    # Given/When: no session or API-key headers are supplied.
    response = getattr(integration_client, method)("/api/v1/auth/me/photo")
    # Then: the shared auth boundary prevents any private file access.
    assert response.status_code == 401
