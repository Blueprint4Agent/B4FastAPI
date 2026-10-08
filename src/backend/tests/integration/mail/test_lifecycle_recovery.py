"""Real DB lifecycle recovery without an external broker or SMTP server."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, update

from app.core.config.settings import SETTINGS
from app.core.db.session import get_db
from app.manage_notifications import retry_notification
from app.models.notification import Notification, Notifications
from app.services import notifications

pytestmark = pytest.mark.primary_data


async def make_notice(key="recovery"):
    row = notifications.notification_row(
        key, "account_deleted", email="private@example.com", name="Private User", language="ko"
    )
    await Notifications.add(row)
    return row


async def expire_lease(row):
    async with get_db() as db:
        await db.execute(
            update(Notification)
            .where(Notification.id == row.id)
            .values(leased_until=datetime.now(UTC) - timedelta(seconds=1))
        )
        await db.commit()


def test_abandoned_worker_claims_exhaust_budget_and_reject_stale_completion(integration_client):
    """Scenario: repeated worker crashes stop after five claims and cannot be completed by stale workers."""

    async def scenario():
        # Given: retained notification with crashed workers that never finish.
        await make_notice()
        first = None
        for attempt in range(1, 6):
            row = await Notifications.claim()
            assert row.attempts == attempt
            first = first or row
            await expire_lease(row)
        # When: the scanner recovers the fifth abandoned claim.
        assert await Notifications.claim() is None
        await Notifications.finish(first, state="sent")
        # Then: it remains terminal and inspectable without recipient/payload exposure.
        failures = await Notifications.failures()
        assert len(failures) == 1
        assert failures[0]["state"] == "failed"
        assert failures[0]["error"] == "delivery_unconfirmed"
        assert failures[0]["attempts"] == 5
        assert "payload" not in failures[0] and "email" not in failures[0]
        assert "private@example.com" not in json.dumps(failures, default=str)

    asyncio.run(scenario())


def test_smtp_budget_manual_retry_and_success_erasure(integration_client, monkeypatch, caplog):
    """Scenario: five SMTP failures persist, explicit operator retry keeps expiry and can recover."""
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    send = AsyncMock(side_effect=RuntimeError("SMTP includes private@example.com"))
    monkeypatch.setattr(notifications.MAIL_SERVICE, "send_lifecycle_email", send)

    async def scenario():
        # Given: a provider which fails repeatedly.
        original = await make_notice()
        for _ in range(5):
            await notifications.deliver_notifications()
            async with get_db() as db:
                await db.execute(update(Notification).values(available_at=datetime.now(UTC)))
                await db.commit()
        await notifications.deliver_notifications()
        assert send.await_count == 5
        assert (await Notifications.failures())[0]["error"] == "delivery_failed"
        # When: an explicit retry is requested after provider repair.
        assert await retry_notification(original.id)
        assert not await retry_notification(original.id)
        async with get_db() as db:
            stored = await db.get(Notification, original.id)
            assert stored.expires_at.replace(tzinfo=UTC) == original.expires_at
        send.side_effect = None
        await notifications.deliver_notifications()
        # Then: no recipient remains and terminal success cannot be retried.
        async with get_db() as db:
            stored = await db.get(Notification, original.id)
            assert stored.state == "sent" and stored.payload is None
        assert not await retry_notification(original.id)

    asyncio.run(scenario())
    assert "private@example.com" not in caplog.text
    assert "Lifecycle mail retry requested" in caplog.text


def test_expiry_and_disabled_mode_prevent_recovery(integration_client, monkeypatch):
    """Scenario: operators cannot revive expired recipients or requeue while email is disabled."""

    async def scenario():
        # Given: a retained terminal failure.
        row = await make_notice()
        async with get_db() as db:
            await db.execute(update(Notification).values(state="failed"))
            await db.commit()
        # When/Then: disabled email and invalid identifiers reject before mutation.
        monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
        with pytest.raises(ValueError):
            await retry_notification(row.id)
        with pytest.raises(ValueError):
            await retry_notification("invalid")
        monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
        async with get_db() as db:
            await db.execute(
                update(Notification).values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
            )
            await db.commit()
        assert not await retry_notification(row.id)
        assert await Notifications.claim() is None
        async with get_db() as db:
            expired = await db.get(Notification, row.id)
            assert expired.state == "expired" and expired.payload is None
        with pytest.raises(ValueError):
            await Notifications.failures(101)

    asyncio.run(scenario())


def test_disabled_delivery_erases_without_smtp(integration_client, monkeypatch):
    """Scenario: disabling email after reservation preserves domain success and erases recipients."""
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    send = AsyncMock()
    monkeypatch.setattr(notifications.MAIL_SERVICE, "send_lifecycle_email", send)

    async def scenario():
        # Given: a notification created before email was disabled.
        row = await make_notice()
        # When: the worker scans the durable outbox.
        await notifications.deliver_notifications()
        # Then: there is no SMTP side effect or retained address.
        send.assert_not_called()
        async with get_db() as db:
            stored = await db.get(Notification, row.id)
            assert stored.state == "skipped" and stored.payload is None

    asyncio.run(scenario())


@pytest.mark.parametrize("fail_commit", [False, True])
def test_deletion_notice_commits_with_user_removal_and_survives_broker_failure(
    integration_client, monkeypatch, fail_commit
):
    """Scenario: deletion and encrypted recipient commit together; broker outage cannot undo deletion."""
    from app.models.user import User
    from tests.integration.api.v1.billing.test_billing_integration import login

    # Given: a real account with a validated deletion proof, no outbound broker.
    headers = login(integration_client)
    user = integration_client.get("/api/v1/auth/me", headers=headers).json()
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr("app.services.auth.consume_deletion_code", AsyncMock(return_value=True))
    monkeypatch.setattr(
        notifications.MAIL_QUEUE_SERVICE,
        "wake_lifecycle",
        AsyncMock(side_effect=RuntimeError("offline")),
    )
    key = f"account-deleted:{user['id']}"
    if fail_commit:
        # A conflicting outbox row forces the actual DB transaction to roll back.
        asyncio.run(make_notice(key))
    # When: confirmed deletion is requested in Korean.
    response = integration_client.request(
        "DELETE",
        "/api/v1/auth/me",
        headers={**headers, "Accept-Language": "ko-KR"},
        json={"email": user["email"], "code": "123456"},
    )
    assert response.status_code == (500 if fail_commit else 204)

    # Then: either both deletion and notice commit or neither does.
    async def inspect():
        async with get_db() as db:
            present = await db.get(User, user["id"])
            row = await db.scalar(select(Notification))
            assert (present is not None) == fail_commit
            if not fail_commit:
                assert row.kind == "account_deleted" and row.state == "pending"
                assert user["email"] not in row.payload
                payload = json.loads(notifications.cipher().decrypt(row.payload.encode()))
                assert payload["email"] == user["email"] and payload["language"] == "ko"

    asyncio.run(inspect())


def test_previous_dedupe_key_survives_event_key_upgrade(integration_client, monkeypatch):
    """Scenario: delivery records written by the previous version suppress historical event replay."""
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)

    async def scenario():
        # Given: a notification from the previous timestamp/price-key release.
        await notifications.queue_notification(
            "old-key", "plan_changed", email="a@example.com", name="A", language="en", plan="Plus"
        )
        # When: the new event-ID policy processes the same historical event.
        await notifications.queue_notification(
            "new-event-key",
            "plan_changed",
            previous_key="old-key",
            email="a@example.com",
            name="A",
            language="en",
            plan="Plus",
        )
        # Then: only the existing reservation remains.
        async with get_db() as db:
            assert len(list((await db.scalars(select(Notification))).all())) == 1

    asyncio.run(scenario())
