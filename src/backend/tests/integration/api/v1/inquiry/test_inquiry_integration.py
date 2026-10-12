import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.db.session import get_db
from app.models.user import User
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data


def test_private_inquiry_lifecycle_and_notifications(integration_client, monkeypatch):
    client = integration_client
    monkeypatch.setattr("app.services.inbox.RealtimeService.publish_user_notification", AsyncMock())
    headers = []
    for email in [
        "support-owner@example.com",
        "support-other@example.com",
        "support-admin@example.com",
    ]:
        assert (
            client.post("/api/v1/auth/signup", json=build_signup_payload(email=email)).status_code
            == 200
        )
        token = client.post("/api/v1/auth/login", json=build_login_payload(email=email)).json()[
            "access_token"
        ]
        headers.append({"Authorization": f"Bearer {token}"})

    async def roles():
        async with get_db() as db:
            users = (await db.scalars(select(User).order_by(User.id))).all()
            users[1].role = "manager"
            users[2].role = "admin"
            await db.commit()

    asyncio.run(roles())
    assert client.get("/api/v1/inquiries").status_code == 401
    form = {
        "subject": "Invoice question",
        "body": "Please check my plan.",
        "request_id": str(uuid4()),
    }
    created = client.post("/api/v1/inquiries", headers=headers[0], json=form)
    assert created.status_code == 200
    row = created.json()
    assert row["status"] == "open" and len(row["messages"]) == 1
    inquiry_id = row["id"]
    assert (
        client.post("/api/v1/inquiries", headers=headers[0], json=form).json()["id"] == inquiry_id
    )
    assert client.get("/api/v1/inquiries", headers=headers[0]).json()["total"] == 1
    assert client.get("/api/v1/inquiries", headers=headers[1]).json()["total"] == 0
    assert client.get(f"/api/v1/inquiries/{inquiry_id}", headers=headers[1]).status_code == 404
    assert client.get("/api/v1/inquiries/admin", headers=headers[1]).status_code == 403
    assert client.get("/api/v1/inquiries/admin", headers=headers[2]).json()["total"] == 1
    assert (
        client.get("/api/v1/inquiries/admin", headers=headers[2]).headers["cache-control"]
        == "no-store"
    )
    assert (
        client.get("/api/v1/inbox", headers=headers[2]).json()["items"][0]["kind"]
        == "inquiry_received"
    )
    reply = {"body": "Your plan is active.", "request_id": str(uuid4())}
    path = f"/api/v1/inquiries/{inquiry_id}/messages"
    assert client.post(path, headers=headers[1], json=reply).status_code == 404
    answer = client.post(path, headers=headers[2], json=reply)
    assert answer.status_code == 200 and answer.json()["messages"][-1]["author_role"] == "admin"
    assert len(client.post(path, headers=headers[2], json=reply).json()["messages"]) == 2
    assert (
        client.get("/api/v1/inbox", headers=headers[0]).json()["items"][0]["kind"]
        == "inquiry_reply"
    )
    status_path = f"/api/v1/inquiries/{inquiry_id}/status"
    assert (
        client.patch(status_path, headers=headers[0], json={"status": "closed"}).status_code == 403
    )
    assert (
        client.patch(status_path, headers=headers[2], json={"status": "closed"}).status_code == 200
    )
    assert (
        client.post(
            path, headers=headers[0], json={"body": "Again", "request_id": str(uuid4())}
        ).status_code
        == 409
    )
    assert (
        client.get("/api/v1/inquiries/admin?status=closed", headers=headers[2]).json()["total"] == 1
    )
    assert client.patch(status_path, headers=headers[2], json={"status": "open"}).status_code == 200
    assert (
        client.post(
            path, headers=headers[0], json={"body": "Thank you", "request_id": str(uuid4())}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/inquiries", headers=headers[0], json={**form, "subject": "  "}
        ).status_code
        == 422
    )
