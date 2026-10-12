import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.core.config import SETTINGS
from app.core.db.session import get_db
from app.models.user import User
from app.services.admin import AdminDemoSnapshots, AdminService
from tests.fixtures.payload_data import build_signup_payload

pytestmark = pytest.mark.primary_data


def test_public_demo_masks_identity_and_searches_only_aliases(integration_client, monkeypatch):
    """Scenario: public demo uses real counts without disclosing or searching private identity."""
    # Given: an enabled demo and real accounts with private names and email addresses.
    monkeypatch.setattr(SETTINGS, "DEMO_ENABLED", True)
    client = integration_client
    assert client.get("/config").json()["demo_enabled"] is True
    for email in ("private-one@example.com", "private-two@example.com"):
        assert (
            client.post("/api/v1/auth/signup", json=build_signup_payload(email=email)).status_code
            == 200
        )

    async def update():
        async with get_db() as db:
            users = (await db.scalars(select(User).order_by(User.id))).all()
            users[0].name = "Private Person"
            users[0].role = "admin"
            users[1].is_active = False
            users[0].created_at = datetime(2026, 1, 3, 15, 21, tzinfo=UTC)
            await db.commit()
            return [user.id for user in users]

    ids = asyncio.run(update())
    endpoint = "/api/v1/admin/demo/users"
    # When: a guest reads, paginates, filters, and searches the directory.
    response = client.get(endpoint)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    payload = response.json()
    assert payload["summary"] == dict(total_users=2, active_users=1, admin_users=1, manager_users=0)
    assert payload["total"] == 2
    assert "private-one" not in response.text
    assert "private-two" not in response.text
    assert "Private Person" not in response.text
    for item in payload["items"]:
        assert item["id"] not in ids
        assert item["email"].endswith("@demo.invalid")
        assert "T00:00:00" in item["created_at"]
    alias = payload["items"][0]["email"]
    assert client.get(endpoint, params={"search": alias}).json()["total"] == 1
    assert client.get(endpoint, params={"search": "Private Person"}).json()["total"] == 0
    assert client.get(endpoint, params={"search": "private-one"}).json()["total"] == 0
    assert client.get(endpoint, params={"role": "admin"}).json()["total"] == 1
    assert client.get(endpoint, params={"is_active": False}).json()["total"] == 1
    assert len(client.get(endpoint, params={"page_size": 1}).json()["items"]) == 1
    assert client.get(endpoint, params={"page": 9, "page_size": 1}).json()["items"] == []
    # Then: private endpoints remain protected; turning the flag off closes even warm snapshots.
    assert client.get("/api/v1/admin/status").status_code == 401
    assert client.get("/api/v1/auth/admin/users").status_code == 401
    monkeypatch.setattr(SETTINGS, "DEMO_ENABLED", False)
    assert client.get(endpoint).status_code == 404
    assert client.get("/api/v1/admin/demo/status").status_code == 404
    assert client.get("/config").json()["demo_enabled"] is False


def test_demo_server_status_redacts_hosts_without_mutating_admin(monkeypatch):
    """Scenario: shared real health evidence is copied before public redaction."""
    # Given: real admin service output from mocked dependency probes.
    from app.core.observability.health import DependencyCheck

    monkeypatch.setattr(SETTINGS, "DEMO_ENABLED", True)
    monkeypatch.setattr("app.services.admin.DEMO_SNAPSHOTS", AdminDemoSnapshots())
    monkeypatch.setattr(
        "app.services.admin.check_dependencies",
        AsyncMock(
            return_value={
                "database": DependencyCheck(status="ok", latency_ms=4),
                "redis": DependencyCheck(status="failed", latency_ms=7),
            }
        ),
    )

    async def run():
        original = await AdminService().status()
        original.connections[1].host = "private-db.internal"
        original.connections[1].port = 5432
        probe = AsyncMock(return_value=original)
        monkeypatch.setattr(AdminService, "status", probe)
        # When: concurrent public requests inspect server health.
        first, second = await asyncio.gather(
            AdminService().demo_status(), AdminService().demo_status()
        )
        # Then: one probe supplies real statuses while private addresses remain admin-only.
        assert probe.await_count == 1
        assert first.status == original.status
        assert second.connections[1].status == original.connections[1].status
        assert all(item.host is None and item.port is None for item in first.connections)
        assert original.connections[1].host == "private-db.internal"
        assert "private-db" not in first.model_dump_json()

    asyncio.run(run())


def test_demo_status_is_public_but_off_switch_precedes_probe(integration_client, monkeypatch):
    """Scenario: visitors can read only the enabled demo endpoint, never the private route."""
    # Given: the real status projection with safely replaced dependency probes.
    from app.core.observability.health import DependencyCheck

    monkeypatch.setattr(SETTINGS, "DEMO_ENABLED", True)
    monkeypatch.setattr(
        "app.services.admin.check_dependencies",
        AsyncMock(
            return_value={
                "database": DependencyCheck(status="ok", latency_ms=2),
                "redis": DependencyCheck(status="ok", latency_ms=3),
            }
        ),
    )
    # When: an anonymous visitor requests the public status endpoint.
    response = integration_client.get("/api/v1/admin/demo/status")
    # Then: typed real health is returned without addresses or elevated authorization.
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert all(
        row["host"] is None and row["port"] is None for row in response.json()["connections"]
    )
    assert integration_client.get("/api/v1/admin/status").status_code == 401
    monkeypatch.setattr(SETTINGS, "DEMO_ENABLED", False)
    assert integration_client.get("/api/v1/admin/demo/status").status_code == 404


def test_demo_snapshot_failure_never_exposes_exception_or_stale_private_data(monkeypatch):
    """Scenario: failed projections return a typed safe error and are retried on next request."""
    from app.core.error.admin_exception import AdminException

    # Given: a projection that fails with a sensitive internal error message.
    async def run():
        snapshots = AdminDemoSnapshots()
        load = AsyncMock(side_effect=RuntimeError("private-db-credential"))
        # When: concurrent visitors encounter the failing projection.
        results = await asyncio.gather(
            snapshots.get("users", load), snapshots.get("users", load), return_exceptions=True
        )
        # Then: one attempt is shared and neither exception nor failed data is cached.
        assert load.await_count == 1
        assert all(isinstance(result, AdminException) for result in results)
        assert all("private-db-credential" not in str(result) for result in results)
        assert not snapshots.cache
        load.side_effect = None
        load.return_value = []
        assert await snapshots.get("users", load) == []
        assert load.await_count == 2
        await snapshots.reset()
        assert not snapshots.cache and not snapshots.pending

    asyncio.run(run())
