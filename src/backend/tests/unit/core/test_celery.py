import asyncio
import threading
from unittest.mock import Mock

import pytest
from celery.contrib.testing.worker import start_worker

from app.core.celery.app import create_celery_app
from app.core.celery.publisher import publish_task
from app.core.config.settings import Settings
from app.core.observability.request_context import reset_request_context, set_request_context
from app.core.observability.task_context import get_task_context


def test_celery_broker_is_independent_of_api_fakeredis() -> None:
    """Scenario: API fakeredis does not become a standalone worker broker."""
    # Given: API in-memory mode with an explicit real broker.
    settings = Settings(REDIS_IN_MEMORY=True, CELERY_BROKER_URL="redis://localhost:6380/2")
    app = create_celery_app(settings)
    # When: configuring a standalone worker.
    # Then: it uses the real broker and safe serialization, without business schedules.
    assert app.conf.broker_url == "redis://localhost:6380/2"
    assert app.conf.accept_content == ["json"]
    assert app.conf.result_backend is None
    assert app.conf.beat_schedule == {}
    assert app.conf.task_acks_late
    assert app.conf.task_time_limit < app.conf.broker_transport_options["visibility_timeout"]
    app.close()


def test_celery_fallback_encodes_redis_password() -> None:
    """Scenario: the default broker reuses encoded Redis connection settings."""
    # Given: reserved characters in a synthetic password.
    settings = Settings(CELERY_BROKER_URL="", REDIS_PASSWORD="p@ss/word", REDIS_DB=3)
    # When: resolving the fallback broker.
    # Then: the password stays encoded and the database is preserved.
    assert settings.celery_broker_url == settings.REDIS_URL
    assert ":p%40ss%2Fword@" in settings.celery_broker_url
    assert settings.celery_broker_url.endswith("/3")


def test_publish_runs_off_event_loop_and_propagates_trace(monkeypatch) -> None:
    """Scenario: async publication hides payload displays and preserves correlation."""
    # Given: a fake broker publisher and active request context.
    caller_thread = threading.get_ident()
    calls = []

    def send_task(name, **kwargs):
        calls.append((name, kwargs, threading.get_ident()))

    monkeypatch.setattr("app.core.celery.publisher.celery_app.send_task", send_task)
    tokens = set_request_context(request_id="request", trace_id="origin-trace")
    try:
        # When: publishing from async code.
        task_id = asyncio.run(publish_task("b4fastapi.probe", payload={}))
    finally:
        reset_request_context(tokens)
    # Then: synchronous broker I/O ran elsewhere with explicit correlation.
    name, options, publish_thread = calls[0]
    assert name == "b4fastapi.probe"
    assert publish_thread != caller_thread
    assert options["task_id"] == task_id
    assert options["headers"] == {"trace_id": "origin-trace"}
    assert options["kwargsrepr"] == "<redacted>"


def test_publish_failure_is_not_reported_as_success(monkeypatch) -> None:
    """Scenario: broker failure propagates to the calling service."""
    # Given: an unavailable broker.
    monkeypatch.setattr(
        "app.core.celery.publisher.celery_app.send_task",
        Mock(side_effect=ConnectionError("broker unavailable")),
    )
    # When: publishing a task.
    # Then: callers can normalize the failure rather than receiving a false receipt.
    with pytest.raises(ConnectionError):
        asyncio.run(publish_task("b4fastapi.probe", payload={}))


def test_worker_consumes_messages_and_clears_context() -> None:
    """Scenario: a real worker consumes serialized messages and isolates task context."""
    # Given: isolated test transports (production result storage remains disabled).
    app = create_celery_app(Settings(CELERY_BROKER_URL="memory://", CELERY_QUEUE="test.celery"))
    app.conf.update(result_backend="cache+memory://", task_ignore_result=False)

    @app.task(name="test.context")
    def context():
        return list(get_task_context())

    @app.task(name="test.failure")
    def failure():
        raise ValueError("test failure")

    try:
        with start_worker(app, pool="solo", perform_ping_check=False, shutdown_timeout=10):
            # When: handling success, failure, then a message without trace headers.
            first = context.apply_async(headers={"trace_id": "trace-one"})
            assert first.get(timeout=10) == [first.id, "trace-one"]
            failed = failure.delay()
            with pytest.raises(ValueError, match="test failure"):
                failed.get(timeout=10)
            last = context.delay()
            # Then: the worker survives and does not reuse the preceding task's trace.
            assert last.get(timeout=10) == [last.id, ""]
            assert get_task_context() == ("", "")
    finally:
        app.close()
