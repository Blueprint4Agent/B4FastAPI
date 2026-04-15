import asyncio
import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import urljoin

from app.core.mail_templates import build_password_reset_email, build_verification_email
from app.core.settings import SETTINGS, Settings

# Use uvicorn's error logger so service logs are visible in standard server output.
logger = logging.getLogger("uvicorn.error")


@dataclass(frozen=True)
class MailMessage:
    to_email: str
    subject: str
    text_body: str
    html_body: str | None = None


class MailProvider:
    def validate_configuration(self) -> None:
        raise NotImplementedError

    def verify_startup(self) -> None:
        raise NotImplementedError

    async def send(self, message: MailMessage) -> None:
        raise NotImplementedError


class NullMailProvider(MailProvider):
    def validate_configuration(self) -> None:
        return

    def verify_startup(self) -> None:
        return

    async def send(self, message: MailMessage) -> None:
        logger.info("Email disabled. Skip sending email to %s.", message.to_email)


class SMTPMailProvider(MailProvider):
    def __init__(self, settings: Settings):
        self._settings = settings

    def validate_configuration(self) -> None:
        errors = self._settings.get_smtp_validation_errors()
        if errors:
            raise ValueError("; ".join(errors))

    def verify_startup(self) -> None:
        with self._open_client():
            return

    async def send(self, message: MailMessage) -> None:
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: MailMessage) -> None:
        with self._open_client() as smtp:
            smtp.send_message(self._build_email_message(message))

    def _build_email_message(self, message: MailMessage) -> EmailMessage:
        email_message = EmailMessage()
        email_message["Subject"] = message.subject
        email_message["From"] = self._settings.EMAIL_FROM
        email_message["To"] = message.to_email
        email_message.set_content(message.text_body)
        if message.html_body:
            email_message.add_alternative(message.html_body, subtype="html")
        return email_message

    def _open_client(self) -> smtplib.SMTP:
        smtp_factory = smtplib.SMTP_SSL if self._settings.SMTP_USE_SSL else smtplib.SMTP
        smtp = smtp_factory(
            host=self._settings.SMTP_HOST,
            port=self._settings.SMTP_PORT,
            timeout=self._settings.SMTP_TIMEOUT_SECONDS,
        )
        smtp.ehlo()
        if self._settings.SMTP_USE_STARTTLS and not self._settings.SMTP_USE_SSL:
            smtp.starttls()
            smtp.ehlo()

        if self._settings.SMTP_USERNAME and self._settings.SMTP_PASSWORD:
            smtp.login(self._settings.SMTP_USERNAME, self._settings.SMTP_PASSWORD)
        return smtp


class MailService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._provider: MailProvider = (
            SMTPMailProvider(settings) if settings.EMAIL_ENABLED else NullMailProvider()
        )

    async def initialize(self) -> None:
        if not self._settings.EMAIL_ENABLED:
            logger.info("Email integration is disabled.")
            return

        try:
            self._provider.validate_configuration()
        except ValueError:
            logger.exception("SMTP configuration validation failed.")
            raise

        logger.info(
            "SMTP integration enabled (host=%s, port=%s, starttls=%s, ssl=%s).",
            self._settings.SMTP_HOST,
            self._settings.SMTP_PORT,
            self._settings.SMTP_USE_STARTTLS,
            self._settings.SMTP_USE_SSL,
        )

        if self._settings.SMTP_VALIDATE_ON_STARTUP:
            await asyncio.to_thread(self._provider.verify_startup)
            logger.info("SMTP startup verification succeeded.")
        else:
            logger.info("SMTP startup verification skipped by configuration.")

    async def send_signup_verification_email(
        self, *, to_email: str, user_name: str, link: str = ""
    ) -> None:
        if not self._settings.EMAIL_ENABLED:
            return
        resolved_link = self._resolve_link(path="/verify-email", link=link)
        if not resolved_link:
            logger.warning("Skip signup verification email. Missing APP_BASE_URL and link.")
            return

        content = build_verification_email(
            name=user_name,
            link=resolved_link,
            app_name=self._settings.EMAIL_BRAND_NAME,
        )
        message = MailMessage(
            to_email=to_email,
            subject=content.subject,
            text_body=content.text,
            html_body=content.html,
        )
        logger.info("Attempting signup verification email delivery to %s.", to_email)
        try:
            await self._provider.send(message)
            logger.info("Signup verification email delivered to %s.", to_email)
        except Exception:
            logger.exception("Failed to send signup verification email to %s.", to_email)

    async def send_password_reset_email(
        self, *, to_email: str, user_name: str, link: str = ""
    ) -> None:
        if not self._settings.EMAIL_ENABLED:
            return
        resolved_link = self._resolve_link(path="/reset-password", link=link)
        if not resolved_link:
            logger.warning("Skip password reset email. Missing APP_BASE_URL and link.")
            return

        content = build_password_reset_email(
            name=user_name,
            link=resolved_link,
            app_name=self._settings.EMAIL_BRAND_NAME,
        )
        message = MailMessage(
            to_email=to_email,
            subject=content.subject,
            text_body=content.text,
            html_body=content.html,
        )
        logger.info("Attempting password reset email delivery to %s.", to_email)
        try:
            await self._provider.send(message)
            logger.info("Password reset email delivered to %s.", to_email)
        except Exception:
            logger.exception("Failed to send password reset email to %s.", to_email)

    def _resolve_link(self, *, path: str, link: str) -> str:
        explicit_link = link.strip()
        if explicit_link:
            return explicit_link

        base_url = self._settings.APP_BASE_URL.strip()
        if not base_url:
            return ""

        normalized_base = f"{base_url.rstrip('/')}/"
        return urljoin(normalized_base, path.lstrip("/"))


MAIL_SERVICE = MailService(SETTINGS)
