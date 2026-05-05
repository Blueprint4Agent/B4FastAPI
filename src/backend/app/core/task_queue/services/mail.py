from dataclasses import dataclass

from app.core.logging import get_logger, mask_email
from app.core.mail import MAIL_SERVICE
from app.core.settings import SETTINGS, Settings
from app.core.task_queue.worker import RedisTaskQueueWorker, TaskQueueConfig

logger = get_logger("app.core.task_queue.services.mail")

MAIL_QUEUE_KEY = "queue:mail:jobs"
MAIL_QUEUE_DLQ_KEY = "queue:mail:dlq"


@dataclass
class MailQueueService:
    settings: Settings

    def __post_init__(self) -> None:
        config = TaskQueueConfig(
            queue_key=MAIL_QUEUE_KEY,
            dlq_key=MAIL_QUEUE_DLQ_KEY,
            block_timeout_seconds=self.settings.EMAIL_QUEUE_BLOCK_TIMEOUT_SECONDS,
            max_retries=self.settings.EMAIL_QUEUE_MAX_RETRIES,
            retry_delay_seconds=self.settings.EMAIL_QUEUE_RETRY_DELAY_SECONDS,
        )
        self._worker = RedisTaskQueueWorker(name="mail", config=config)
        self._worker.register_handler("signup_verification", self._handle_signup_verification)
        self._worker.register_handler("password_reset", self._handle_password_reset)

    async def enqueue_signup_verification(
        self,
        *,
        to_email: str,
        user_name: str,
        link: str,
    ) -> None:
        if not self.settings.EMAIL_ENABLED:
            return
        await self._worker.enqueue(
            task_type="signup_verification",
            payload={
                "to_email": to_email,
                "user_name": user_name,
                "link": link,
            },
        )
        logger.info(
            "Email job queued (type=%s, to=%s).",
            "signup_verification",
            mask_email(to_email),
        )

    async def enqueue_password_reset(
        self,
        *,
        to_email: str,
        user_name: str,
        link: str,
    ) -> None:
        if not self.settings.EMAIL_ENABLED:
            return
        await self._worker.enqueue(
            task_type="password_reset",
            payload={
                "to_email": to_email,
                "user_name": user_name,
                "link": link,
            },
        )
        logger.info(
            "Email job queued (type=%s, to=%s).",
            "password_reset",
            mask_email(to_email),
        )

    async def start_worker(self) -> None:
        if not self.settings.EMAIL_ENABLED:
            logger.info("Email queue worker skipped because email integration is disabled.")
            return
        await self._worker.start()
        logger.info("Email queue worker started.")

    async def stop_worker(self) -> None:
        await self._worker.stop()
        logger.info("Email queue worker stopped.")

    async def _handle_signup_verification(self, payload: dict[str, object]) -> None:
        to_email = str(payload.get("to_email", ""))
        user_name = str(payload.get("user_name", ""))
        link = str(payload.get("link", ""))
        await MAIL_SERVICE.send_signup_verification_email(
            to_email=to_email,
            user_name=user_name,
            link=link,
            raise_on_failure=True,
        )
        logger.info(
            "Email job delivered (type=%s, to=%s).",
            "signup_verification",
            mask_email(to_email),
        )

    async def _handle_password_reset(self, payload: dict[str, object]) -> None:
        to_email = str(payload.get("to_email", ""))
        user_name = str(payload.get("user_name", ""))
        link = str(payload.get("link", ""))
        await MAIL_SERVICE.send_password_reset_email(
            to_email=to_email,
            user_name=user_name,
            link=link,
            raise_on_failure=True,
        )
        logger.info(
            "Email job delivered (type=%s, to=%s).",
            "password_reset",
            mask_email(to_email),
        )


MAIL_QUEUE_SERVICE = MailQueueService(SETTINGS)

