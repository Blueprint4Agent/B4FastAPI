"""Authentication mail producers; SMTP execution belongs to standalone Celery."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from app.core.celery.publisher import publish_task
from app.core.config.settings import SETTINGS, Settings
from app.core.observability.logging import get_logger, mask_email

logger = get_logger("app.core.mail.queue")
MailKind = Literal["signup_verification", "password_reset"]
MAIL_TASK_NAME = "b4fastapi.mail.send"


@dataclass
class MailQueueService:
    settings: Settings

    async def enqueue_signup_verification(
        self, *, to_email: str, user_name: str, link: str, language: str
    ) -> None:
        await self._enqueue(
            "signup_verification",
            to_email=to_email,
            user_name=user_name,
            link=link,
            language=language,
            ttl_minutes=self.settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
        )

    async def enqueue_password_reset(
        self, *, to_email: str, user_name: str, link: str, language: str
    ) -> None:
        await self._enqueue(
            "password_reset",
            to_email=to_email,
            user_name=user_name,
            link=link,
            language=language,
            ttl_minutes=self.settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        )

    async def _enqueue(
        self,
        kind: MailKind,
        *,
        to_email: str,
        user_name: str,
        link: str,
        language: str,
        ttl_minutes: int,
    ) -> None:
        if not self.settings.EMAIL_ENABLED:
            return
        now = datetime.now(UTC).timestamp()
        await publish_task(
            MAIL_TASK_NAME,
            payload={
                "message": {
                    "kind": kind,
                    "to_email": to_email,
                    "user_name": user_name,
                    "link": link,
                    "language": language,
                    "created_at": now,
                    "expires_at": now + ttl_minutes * 60,
                }
            },
        )
        logger.info("Email job queued (type=%s, to=%s).", kind, mask_email(to_email))


MAIL_QUEUE_SERVICE = MailQueueService(SETTINGS)
