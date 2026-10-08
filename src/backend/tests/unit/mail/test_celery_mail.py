import asyncio
import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import fakeredis
import pytest
from celery.exceptions import Retry
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.celery import mail
from app.core.config.settings import SETTINGS, Settings
from app.core.mail.queue import MAIL_TASK_NAME, MailQueueService


def message(kind="signup_verification", expires_at=None):
    now = datetime.now(UTC).timestamp()
    return {
        "kind": kind,
        "to_email": "person@example.com",
        "user_name": "User",
        "link": "https://example.com/verify?token=secret",
        "language": "ko",
        "created_at": now,
        "expires_at": expires_at if expires_at is not None else now + 1800,
    }


@pytest.mark.parametrize("kind", ["signup_verification", "password_reset"])
def test_producer_preserves_fields_and_expiry(monkeypatch, kind):
    """Scenario: both auth mail producers publish the expected Celery payload."""
    # Given: enabled mail and a capture publisher.
    publish = AsyncMock(return_value="task-id")
    monkeypatch.setattr("app.core.mail.queue.publish_task", publish)
    settings = Settings(LOGIN_ENABLED=True, EMAIL_ENABLED=True)
    service = MailQueueService(settings)
    # When: the domain enqueues a localized link.
    enqueue = getattr(service, f"enqueue_{kind}")
    asyncio.run(
        enqueue(
            to_email="person@example.com",
            user_name="User",
            link="https://example.com",
            language="ko",
        )
    )
    # Then: the job preserves its kind, locale and token lifetime.
    assert publish.call_args.args == (MAIL_TASK_NAME,)
    job = publish.call_args.kwargs["payload"]["message"]
    assert job["kind"] == kind
    assert job["language"] == "ko"
    assert job["link"] == "https://example.com"
    ttl = (
        settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
        if kind == "signup_verification"
        else settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )
    assert job["expires_at"] - job["created_at"] == ttl * 60


def test_disabled_producer_does_not_contact_broker(monkeypatch):
    """Scenario: email-disabled applications do not require a Celery broker."""
    # Given: disabled email.
    publish = AsyncMock()
    monkeypatch.setattr("app.core.mail.queue.publish_task", publish)
    service = MailQueueService(Settings(EMAIL_ENABLED=False))
    # When: either email is requested.
    for enqueue in (service.enqueue_signup_verification, service.enqueue_password_reset):
        asyncio.run(
            enqueue(to_email="person@example.com", user_name="User", link="url", language="en")
        )
    # Then: no publication occurs.
    publish.assert_not_called()


@pytest.fixture
def delivery(monkeypatch):
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    monkeypatch.setattr(SETTINGS, "EMAIL_QUEUE_MAX_RETRIES", 3)
    monkeypatch.setattr(SETTINGS, "EMAIL_QUEUE_RETRY_DELAY_SECONDS", 2)
    sender = AsyncMock()
    archive = Mock()
    monkeypatch.setattr(mail.MAIL_SERVICE, "send_signup_verification_email", sender)
    monkeypatch.setattr(mail.MAIL_SERVICE, "send_password_reset_email", sender)
    monkeypatch.setattr(mail.MAIL_SERVICE, "send_welcome_email", sender)
    monkeypatch.setattr(mail, "archive_failure", archive)
    return sender, archive


@pytest.mark.parametrize("kind", ["signup_verification", "password_reset", "welcome"])
def test_worker_sends_localized_mail(delivery, kind):
    """Scenario: the task invokes SMTP service with propagated failure handling."""
    # Given: a valid queued message.
    sender, archive = delivery
    # When: Celery executes it.
    mail.send_mail.apply(kwargs={"message": message(kind)}, throw=True)
    # Then: delivery preserves recipient/link/locale without archiving failure.
    sender.assert_awaited_once_with(
        to_email="person@example.com",
        user_name="User",
        link="https://example.com/verify?token=secret",
        language="ko",
        raise_on_failure=True,
    )
    archive.assert_not_called()


def test_delivery_retries_are_bounded_and_exhaustion_is_archived(delivery):
    """Scenario: initial delivery plus three retries ends in one failure record."""
    # Given: persistently failing SMTP.
    sender, archive = delivery
    sender.side_effect = OSError("SMTP down")
    # When: eager execution follows the actual Celery retry chain.
    result = mail.send_mail.apply(kwargs={"message": message()}, throw=False)
    # Then: four attempts finish with a correlated archived failure.
    assert result.successful()
    assert sender.await_count == 4
    archive.assert_called_once()
    record = archive.call_args.kwargs["record"]
    assert record["delivery_attempt"] == 3
    assert record["reason"] == "OSError"
    assert record["task_id"] == result.id


def test_transient_failure_recovers_without_archive(delivery):
    """Scenario: a successful retry does not create a terminal failure record."""
    # Given: one transient SMTP failure.
    sender, archive = delivery
    sender.side_effect = [OSError("temporary"), None]
    # When: retrying the same task.
    result = mail.send_mail.apply(kwargs={"message": message()}, throw=False)
    # Then: the retry succeeds.
    assert result.successful()
    assert sender.await_count == 2
    archive.assert_not_called()


@pytest.mark.parametrize("expired", [True, False])
def test_unusable_message_is_archived_without_sending(delivery, expired):
    """Scenario: expired or malformed links never reach SMTP."""
    # Given: an expired message or unsupported mail kind.
    sender, archive = delivery
    job = message(expires_at=0) if expired else message(kind="unknown")
    # When: executing the task.
    mail.send_mail.apply(kwargs={"message": job}, throw=True)
    # Then: the failure is retained for inspection without attempting delivery.
    sender.assert_not_called()
    assert archive.call_args.kwargs["record"]["reason"] == (
        "expired" if expired else "invalid_payload"
    )


def test_archive_retry_does_not_send_mail_again(delivery, monkeypatch):
    """Scenario: failure storage retries carry a terminal phase and never send SMTP."""
    # Given: terminal archival failing once.
    sender, archive = delivery
    archive.side_effect = [RedisConnectionError("offline"), None]
    retry = Mock(side_effect=Retry())
    monkeypatch.setattr(mail.send_mail, "retry", retry)
    job = message()
    # When: processing an already exhausted delivery.
    with pytest.raises(Retry):
        mail.send_mail.apply(
            kwargs={"message": job, "delivery_attempt": 3, "failure_reason": "OSError"}, throw=True
        )
    # Then: the replacement message is archive-only, with a bounded delay.
    retry_kwargs = retry.call_args.kwargs
    assert retry_kwargs["countdown"] == 60
    assert retry_kwargs["kwargs"]["failure_reason"] == "OSError"
    mail.send_mail.apply(kwargs=retry_kwargs["kwargs"], throw=True)
    sender.assert_not_called()
    assert archive.call_count == 2


def test_failure_archive_is_idempotent(monkeypatch):
    """Scenario: duplicate terminal delivery overwrites one namespaced failure record."""
    # Given: isolated Redis and a stable task ID.
    server = fakeredis.FakeServer()
    monkeypatch.setattr(
        mail.Redis, "from_url", lambda *args, **kwargs: fakeredis.FakeRedis(server=server)
    )
    record = {"task_id": "same-task", "reason": "expired"}
    # When: the archive write is repeated after ambiguous completion.
    mail.archive_failure(task_id="same-task", record=record)
    mail.archive_failure(task_id="same-task", record=record)
    # Then: only one record remains.
    client = fakeredis.FakeRedis(server=server)
    key = f"{SETTINGS.CELERY_KEY_PREFIX}mail:failures"
    assert client.hlen(key) == 1
    assert json.loads(client.hget(key, "same-task")) == record


def test_disabled_consumer_skips_smtp(delivery, monkeypatch):
    """Scenario: disabling email at the worker prevents pending jobs from sending."""
    # Given: email has been disabled since publication.
    sender, archive = delivery
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", False)
    # When: consuming a pending job.
    mail.send_mail.apply(kwargs={"message": message()}, throw=True)
    # Then: neither delivery nor error archival occurs.
    sender.assert_not_called()
    archive.assert_not_called()


def test_worker_initialization_fails_closed(monkeypatch):
    """Scenario: invalid SMTP settings prevent a mail worker from starting."""
    # Given: SMTP configuration rejection.
    monkeypatch.setattr(
        mail.MAIL_SERVICE, "initialize", AsyncMock(side_effect=ValueError("invalid SMTP"))
    )
    # When: worker initialization runs.
    # Then: startup exits instead of accepting tasks with invalid mail configuration.
    with pytest.raises(SystemExit, match="SMTP initialization failed"):
        mail.initialize_mail_worker()


def test_worker_delivers_deletion_code_without_turning_it_into_a_link(delivery, monkeypatch):
    """Scenario: deletion codes use the shared retry pipeline and a code-only SMTP method."""
    # Given: a valid user-requested code message.
    sender, archive = delivery
    monkeypatch.setattr(mail.MAIL_SERVICE, "send_account_deletion_email", sender)
    payload = {**message("account_deletion"), "link": "", "code": "123456"}
    # When: the worker handles the message.
    mail.send_mail.apply(kwargs={"message": payload}, throw=True)
    # Then: the secret is delivered only as the code parameter, not a URL.
    sender.assert_awaited_once_with(
        to_email="person@example.com",
        user_name="User",
        code="123456",
        language="ko",
        raise_on_failure=True,
    )
    archive.assert_not_called()


@pytest.mark.parametrize("enabled", [False, True])
def test_lifecycle_wake_uses_existing_queue_without_recipient_payload(monkeypatch, enabled):
    """Scenario: the existing mail queue wakes lifecycle delivery without sending private broker data."""
    # Given: an isolated queue service and captured publication.
    publish = AsyncMock()
    monkeypatch.setattr("app.core.mail.queue.publish_task", publish)
    service = MailQueueService(Settings(EMAIL_ENABLED=enabled))
    # When: a committed outbox asks for a worker wake-up.
    asyncio.run(service.wake_lifecycle())
    # Then: disabled mode is silent; enabled mode sends only the task name and empty payload.
    if enabled:
        publish.assert_awaited_once_with("b4fastapi.notifications.drain", payload={})
    else:
        publish.assert_not_called()


@pytest.mark.parametrize("kind", ["account_deletion", "password_change"])
def test_code_mail_producer_and_worker_keep_purpose_and_expiry(monkeypatch, kind):
    """Scenario: private six-digit code jobs reach only their intended mail sender."""
    # Given: captured publication and a mocked SMTP boundary.
    publish = AsyncMock()
    monkeypatch.setattr("app.core.mail.queue.publish_task", publish)
    monkeypatch.setattr(SETTINGS, "EMAIL_ENABLED", True)
    queue = MailQueueService(Settings(EMAIL_ENABLED=True))
    # When: queueing and executing the exact generated job.
    asyncio.run(
        getattr(queue, f"enqueue_{kind}")(
            to_email="person@example.com", user_name="User", code="123456", language="ko"
        )
    )
    job = publish.call_args.kwargs["payload"]["message"]
    assert job["expires_at"] - job["created_at"] == 600
    assert job["kind"] == kind and job["link"] == ""
    sender = AsyncMock()
    monkeypatch.setattr(mail.MAIL_SERVICE, f"send_{kind}_email", sender)
    mail.send_mail.apply(kwargs={"message": job}, throw=True)
    # Then: the purpose-specific sender receives a code, never a reset/deletion link.
    sender.assert_awaited_once_with(
        to_email="person@example.com",
        user_name="User",
        code="123456",
        language="ko",
        raise_on_failure=True,
    )
