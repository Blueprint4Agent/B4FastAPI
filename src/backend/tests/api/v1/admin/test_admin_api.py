import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import SETTINGS
from app.core.observability import health
from app.deps import get_current_user
from app.main import register_exception_handlers
from app.models.user import UserRole
from app.routers.v1.admin import router
from app.services.admin import AdminService

pytestmark = pytest.mark.api_test


@pytest.fixture(autouse=True)
def isolated_provider_checks(monkeypatch):
    from app.core.observability.integration_health import IntegrationHealth

    async def healthy():
        return None

    monkeypatch.setattr("app.services.admin.INTEGRATION_HEALTH", IntegrationHealth())
    monkeypatch.setattr("app.services.admin.MAIL_SERVICE.check_connection", healthy)


@pytest.mark.parametrize("role,expected", [("admin", 200), ("manager", 403), ("user", 403)])
def test_status_role_contract(monkeypatch, role, expected):
    """Scenario: only current administrators can inspect safe effective configuration."""
    # Given: the real role dependency and a safe dependency probe.
    from types import SimpleNamespace

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/admin")
    from unittest.mock import AsyncMock

    app.state.object_storage = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1, role=UserRole(role))

    async def healthy():
        return {
            name: health.DependencyCheck(status="ok", latency_ms=1)
            for name in ("database", "redis")
        }

    monkeypatch.setattr("app.services.admin.check_dependencies", healthy)
    # When: the protected read endpoint is requested.
    response = TestClient(app).get("/api/v1/admin/status")
    # Then: the role guard and no-store successful response are enforced.
    assert response.status_code == expected
    if expected == 200:
        assert response.headers["cache-control"] == "no-store"
        payload = response.json()
        assert payload["environment"]["admin_access"] == "admin_only"
        assert "DATABASE_URL" not in response.text
        assert "STRIPE_SECRET_KEY" not in response.text


def test_status_requires_authentication():
    """Scenario: anonymous requests cannot inspect server configuration."""
    # Given: an endpoint without dependency overrides.
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/admin")
    # When / Then: missing credentials are rejected.
    assert TestClient(app).get("/api/v1/admin/status").status_code == 401


def test_dependency_timeout_and_failure_are_isolated(monkeypatch):
    """Scenario: a stalled database does not hide the cache failure or hang readiness."""

    # Given: one slow probe and one failed probe.
    async def slow():
        await asyncio.sleep(1)
        return "ok"

    async def failed():
        raise RuntimeError("private-connection-string")

    monkeypatch.setattr(health, "PROBE_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(health, "check_database", slow)
    monkeypatch.setattr(health, "check_redis", failed)
    # When: the shared readiness check runs.
    result = asyncio.run(health.get_readiness())
    # Then: each result is bounded and sanitized.
    assert result.status == "degraded"
    assert result.checks == {"database": "timeout", "redis": "failed"}


def test_environment_effective_flags(monkeypatch):
    """Scenario: effective feature modes do not leak provider credentials."""
    # Given: development with login and payment disabled.
    monkeypatch.setattr(SETTINGS, "APP_MODE", "development")
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "OAUTH_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_ENABLED", False)
    monkeypatch.setattr(SETTINGS, "STRIPE_SECRET_KEY", "private-value-never-expose")

    async def healthy():
        return {
            name: health.DependencyCheck(status="ok", latency_ms=1)
            for name in ("database", "redis")
        }

    monkeypatch.setattr("app.services.admin.check_dependencies", healthy)
    # When: projecting the safe environment allowlist.
    result = asyncio.run(AdminService().status())
    # Then: gates are effective and secrets never enter the schema.
    assert result.environment.developer_enabled
    assert not result.environment.oauth_enabled
    assert result.environment.oauth_providers == []
    assert result.environment.billing_mode == "disabled"
    assert result.environment_values.STRIPE_ENABLED is False
    assert result.environment_values.APP_MODE == "development"
    assert "private-value" not in result.model_dump_json()


def test_startup_evidence_is_not_inferred_from_enabled_flags(monkeypatch):
    """Scenario: enabled providers are not reported healthy without successful startup evidence."""
    from app.core.observability.startup_checks import STARTUP_CHECKS, record_startup_check

    # Given: no completed checks in a fresh process.
    monkeypatch.setattr("app.services.admin.STARTUP_CHECKS", {})

    async def healthy():
        return {
            name: health.DependencyCheck(status="ok", latency_ms=1)
            for name in ("database", "redis")
        }

    monkeypatch.setattr("app.services.admin.check_dependencies", healthy)
    # When / Then: unknown evidence remains unverified, regardless of configuration.
    result = asyncio.run(AdminService().status())
    assert all(check.status == "unverified" for check in result.startup_checks.values())
    # Given: a completed SMTP handshake and configuration-only OAuth check.
    monkeypatch.setattr("app.services.admin.STARTUP_CHECKS", STARTUP_CHECKS)
    previous = STARTUP_CHECKS.copy()
    try:
        record_startup_check("email", "ok")
        record_startup_check("oauth", "configured")
        # When / Then: the different verification levels and their times are preserved.
        result = asyncio.run(AdminService().status())
        assert result.startup_checks["email"].status == "ok"
        assert result.startup_checks["email"].checked_at is not None
        assert result.startup_checks["oauth"].status == "configured"
    finally:
        STARTUP_CHECKS.clear()
        STARTUP_CHECKS.update(previous)


def test_database_address_excludes_credentials_and_options(monkeypatch):
    """Scenario: administrators see the actual database host/port without its secret DSN."""
    from types import SimpleNamespace

    from sqlalchemy.engine import make_url

    # Given: a network database URL containing private credentials and options.
    engine = SimpleNamespace(
        dialect=SimpleNamespace(name="postgresql"),
        url=make_url(
            "postgresql+asyncpg://private-user:private-password@db.internal:5433/private-name?sslmode=require"
        ),
    )
    monkeypatch.setattr("app.services.admin.get_engine", lambda: engine)
    monkeypatch.setattr(SETTINGS, "REDIS_IN_MEMORY", False)
    monkeypatch.setattr(
        SETTINGS, "REDIS_URL", "redis://private-user:private-password@cache.internal:6380/2"
    )

    async def healthy():
        return {
            name: health.DependencyCheck(status="ok", latency_ms=1)
            for name in ("database", "redis")
        }

    monkeypatch.setattr("app.services.admin.check_dependencies", healthy)
    # When: returning the safe status projection.
    result = asyncio.run(AdminService().status())
    # Then: address metadata is separate from credentials/database name/query options.
    assert result.connections[1].host == "db.internal"
    assert result.connections[1].port == 5433
    assert result.connections[2].host == "cache.internal"
    assert result.connections[2].port == 6380
    assert "private-" not in result.model_dump_json()
    assert "sslmode" not in result.model_dump_json()


@pytest.mark.parametrize(
    "provider,endpoint,transport,port",
    [
        ("local", "", "filesystem", None),
        ("s3", "", "https", 443),
        (
            "r2",
            "https://private-account.example:8443/private-bucket?secret=private-token",
            "https",
            8443,
        ),
        ("supabase", "https://private-project.example/storage/v1/s3", "https", 443),
        ("s3", "http://private-host:9000", "http", 9000),
    ],
)
def test_storage_metadata_allowlist_and_cached_probe(
    monkeypatch, provider, endpoint, transport, port
):
    """Only safe connection metadata leaves the admin service; repeated reads share a probe."""
    from unittest.mock import AsyncMock

    monkeypatch.setattr(SETTINGS, "OBJECT_STORAGE_PROVIDER", provider)
    monkeypatch.setattr(SETTINGS, "OBJECT_STORAGE_S3_ENDPOINT_URL", endpoint)
    monkeypatch.setattr(SETTINGS, "OBJECT_STORAGE_S3_BUCKET", "private-bucket")
    monkeypatch.setattr(SETTINGS, "OBJECT_STORAGE_S3_ACCESS_KEY_ID", "private-access-key")
    storage = AsyncMock()

    async def run():
        first = await AdminService().status(storage)
        second = await AdminService().status(storage)
        return first, second

    first, second = asyncio.run(run())
    item = first.connections[-1]
    assert item.id == "object_storage"
    assert item.technology == provider
    assert item.transport == transport
    assert item.port == port
    assert item.host is None
    assert item.status == "ok"
    assert item.latency_ms is not None
    assert item.checked_at == second.connections[-1].checked_at
    assert "private-" not in first.model_dump_json()
    storage.check_connection.assert_awaited_once()


def test_storage_failure_is_sanitized_and_degrades_status(monkeypatch):
    """An unavailable storage provider leaves all other dependency rows observable."""
    from unittest.mock import AsyncMock

    storage = AsyncMock()
    storage.check_connection.side_effect = RuntimeError("private-token-and-endpoint")
    result = asyncio.run(AdminService().status(storage))
    assert result.status == "degraded"
    assert result.connections[-1].status == "failed"
    assert len(result.connections) == 4
    assert "private-token" not in result.model_dump_json()
