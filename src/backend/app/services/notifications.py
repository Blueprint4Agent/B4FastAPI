"""Lifecycle event -> encrypted outbox -> bounded SMTP delivery."""

import base64
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Literal

from cryptography.fernet import Fernet

from app.core.celery.publisher import publish_task
from app.core.config.settings import SETTINGS
from app.core.mail.service import MAIL_SERVICE
from app.core.observability.logging import get_logger
from app.models.notification import Notification, Notifications

logger = get_logger("app.service.notifications")
NotificationKind = Literal["subscription_started", "plan_changed", "account_deleted"]


def cipher() -> Fernet:
    return Fernet(
        base64.urlsafe_b64encode(
            hashlib.sha256(b"mail-notification-v1:" + SETTINGS.SECRET_KEY.encode()).digest()
        )
    )


def notification_row(
    key: str, kind: NotificationKind, *, email: str, name: str, language: str = "en", plan: str = ""
) -> Notification:
    now = datetime.now(UTC)
    payload = (
        cipher()
        .encrypt(json.dumps(dict(email=email, name=name, language=language, plan=plan)).encode())
        .decode()
    )
    return Notification(
        id=hashlib.sha256(key.encode()).hexdigest(),
        kind=kind,
        payload=payload,
        state="pending",
        attempts=0,
        available_at=now,
        expires_at=now + timedelta(hours=72),
    )


async def wake_notifications() -> None:
    try:
        await publish_task("b4fastapi.notifications.drain", payload={})
    except Exception:
        # Beat will recover; do not undo the committed domain result.
        logger.warning("Notification wake-up unavailable; durable outbox retained.")


async def queue_notification(key: str, kind: NotificationKind, **payload: str) -> None:
    if not SETTINGS.EMAIL_ENABLED:
        return
    await Notifications.add(notification_row(key, kind, **payload))
    await wake_notifications()


async def deliver_notifications() -> None:
    for _ in range(10):
        row = await Notifications.claim()
        if row is None:
            return
        if not SETTINGS.EMAIL_ENABLED or (
            row.kind != "account_deleted" and not SETTINGS.STRIPE_ENABLED
        ):
            await Notifications.finish(row, state="skipped")
            continue
        try:
            payload = json.loads(cipher().decrypt(row.payload.encode()))
            await MAIL_SERVICE.send_lifecycle_email(kind=row.kind, **payload)
        except Exception:
            await Notifications.finish(
                row, state="pending" if row.attempts < 5 else "failed", error="delivery_failed"
            )
            logger.warning(
                "Lifecycle mail delivery failed (id=%s, attempt=%s).", row.id, row.attempts
            )
        else:
            await Notifications.finish(row, state="sent")
