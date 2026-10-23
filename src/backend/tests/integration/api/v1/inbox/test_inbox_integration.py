import asyncio
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import delete, select

from app.core.db.session import get_db
from app.models.inbox import InboxNotification, add_inbox_notification
from app.models.user import User
from tests.fixtures.payload_data import build_login_payload, build_signup_payload

pytestmark = pytest.mark.primary_data


@pytest.mark.parametrize("provider", ["email", "google"])
def test_account_welcome_uses_configured_brand(integration_client, monkeypatch, provider):
    # Given: isolated persistence and a configured project identity.
    from app.core.config.settings import SETTINGS
    from app.models.user import UserRepository

    monkeypatch.setattr(SETTINGS, "EMAIL_BRAND_NAME", "Acme")

    async def create_and_read():
        repository = UserRepository()
        if provider == "email":
            user = await repository.create_signup_user(
                email="brand@example.com", name="Example", password_hash="fixture-hash"
            )
        else:
            user = await repository.create_oauth_user(
                email="brand@example.com",
                name="Example",
                provider=provider,
                identifier="fixture-id",
            )
        async with get_db() as db:
            return await db.scalar(
                select(InboxNotification).where(InboxNotification.user_id == user.id)
            )

    # When: either creation path commits its existing welcome notification.
    welcome = asyncio.run(create_and_read())
    # Then: raw storage/API text is branded independently of frontend translation.
    assert welcome.title == "Welcome to Acme"
    assert welcome.body == "Your account is ready. Welcome to Acme."


def test_inbox_ownership_read_idempotency_and_high_water(integration_client, monkeypatch):
    """Scenario: even an admin reads only their inbox and bulk reads spare new arrivals."""
    client = integration_client
    assert client.get("/api/v1/inbox").status_code == 401
    headers = []
    for email in ["owner@example.com", "other@example.com"]:
        assert (
            client.post("/api/v1/auth/signup", json=build_signup_payload(email=email)).status_code
            == 200
        )
        login = client.post("/api/v1/auth/login", json=build_login_payload(email=email)).json()
        headers.append({"Authorization": "Bearer " + login["access_token"]})

    async def seed():
        async with get_db() as db:
            welcomes = (await db.scalars(select(InboxNotification))).all()
            assert len(welcomes) == 2 and all(row.kind == "welcome" for row in welcomes)
            await db.execute(delete(InboxNotification))
            users = (await db.scalars(select(User).order_by(User.id))).all()
            users[1].role = "admin"
            for owner in users:
                await add_inbox_notification(
                    db, user_id=owner.id, kind="test", title="Update", body="Stored message"
                )
            await db.commit()
            return users[0].id

    owner = asyncio.run(seed())
    # Given: a committed record for each owner and best-effort realtime publication.
    publish = AsyncMock()
    monkeypatch.setattr("app.services.inbox.RealtimeService.publish_user_notification", publish)
    first = client.get("/api/v1/inbox", headers=headers[0])
    assert first.headers["cache-control"] == "no-store"
    data = first.json()
    assert data["total"] == 1 and data["summary"]["unread_count"] == 1
    key = data["items"][0]["id"]
    # When: another user, including an admin, guesses a private ID.
    assert client.post(f"/api/v1/inbox/{key}/read", headers=headers[1]).status_code == 404
    assert client.get("/api/v1/inbox", headers=headers[1]).json()["items"][0]["id"] != key
    # Then: repeat reads are idempotent and do not move read_at.
    a = client.post(f"/api/v1/inbox/{key}/read", headers=headers[0]).json()
    b = client.post(f"/api/v1/inbox/{key}/read", headers=headers[0]).json()
    assert a["read_at"] == b["read_at"]
    assert (
        client.get("/api/v1/inbox", params={"unread_only": True}, headers=headers[0]).json()[
            "items"
        ]
        == []
    )

    async def later():
        async with get_db() as db:
            await add_inbox_notification(
                db, user_id=owner, kind="test", title="New", body="Arrived after snapshot"
            )
            await db.commit()

    asyncio.run(later())
    result = client.post("/api/v1/inbox/read-all", headers=headers[0], json={"through_id": key})
    assert result.status_code == 200 and result.json()["unread_count"] == 1
    assert (
        client.post(
            "/api/v1/inbox/read-all", headers=headers[0], json={"through_id": -1}
        ).status_code
        == 422
    )
    assert publish.await_count == 3

    # Deleting an owner removes inbox contents, independent of browser state.
    async def delete_owner():
        async with get_db() as db:
            row = await db.get(User, owner)
            await db.delete(row)
            await db.commit()
            assert not (
                await db.scalars(
                    select(InboxNotification).where(InboxNotification.user_id == owner)
                )
            ).all()

    asyncio.run(delete_owner())


def test_confirmed_billing_inbox_without_email_is_deduplicated(integration_client, monkeypatch):
    from contextlib import asynccontextmanager
    from types import SimpleNamespace

    import stripe

    from app.core.config.settings import SETTINGS
    from app.models.user import Users
    from app.services.billing_notifications import BillingNotificationService

    client = integration_client
    email = "billing-inbox@example.com"
    assert (
        client.post("/api/v1/auth/signup", json=build_signup_payload(email=email)).status_code
        == 200
    )
    monkeypatch.setattr(SETTINGS, "STRIPE_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_SECRET_KEY", "sk_test_fixture")
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    obj = {
        "id": "sub_fixture",
        "customer": "cus_fixture",
        "status": "active",
        "livemode": False,
        "items": {"data": [{"price": {"id": "price_MONTHLY_KRW"}}]},
    }
    sub = stripe.StripeObject.construct_from(obj, None)
    provider = SimpleNamespace(
        v1=SimpleNamespace(
            subscriptions=SimpleNamespace(retrieve_async=AsyncMock(return_value=sub))
        )
    )

    @asynccontextmanager
    async def context(self):
        yield provider

    monkeypatch.setattr("app.services.billing_notifications.BillingService._provider", context)
    monkeypatch.setattr(
        "app.services.billing_notifications.BillingService.sync_subscription", AsyncMock()
    )
    publish = AsyncMock()
    monkeypatch.setattr("app.services.inbox.RealtimeService.publish_user_notification", publish)

    async def scenario():
        user = await Users.get_auth_user_by_email(email)
        monkeypatch.setattr(
            "app.services.billing_notifications.BillingCustomers.owner",
            AsyncMock(return_value=user),
        )
        payload = {
            "id": "evt_plan",
            "type": "customer.subscription.updated",
            "livemode": False,
            "data": {
                "object": obj,
                "previous_attributes": {"items": {"data": [{"price": {"id": "price_old"}}]}},
            },
        }
        monkeypatch.setattr(
            stripe.Webhook,
            "construct_event",
            lambda *args: stripe.StripeObject.construct_from(payload, None),
        )
        service = BillingNotificationService()
        await service.receive(b"fixture", "fixture")
        await service.receive(b"fixture", "fixture")
        async with get_db() as db:
            rows = (
                await db.scalars(
                    select(InboxNotification).where(InboxNotification.user_id == user.id)
                )
            ).all()
            assert [row.kind for row in rows] == ["welcome", "plan_changed"]
            assert rows[-1].body == "Plus"
        assert publish.await_count == 1
        # Pending changes must never be reported as applied.
        payload["id"] = "evt_pending"
        obj["pending_update"] = {"expires_at": 123}
        await service.receive(b"fixture", "fixture")
        assert publish.await_count == 1

    asyncio.run(scenario())


def test_selected_actions_are_private_and_deleted_delivery_stays_deduplicated(
    integration_client, monkeypatch
):
    from app.models.inbox import INBOX
    from app.models.user import Users

    client = integration_client
    monkeypatch.setattr("app.services.inbox.RealtimeService.publish_user_notification", AsyncMock())
    headers = []
    for email in ["delete-owner@example.com", "delete-other@example.com"]:
        client.post("/api/v1/auth/signup", json=build_signup_payload(email=email))
        token = client.post("/api/v1/auth/login", json=build_login_payload(email=email)).json()[
            "access_token"
        ]
        headers.append({"Authorization": f"Bearer {token}"})

    async def seed():
        owner = await Users.get_auth_user_by_email("delete-owner@example.com")
        await INBOX.deliver(
            key="billing-fixture",
            user_id=owner.id,
            kind="plan_changed",
            title="Plan changed",
            body="Private content",
            action_path="/settings?section=billing",
        )
        return owner.id

    owner_id = asyncio.run(seed())
    own = client.get("/api/v1/inbox", headers=headers[0]).json()["items"][0]["id"]
    other = client.get("/api/v1/inbox", headers=headers[1]).json()["items"][0]["id"]
    payload = {"notification_ids": [own, other]}
    assert (
        client.post("/api/v1/inbox/read-selected", headers=headers[0], json=payload).status_code
        == 200
    )
    assert client.get("/api/v1/inbox", headers=headers[1]).json()["items"][0]["read_at"] is None
    deleted = client.request("DELETE", "/api/v1/inbox/selected", headers=headers[0], json=payload)
    assert deleted.status_code == 200 and deleted.headers["cache-control"] == "no-store"
    assert client.post(f"/api/v1/inbox/{own}/read", headers=headers[0]).status_code == 404
    assert client.get("/api/v1/inbox", headers=headers[1]).json()["total"] == 1
    assert (
        client.request(
            "DELETE", "/api/v1/inbox/selected", headers=headers[0], json=payload
        ).status_code
        == 200
    )
    assert (
        client.request(
            "DELETE", "/api/v1/inbox/selected", headers=headers[0], json={"notification_ids": []}
        ).status_code
        == 422
    )
    assert client.request("DELETE", "/api/v1/inbox/selected", json=payload).status_code == 401

    async def retained_key():
        async with get_db() as db:
            row = await db.get(InboxNotification, own)
            assert row.deleted_at is not None
            assert row.title == row.body == "" and row.action_path is None
        assert not await INBOX.deliver(
            key="billing-fixture",
            user_id=owner_id,
            kind="plan_changed",
            title="Replay",
            body="Do not recreate",
            action_path="/settings?section=billing",
        )

    asyncio.run(retained_key())
