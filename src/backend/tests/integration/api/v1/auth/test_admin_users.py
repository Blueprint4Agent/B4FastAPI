import asyncio
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.db.session import get_db
from app.manage_user_role import change_role
from app.models.user import AuthIdentity, User, UserRole
from tests.fixtures.payload_data import build_login_payload, build_signup_payload


@pytest.mark.primary_data
def test_admin_directory_access_filters_and_login_metadata(integration_client):
    """Scenario: only admins see a paginated directory with the latest linked-provider login."""
    # Given: two users, one promoted admin, and linked provider metadata.
    client = integration_client
    endpoint = "/api/v1/auth/admin/users"
    assert client.get(endpoint).status_code == 401
    for email in ("admin@example.com", "member@example.com"):
        assert (
            client.post("/api/v1/auth/signup", json=build_signup_payload(email=email)).status_code
            == 200
        )
    member_login = client.post(
        "/api/v1/auth/login", json=build_login_payload(email="member@example.com")
    )
    member_headers = {"Authorization": f"Bearer {member_login.json()['access_token']}"}
    assert client.get(endpoint, headers=member_headers).status_code == 403
    asyncio.run(change_role("admin@example.com", UserRole.ADMIN))
    login = client.post("/api/v1/auth/login", json=build_login_payload(email="admin@example.com"))
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    async def seed_metadata():
        async with get_db() as db:
            user = await db.scalar(select(User).where(User.email == "member@example.com"))
            user.is_active = False
            user.name = "Member 100%"
            identities = (
                await db.scalars(select(AuthIdentity).where(AuthIdentity.user_id == user.id))
            ).all()
            identities[0].last_login_at = datetime(2026, 1, 1, tzinfo=UTC)
            db.add(
                AuthIdentity(
                    user_id=user.id,
                    provider="google",
                    identifier="linked-google",
                    last_login_at=datetime(2026, 2, 1, tzinfo=UTC),
                    last_login_ip="192.0.2.1",
                    last_login_user_agent="private-agent",
                )
            )
            await db.commit()

    asyncio.run(seed_metadata())
    # When: fetching a single-page slice, then literal search and role/status filters.
    result = client.get(endpoint, headers=headers, params={"page_size": 1}).json()
    assert result["total"] == 2
    assert len(result["items"]) == 1
    assert result["summary"] == {"total_users": 2, "active_users": 1, "admin_users": 1}
    member = result["items"][0]
    assert member["email"] == "member@example.com"
    assert member["login_providers"] == ["email", "google"]
    assert member["last_login_at"].startswith("2026-02-01")
    assert set(member) == {
        "id",
        "email",
        "name",
        "role",
        "is_active",
        "is_verified",
        "created_at",
        "last_login_at",
        "login_providers",
    }
    filtered = client.get(
        endpoint, headers=headers, params={"search": "100%", "role": "user", "is_active": False}
    ).json()
    assert filtered["total"] == 1
    assert (
        client.get(endpoint, headers=headers, params={"search": "no-match"}).json()["items"] == []
    )
    assert client.get(endpoint, headers=headers, params={"role": "admin"}).json()["total"] == 1
    assert (
        client.get(endpoint, headers=headers, params={"page": 3, "page_size": 1}).json()["items"]
        == []
    )
    # Then: bounded pagination/filter validation rejects malformed queries.
    for params in ({"page": 0}, {"page_size": 101}, {"role": "owner"}, {"search": "x" * 201}):
        assert client.get(endpoint, headers=headers, params=params).status_code == 422
