import asyncio
from io import BytesIO
from unittest.mock import Mock

import pytest
from botocore.exceptions import EndpointConnectionError
from botocore.response import StreamingBody
from botocore.stub import Stubber
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config.settings import Settings
from app.core.object_storage import (
    ObjectStorage,
    StorageError,
    StorageErrorCode,
    create_object_storage,
    object_storage_lifespan,
)
from app.core.object_storage.local import LocalObjectStorage
from app.core.object_storage.s3 import S3ObjectStorage, create_s3_client
from app.deps import get_object_storage


def settings(**overrides):
    values = dict(
        OBJECT_STORAGE_PROVIDER="local",
        OBJECT_STORAGE_S3_ENDPOINT_URL="",
        OBJECT_STORAGE_S3_BUCKET="objects",
        OBJECT_STORAGE_S3_REGION="us-east-1",
        OBJECT_STORAGE_S3_ACCESS_KEY_ID="test-key",
        OBJECT_STORAGE_S3_SECRET_ACCESS_KEY="test-secret",
        OBJECT_STORAGE_S3_SESSION_TOKEN="",
        APP_MODE="development",
        LOGIN_ENABLED=True,
    )
    return Settings(**(values | overrides))


def test_local_roundtrip_replace_reopen_delete(tmp_path):
    """Scenario: private objects retain metadata and bytes across provider restarts."""

    async def scenario():
        # Given: a private temporary storage root.
        storage = await create_object_storage(settings(OBJECT_STORAGE_LOCAL_ROOT=tmp_path))
        # When: a nested logical key is created and atomically replaced.
        await storage.put("avatars/user-1.webp", b"old", "image/webp")
        result = await storage.put("avatars/user-1.webp", b"new bytes", "image/png")
        await storage.close()
        storage = await create_object_storage(settings(OBJECT_STORAGE_LOCAL_ROOT=tmp_path))
        # Then: stat/get use persisted metadata and missing deletes are idempotent.
        assert result == await storage.stat(result.key)
        obj = await storage.get(result.key)
        assert obj.metadata.content_type == "image/png"
        assert obj.data == b"new bytes"
        assert obj.metadata.size == 9
        await storage.delete(result.key)
        await storage.delete(result.key)
        with pytest.raises(StorageError) as error:
            await storage.get(result.key)
        assert error.value.code == StorageErrorCode.NOT_FOUND
        await storage.close()
        with pytest.raises(StorageError) as error:
            await storage.get(result.key)
        assert error.value.code == StorageErrorCode.CLOSED

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "key", ["../escape", "/absolute", "a/../b", "a//b", "a/", "a\\b", "a/%2e", "", "a" * 513]
)
def test_invalid_keys_rejected_by_both_providers(tmp_path, key):
    """Scenario: keys cannot escape a storage root or exploit ambiguous path syntax."""

    async def scenario():
        # Given: both providers without any external I/O.
        client = Mock()
        stores = [LocalObjectStorage(tmp_path, 100), S3ObjectStorage(client, "bucket", 100)]
        # When/Then: every operation rejects the key before I/O.
        for storage in stores:
            for call in (
                lambda storage=storage: storage.put(key, b"x"),
                lambda storage=storage: storage.get(key),
                lambda storage=storage: storage.stat(key),
                lambda storage=storage: storage.delete(key),
            ):
                with pytest.raises(StorageError) as error:
                    await call()
                assert error.value.code == StorageErrorCode.INVALID_INPUT
        assert not client.mock_calls

    asyncio.run(scenario())


def test_local_symlink_and_corruption_cannot_read_external_data(tmp_path):
    """Scenario: an object symlink or malformed record never exposes an external file."""

    async def scenario():
        # Given: a symlink at a valid object's hashed path.
        root = tmp_path / "objects"
        storage = LocalObjectStorage(root, 100)
        await storage.initialize()
        outside = tmp_path / "private"
        outside.write_bytes(b"secret")
        target = storage._path("key")
        target.symlink_to(outside)
        # When/Then: read fails and overwrite replaces the link, not its target.
        with pytest.raises(StorageError):
            await storage.get("key")
        await storage.put("key", b"safe")
        assert outside.read_bytes() == b"secret"
        assert (await storage.get("key")).data == b"safe"
        target.write_bytes(b"broken")
        with pytest.raises(StorageError) as error:
            await storage.stat("key")
        assert error.value.code == StorageErrorCode.CORRUPT_OBJECT

    asyncio.run(scenario())


def test_local_concurrent_writes_and_failed_replace_preserve_complete_object(tmp_path, monkeypatch):
    """Scenario: racing writes never mix metadata/payload, and failure preserves the old file."""

    async def scenario():
        # Given: two complete replacements for one key.
        storage = LocalObjectStorage(tmp_path, 100)
        await storage.initialize()
        # When: writes race.
        await asyncio.gather(
            storage.put("key", b"a", "image/png"), storage.put("key", b"bbbb", "image/webp")
        )
        # Then: either complete record wins.
        obj = await storage.get("key")
        assert (obj.data, obj.metadata.content_type) in {
            (b"a", "image/png"),
            (b"bbbb", "image/webp"),
        }
        with monkeypatch.context() as patch:
            patch.setattr(
                "app.core.object_storage.local.os.replace",
                Mock(side_effect=OSError("private path")),
            )
            with pytest.raises(StorageError) as error:
                await storage.put("key", b"other")
            assert "private path" not in str(error.value)
        assert await storage.get("key") == obj
        assert not list(tmp_path.glob(".put-*"))

    asyncio.run(scenario())


def test_both_providers_enforce_put_limits_and_content_type(tmp_path):
    """Scenario: oversized payloads and header injection fail before any writes."""

    async def scenario():
        # Given: small limits on both providers.
        for storage in (LocalObjectStorage(tmp_path, 2), S3ObjectStorage(Mock(), "bucket", 2)):
            # When/Then: bounds and unsafe MIME values fail identically.
            with pytest.raises(StorageError) as error:
                await storage.put("key", b"123")
            assert error.value.code == StorageErrorCode.TOO_LARGE
            with pytest.raises(StorageError) as error:
                await storage.put("key", b"1", "image/png\r\nX-Test: yes")
            assert error.value.code == StorageErrorCode.INVALID_INPUT

    asyncio.run(scenario())


def test_s3_contract_with_real_sdk_stub():
    """Scenario: the common SDK adapter uses only portable object operations and closes bodies."""

    async def scenario():
        # Given: a real SDK client with all network calls intercepted by Stubber.
        client = create_s3_client(settings(OBJECT_STORAGE_PROVIDER="s3"))
        storage = S3ObjectStorage(client, "objects", 100)
        raw = BytesIO(b"hello")
        with Stubber(client) as stub:
            stub.add_response(
                "put_object",
                {},
                {"Bucket": "objects", "Key": "key", "Body": b"hello", "ContentType": "text/plain"},
            )
            stub.add_response(
                "head_object",
                {"ContentLength": 5, "ContentType": "text/plain"},
                {"Bucket": "objects", "Key": "key"},
            )
            stub.add_response(
                "get_object",
                {"ContentLength": 5, "ContentType": "text/plain", "Body": StreamingBody(raw, 5)},
                {"Bucket": "objects", "Key": "key"},
            )
            stub.add_response("delete_object", {}, {"Bucket": "objects", "Key": "key"})
            # When: the full object lifecycle executes.
            meta = await storage.put("key", b"hello", "text/plain")
            assert await storage.stat("key") == meta
            obj = await storage.get("key")
            await storage.delete("key")
            # Then: payload/metadata match, stream closes, and all expectations were consumed.
            assert obj.metadata == meta and obj.data == b"hello"
            assert raw.closed
            stub.assert_no_pending_responses()
        await storage.close()
        with pytest.raises(StorageError) as error:
            await storage.stat("key")
        assert error.value.code == StorageErrorCode.CLOSED

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "code,status,expected",
    [
        ("NoSuchKey", 404, StorageErrorCode.NOT_FOUND),
        ("AccessDenied", 403, StorageErrorCode.ACCESS_DENIED),
        ("NoSuchBucket", 404, StorageErrorCode.UNAVAILABLE),
        ("SlowDown", 503, StorageErrorCode.UNAVAILABLE),
    ],
)
def test_s3_errors_are_sanitized(code, status, expected):
    """Scenario: vendor messages and URLs are excluded from normalized storage errors."""

    async def scenario():
        # Given: a failing remote response.
        client = create_s3_client(settings(OBJECT_STORAGE_PROVIDER="s3"))
        storage = S3ObjectStorage(client, "objects", 100)
        with Stubber(client) as stub:
            stub.add_client_error(
                "get_object",
                service_error_code=code,
                service_message="private-token",
                http_status_code=status,
            )
            # When/Then: only the normalized code reaches the caller.
            with pytest.raises(StorageError) as error:
                await storage.get("key")
            assert error.value.code == expected
            assert "private-token" not in str(error.value)
        await storage.close()

    asyncio.run(scenario())


def test_s3_limit_closes_body_and_network_failure_is_unavailable():
    """Scenario: oversize objects release connections and network errors never fall back."""

    async def scenario():
        # Given: an oversized remote response.
        raw = BytesIO(b"123")
        client = Mock()
        client.get_object.return_value = {"ContentLength": 3, "Body": StreamingBody(raw, 3)}
        storage = S3ObjectStorage(client, "objects", 2)
        # When/Then: reject before reading and close the body.
        with pytest.raises(StorageError) as error:
            await storage.get("key")
        assert error.value.code == StorageErrorCode.TOO_LARGE
        assert raw.closed
        client.get_object.side_effect = EndpointConnectionError(
            endpoint_url="https://private-token"
        )
        with pytest.raises(StorageError) as error:
            await storage.get("key")
        assert error.value.code == StorageErrorCode.UNAVAILABLE
        assert "private-token" not in str(error.value)

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "provider,region,style",
    [("s3", "us-east-1", "auto"), ("r2", "auto", "path"), ("supabase", "us-east-1", "path")],
)
def test_remote_provider_presets_share_adapter(provider, region, style):
    """Scenario: explicit remote selections configure one transport with correct defaults."""

    async def scenario():
        # Given: offline SDK configuration with explicit fake credentials.
        config = settings(
            OBJECT_STORAGE_PROVIDER=provider,
            OBJECT_STORAGE_S3_ENDPOINT_URL="https://storage.example.com",
        )
        # When: the factory constructs the remote provider without bucket requests.
        storage = await create_object_storage(config)
        # Then: settings produce the correct signature, region and addressing behavior.
        assert isinstance(storage, S3ObjectStorage)
        assert storage._client.meta.region_name == region
        assert storage._client.meta.config.s3["addressing_style"] == style
        assert storage._client.meta.config.signature_version == "s3v4"
        assert storage._client.meta.config.retries["total_max_attempts"] == 3
        await storage.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "overrides",
    [
        {"OBJECT_STORAGE_PROVIDER": "unknown"},
        {"OBJECT_STORAGE_PROVIDER": "s3", "OBJECT_STORAGE_S3_BUCKET": ""},
        {"OBJECT_STORAGE_PROVIDER": "r2"},
        {
            "OBJECT_STORAGE_PROVIDER": "supabase",
            "OBJECT_STORAGE_S3_ENDPOINT_URL": "https://example.com",
            "OBJECT_STORAGE_S3_REGION": "",
        },
        {"OBJECT_STORAGE_PROVIDER": "s3", "OBJECT_STORAGE_S3_SECRET_ACCESS_KEY": ""},
        {
            "OBJECT_STORAGE_PROVIDER": "s3",
            "OBJECT_STORAGE_S3_ENDPOINT_URL": "https://user:pass@example.com",
        },
        {
            "OBJECT_STORAGE_PROVIDER": "s3",
            "OBJECT_STORAGE_S3_ENDPOINT_URL": "http://example.com",
            "APP_MODE": "production",
        },
        {"OBJECT_STORAGE_LOCAL_ROOT": "relative"},
        {"OBJECT_STORAGE_MAX_BYTES": 0},
        {"OBJECT_STORAGE_TIMEOUT_SECONDS": 0},
    ],
)
def test_invalid_settings_fail_early(overrides):
    """Scenario: invalid provider configuration fails before storage I/O."""
    # Given/When/Then: construction validates settings, without attempting remote fallback.
    with pytest.raises((ValueError, ValidationError)):
        settings(**overrides)


def test_secrets_excluded_and_aws_credential_chain_allowed():
    """Scenario: config serialization hides secrets and AWS supports role-based credentials."""
    # Given: explicit secrets in centralized settings.
    config = settings()
    # When/Then: dumps/repr cannot leak the storage access key or secret.
    assert "test-secret" not in repr(config)
    assert "test-secret" not in config.model_dump_json()
    assert "OBJECT_STORAGE_S3_ACCESS_KEY_ID" not in config.model_dump()
    config = settings(
        OBJECT_STORAGE_PROVIDER="s3",
        OBJECT_STORAGE_S3_ACCESS_KEY_ID="",
        OBJECT_STORAGE_S3_SECRET_ACCESS_KEY="",
    )
    assert config.OBJECT_STORAGE_PROVIDER == "s3"


def test_lifespan_dependency_and_cleanup_on_failure(tmp_path):
    """Scenario: application DI owns one provider and closes it even on downstream failure."""
    # Given: an isolated app with the real storage lifespan and dependency.
    config = settings(OBJECT_STORAGE_LOCAL_ROOT=tmp_path)
    app = FastAPI(lifespan=lambda app: object_storage_lifespan(app, config))

    @app.get("/object")
    async def read_object(storage: ObjectStorage = Depends(get_object_storage)):
        await storage.put("key", b"hello")
        return {"size": (await storage.get("key")).metadata.size}

    # When: a request resolves DI through the application lifespan.
    with TestClient(app) as client:
        storage = app.state.object_storage
        assert client.get("/object").json() == {"size": 5}
    # Then: shutdown clears the reference and closes the instance.
    assert not hasattr(app.state, "object_storage")
    assert storage._closed

    async def fail():
        with pytest.raises(RuntimeError, match="downstream"):
            async with object_storage_lifespan(app, config):
                inner = app.state.object_storage
                raise RuntimeError("downstream")
        assert inner._closed
        assert not hasattr(app.state, "object_storage")

    asyncio.run(fail())


def test_startup_local_probe_logs_success_and_leaves_no_file(tmp_path, caplog):
    """Scenario: local startup verifies write/read/delete and emits safe success evidence."""

    async def scenario():
        # Given: private local storage and startup log capture.
        app = FastAPI()
        config = settings(OBJECT_STORAGE_LOCAL_ROOT=tmp_path)
        # When: startup initializes and probes the actual filesystem.
        with caplog.at_level("INFO", logger="uvicorn"):
            async with object_storage_lifespan(app, config):
                assert list(tmp_path.iterdir()) == []
        # Then: success identifies only the provider, not sensitive paths or keys.
        assert "startup check succeeded (provider=local)" in caplog.text
        assert str(tmp_path) not in caplog.text
        assert "test-secret" not in caplog.text

    asyncio.run(scenario())


def test_failed_startup_probe_closes_client_and_aborts(monkeypatch, caplog):
    """Scenario: bucket denial prevents startup and closes the selected provider."""

    async def scenario():
        # Given: a real SDK client returning denied bucket access.
        config = settings(
            OBJECT_STORAGE_PROVIDER="r2", OBJECT_STORAGE_S3_ENDPOINT_URL="https://example.com"
        )
        client = create_s3_client(config)
        storage = S3ObjectStorage(client, "objects", 100)
        from unittest.mock import AsyncMock

        monkeypatch.setattr(
            "app.core.object_storage.create_object_storage", AsyncMock(return_value=storage)
        )
        app = FastAPI()
        with Stubber(client) as stub:
            stub.add_client_error(
                "head_bucket",
                service_error_code="AccessDenied",
                service_message="secret-vendor-message",
                http_status_code=403,
                expected_params={"Bucket": "objects"},
            )
            # When: the lifespan performs the required bucket probe.
            with caplog.at_level("INFO", logger="uvicorn"), pytest.raises(StorageError):
                async with object_storage_lifespan(app, config):
                    pytest.fail("startup must not continue")
            stub.assert_no_pending_responses()
        # Then: only safe failure evidence remains; resources are closed.
        assert storage._closed
        assert not hasattr(app.state, "object_storage")
        assert "startup check failed (provider=r2, code=access_denied)" in caplog.text
        assert "secret-vendor-message" not in caplog.text
        assert "startup check succeeded" not in caplog.text

    asyncio.run(scenario())


def test_s3_startup_check_is_read_only():
    """Scenario: successful remote startup checks the existing bucket without writes."""

    async def scenario():
        # Given: one expected read-only SDK operation.
        client = create_s3_client(settings(OBJECT_STORAGE_PROVIDER="s3"))
        storage = S3ObjectStorage(client, "objects", 100)
        with Stubber(client) as stub:
            stub.add_response("head_bucket", {}, {"Bucket": "objects"})
            # When/Then: the connection check consumes exactly that operation.
            await storage.check_connection()
            stub.assert_no_pending_responses()
        await storage.close()

    asyncio.run(scenario())


def test_r2_endpoint_rejects_bucket_path_with_actionable_message():
    """Scenario: a pasted R2 bucket URL is rejected before SDK duplicates its path."""
    # Given: the bucket appears in both the endpoint URL and the bucket setting.
    # When/Then: validation identifies the configuration error without exposing the URL.
    with pytest.raises(ValueError, match="without a bucket/path") as error:
        settings(
            OBJECT_STORAGE_PROVIDER="r2",
            OBJECT_STORAGE_S3_ENDPOINT_URL="https://private-account.r2.cloudflarestorage.com/objects",
        )
    assert "private-account" not in str(error.value)
