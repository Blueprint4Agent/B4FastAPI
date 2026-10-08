"""Confirmed lifecycle delivery is durable, private and selectively enabled."""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select

from app.core.config.settings import SETTINGS
from app.core.db.session import get_db
from app.core.error.billing_exception import BillingException
from app.models.notification import Notification, Notifications
from app.services import notifications
from app.services.billing_notifications import BillingNotificationService


def test_outbox_deduplicates_encrypts_and_erases_after_delivery(integration_client, monkeypatch):
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    publish = AsyncMock(side_effect=RuntimeError("offline"))
    send = AsyncMock()
    monkeypatch.setattr(notifications.MAIL_QUEUE_SERVICE, "wake_lifecycle", publish)
    monkeypatch.setattr(notifications.MAIL_SERVICE, "send_lifecycle_email", send)

    async def scenario():
        for _ in range(2):
            await notifications.queue_notification(
                "deleted:1", "account_deleted", email="a@example.com", name="User", language="ko"
            )
        async with get_db() as db:
            rows = list((await db.scalars(select(Notification))).all())
            assert len(rows) == 1
            assert "a@example.com" not in rows[0].payload
        await notifications.deliver_notifications()
        await notifications.deliver_notifications()
        send.assert_awaited_once()
        assert send.call_args.kwargs["language"] == "ko"
        async with get_db() as db:
            row = await db.get(Notification, rows[0].id)
            assert row.state == "sent" and row.payload is None

    asyncio.run(scenario())


def test_claim_excludes_other_workers_and_expired_payloads(integration_client):
    async def scenario():
        row = notifications.notification_row(
            "lease", "account_deleted", email="a@example.com", name="A"
        )
        await Notifications.add(row)
        claimed = await Notifications.claim()
        assert claimed is not None
        assert await Notifications.claim() is None
        await Notifications.finish(claimed, state="pending", error="delivery_failed")
        assert await Notifications.claim() is None  # backoff
        expired = notifications.notification_row(
            "expired", "account_deleted", email="a@example.com", name="A"
        )
        expired.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await Notifications.add(expired)
        assert await Notifications.claim() is None
        async with get_db() as db:
            assert (await db.get(Notification, expired.id)).payload is None

    asyncio.run(scenario())


def test_disabled_mail_has_no_publication(monkeypatch):
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    publish = AsyncMock()
    monkeypatch.setattr(notifications.MAIL_QUEUE_SERVICE, "wake_lifecycle", publish)
    asyncio.run(
        notifications.queue_notification(
            "disabled", "account_deleted", email="a@example.com", name="A"
        )
    )
    publish.assert_not_called()


def test_signed_webhook_rejects_tampering_and_ignores_failure_renewal(monkeypatch, sample_user):
    monkeypatch.setattr(SETTINGS, "STRIPE_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "STRIPE_SECRET_KEY", "sk_test_fixture")
    monkeypatch.setattr(SETTINGS, "STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(
        "app.services.billing_notifications.BillingService.sync_subscription", AsyncMock()
    )
    queue = AsyncMock()
    monkeypatch.setattr("app.services.billing_notifications.queue_notification", queue)
    monkeypatch.setattr(
        "app.services.billing_notifications.BillingCustomers.owner",
        AsyncMock(return_value=sample_user),
    )

    async def scenario():
        for kind in ["invoice.payment_failed", "invoice.paid"]:
            payload = json.dumps(
                {
                    "id": "evt_fixture",
                    "type": kind,
                    "livemode": False,
                    "data": {
                        "object": {
                            "customer": "cus_fixture",
                            "status": "paid",
                            "billing_reason": "subscription_cycle",
                        }
                    },
                }
            ).encode()
            stamp = str(int(time.time()))
            signature = hmac.new(
                b"whsec_fixture", stamp.encode() + b"." + payload, hashlib.sha256
            ).hexdigest()
            header = f"t={stamp},v1={signature}"
            await BillingNotificationService().receive(payload, header)
            with pytest.raises(BillingException):
                await BillingNotificationService().receive(payload + b" ", header)
        queue.assert_not_called()

    asyncio.run(scenario())
