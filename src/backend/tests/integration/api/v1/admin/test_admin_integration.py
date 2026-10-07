import asyncio

import pytest
from sqlalchemy import select

from app.core.db.session import get_session_factory
from app.models.user import User
from tests.fixtures.payload_data import build_login_payload, build_signup_payload


@pytest.mark.primary_data
def test_status_revoked_after_database_demotion(integration_client):
    """Scenario: an existing admin token loses status access immediately after demotion."""
    # Given: a real account and authenticated token on an empty database.
    integration_client.post("/api/v1/auth/signup", json=build_signup_payload())
    login = integration_client.post("/api/v1/auth/login", json=build_login_payload()).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}

    async def change_role(role):
        async with get_session_factory()() as session:
            user = await session.scalar(select(User).where(User.id == login["user"]["id"]))
            user.role = role
            await session.commit()

    asyncio.run(change_role("admin"))
    # When: the admin reads actual database/cache health.
    response = integration_client.get("/api/v1/admin/status", headers=headers)
    # Then: success reflects the configured SQLite database.
    assert response.status_code == 200
    assert response.json()["connections"][1]["technology"] == "sqlite"
    # When / Then: demotion is authoritative even with the same token.
    asyncio.run(change_role("manager"))
    assert integration_client.get("/api/v1/admin/status", headers=headers).status_code == 403
