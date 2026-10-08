import asyncio
import io
import logging
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from rich.console import Console

from app.core.config.settings import Settings
from app.core.observability.logging import get_logger
from app.core.observability.startup_display import (
    StartupDisplay,
    StartupPreludeFilter,
    configure_startup_console,
    startup_step,
)


@pytest.fixture
def settings():
    return Settings(
        APP_MODE="development",
        LOGIN_ENABLED=True,
        DB_DRIVER="postgresql+asyncpg",
        DB_HOST="private-host",
        DB_PASSWORD="secret",
        REDIS_IN_MEMORY=True,
        STARTUP_DISPLAY="plain",
        OAUTH_ENABLED=True,
        OAUTH_PROVIDERS="google,github",
        EMAIL_ENABLED=True,
        SMTP_HOST="smtp.gmail.com",
        STRIPE_ENABLED=False,
        DATABASE_URL="postgresql+asyncpg://user:secret@private-host/db",
    )


@pytest.fixture
def console_logs(caplog):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    target = logging.getLogger("uvicorn")
    previous = target.handlers[:]
    target.handlers = [handler]
    caplog.set_level(logging.INFO, logger="uvicorn")
    try:
        yield stream, handler
    finally:
        target.handlers = previous


def test_stack_enablement_and_evidence_are_separate(settings, console_logs, caplog):
    """Scenario: configured OAuth and disabled Stripe are never reported as verified."""
    # Given: safe names derived from settings containing a private DB connection string.
    display = StartupDisplay(settings, console=Console(file=io.StringIO(), force_terminal=False))
    # When: real caller boundaries finish their respective checks.
    with display.activate():
        with startup_step("oauth", success="Configured"):
            get_logger("test").info("Original provider record")
        with startup_step("billing"):
            pass
        with startup_step("email", success="Configured", detail="Connection check skipped"):
            pass
    # Then: console noise is removed but original records remain available to other handlers.
    output = console_logs[0].getvalue()
    assert "Original provider record" not in output
    assert "Original provider record" in caplog.text
    assert "stack=Google · GitHub enabled=yes check=Configured" in output
    assert "enabled=no check=Not checked" in output
    assert "Connection check skipped" in output
    assert display.rows["database"].stack == "PostgreSQL"
    assert display.rows["email"].stack == "Gmail SMTP"
    rendered = io.StringIO()
    Console(file=rendered, width=100).print(display.render())
    assert "secret" not in rendered.getvalue()
    assert "private-host" not in rendered.getvalue()
    assert "\x1b" not in output


def test_failure_preserves_exception_and_marks_unreached_services(settings, console_logs):
    """Scenario: a failed provider remains failed and subsequent services are not run."""
    # Given: a provider exception whose raw message must not reach the panel.
    display = StartupDisplay(settings)
    error = RuntimeError("secret-provider-response")
    # When: startup aborts at an enabled service.
    with pytest.raises(RuntimeError) as caught, display.activate(), startup_step("storage"):
        raise error
    # Then: failure propagation and terminal cleanup preserve the original semantics.
    assert caught.value is error
    assert display.rows["storage"].status == "Failed"
    assert display.rows["database"].status == "Not run"
    assert display.rows["billing"].status == "Not checked"
    assert "secret-provider-response" not in console_logs[0].getvalue()
    assert not console_logs[1].filters
    get_logger("test").info("After startup")
    assert "After startup" in console_logs[0].getvalue()


def test_cancelled_startup_restores_logging(settings, console_logs):
    """Scenario: cancellation propagates and removes temporary console filters."""
    # Given: an active service check.
    display = StartupDisplay(settings)
    # When: the lifespan task is cancelled.
    with pytest.raises(asyncio.CancelledError), display.activate(), startup_step("storage"):
        raise asyncio.CancelledError
    # Then: no success is claimed and subsequent output is normal.
    assert display.rows["storage"].status == "Cancelled"
    assert display.rows["database"].status == "Not run"
    assert not console_logs[1].filters


def test_interactive_panel_keeps_warnings_and_final_frame(settings, console_logs, monkeypatch):
    """Scenario: an interactive terminal shows the banner, live checks and warnings."""
    # Given: one terminal owner and a normal console handler bound before Live starts.
    settings.STARTUP_DISPLAY = "auto"
    monkeypatch.setattr(Settings, "has_multiple_server_workers", lambda _: False)
    output = io.StringIO()
    display = StartupDisplay(settings, console=Console(file=output, force_terminal=True, width=100))
    # When: a service logs a warning while completing.
    with display.activate():
        with startup_step("storage"):
            get_logger("test").warning("Preserve this warning")
    # Then: warning visibility and a durable completed frame survive animation cleanup.
    rendered = output.getvalue()
    assert "Blueprint for Agents" in rendered
    assert "Preserve this warning" in rendered
    assert "Verified" in rendered
    assert "Startup checks complete" in rendered
    assert display.live is None
    assert not console_logs[1].filters


@pytest.mark.parametrize(
    "mode,width,workers", [("plain", 100, False), ("auto", 60, False), ("auto", 100, True)]
)
def test_plain_fallback_avoids_live_cursor_updates(
    settings, console_logs, monkeypatch, mode, width, workers
):
    """Scenario: plain mode, narrow terminals and multiple workers use durable lines."""
    # Given: an output context unsuitable for a live table.
    settings.STARTUP_DISPLAY = mode
    monkeypatch.setattr(Settings, "has_multiple_server_workers", lambda _: workers)
    output = io.StringIO()
    display = StartupDisplay(
        settings, console=Console(file=output, force_terminal=True, width=width)
    )
    # When: startup executes.
    with display.activate(), startup_step("storage"):
        assert display.live is None
    # Then: no cursor controls are written.
    assert output.getvalue() == ""
    assert "check=Verified" in console_logs[0].getvalue()


def test_off_mode_preserves_original_logs(settings, console_logs):
    """Scenario: off mode leaves service logging and checks untouched."""
    # Given: the original logging mode.
    settings.STARTUP_DISPLAY = "off"
    # When: startup runs.
    with StartupDisplay(settings).activate(), startup_step("storage"):
        get_logger("test").info("Original startup")
    # Then: no reporter output or filters remain.
    assert console_logs[0].getvalue().strip() == "Original startup"
    assert not console_logs[1].filters


def test_prelude_filter_is_console_only_and_idempotent(settings, console_logs, caplog):
    """Scenario: repeated app creation suppresses only redundant INFO console messages."""
    # Given: a configured console and an independent capture/export handler.
    configure_startup_console(settings)
    configure_startup_console(settings)
    # When: Uvicorn announces startup and then an error.
    logging.getLogger("uvicorn.error").info("Waiting for application startup.")
    logging.getLogger("uvicorn.error").error("Application startup failed.")
    # Then: only the console INFO is suppressed; original records remain available.
    assert "Waiting for application startup." not in console_logs[0].getvalue()
    assert "Waiting for application startup." in caplog.text
    assert "Application startup failed." in console_logs[0].getvalue()
    assert sum(isinstance(f, StartupPreludeFilter) for f in console_logs[1].filters) == 1


@pytest.mark.parametrize(
    "scheme,expected", [("sqlite+aiosqlite", "SQLite"), ("postgresql+asyncpg", "PostgreSQL")]
)
def test_database_stack_uses_driver_without_exposing_url(settings, scheme, expected):
    """Scenario: the configured database driver becomes a safe readable stack name."""
    # Given: a driver URL.
    settings.DATABASE_URL = f"{scheme}://private"
    # When: the panel derives stack names.
    display = StartupDisplay(settings)
    # Then: only a fixed provider label is exposed.
    assert display.rows["database"].stack == expected


@pytest.mark.parametrize(
    "provider,expected",
    [("local", "Local"), ("s3", "Amazon S3"), ("r2", "Cloudflare R2"), ("supabase", "Supabase")],
)
def test_storage_stack_follows_selected_provider(settings, provider, expected):
    """Scenario: each supported storage provider has its own display name."""
    # Given: an explicitly selected provider.
    settings.OBJECT_STORAGE_PROVIDER = provider
    # When: the panel derives stack names.
    display = StartupDisplay(settings)
    # Then: a remote provider is never mislabeled as local storage.
    assert display.rows["storage"].stack == expected


def test_lifespan_failure_closes_storage_and_does_not_migrate(settings, monkeypatch, console_logs):
    """Scenario: SMTP failure aborts startup, closes storage and never initializes DB."""
    import app.main as main

    # Given: real lifespan orchestration with isolated service boundaries.
    monkeypatch.setattr(main, "SETTINGS", settings)
    monkeypatch.setattr(main.RedisManager, "verify_startup", AsyncMock())
    monkeypatch.setattr(Settings, "validate_runtime_mode", lambda _: None)
    monkeypatch.setattr(Settings, "get_oauth_validation_errors", lambda _: [])
    storage = AsyncMock()
    monkeypatch.setattr(
        "app.core.object_storage.create_object_storage", AsyncMock(return_value=storage)
    )
    monkeypatch.setattr(
        main.MAIL_SERVICE, "initialize", AsyncMock(side_effect=RuntimeError("SMTP failed"))
    )
    migrate = AsyncMock()
    monkeypatch.setattr(main, "run_startup_schema_migrations", migrate)
    app = FastAPI()

    # When: entering the application lifespan fails.
    async def run():
        with pytest.raises(RuntimeError, match="SMTP failed"):
            async with main.lifespan(app):
                pytest.fail("Requests must not be served after failed startup")

    asyncio.run(run())
    # Then: storage is closed, the DB is untouched, and failure/unreached rows are visible.
    storage.close.assert_awaited_once()
    migrate.assert_not_awaited()
    assert not hasattr(app.state, "object_storage")
    assert "service=Email stack=Gmail SMTP enabled=yes check=Failed" in console_logs[0].getvalue()
    assert (
        "service=Database stack=PostgreSQL enabled=yes check=Not run" in console_logs[0].getvalue()
    )


@pytest.mark.parametrize("cleanup_fails", [False, True])
def test_shutdown_closes_resources_before_farewell(
    settings, monkeypatch, console_logs, cleanup_fails
):
    """Scenario: cleanup reports each resource and says goodbye only after complete success."""
    import app.main as main

    # Given: successful startup with tracked cleanup order and a lazily unused Redis client.
    monkeypatch.setattr(main, "SETTINGS", settings)
    monkeypatch.setattr(main.RedisManager, "verify_startup", AsyncMock())
    monkeypatch.setattr(Settings, "validate_runtime_mode", lambda _: None)
    monkeypatch.setattr(Settings, "get_oauth_validation_errors", lambda _: [])
    settings.LOGIN_ENABLED = True
    order = []
    storage = AsyncMock()

    async def close_storage():
        order.append("storage")

    async def close_database():
        order.append("database")
        if cleanup_fails:
            raise RuntimeError("cleanup failed")

    async def close_redis():
        order.append("redis")

    storage.close.side_effect = close_storage
    monkeypatch.setattr(
        "app.core.object_storage.create_object_storage", AsyncMock(return_value=storage)
    )
    monkeypatch.setattr(main.MAIL_SERVICE, "initialize", AsyncMock())
    monkeypatch.setattr(main.BillingService, "initialize", AsyncMock())
    monkeypatch.setattr(main, "run_startup_schema_migrations", AsyncMock())
    monkeypatch.setattr(main, "init_db", AsyncMock())
    monkeypatch.setattr(main, "dispose_db", close_database)
    monkeypatch.setattr(main.RedisManager, "close", close_redis)
    monkeypatch.setattr(main.RedisManager, "_client", None)
    app = FastAPI()

    # When: the server finishes serving and exits its lifespan.
    async def run():
        async with main.lifespan(app):
            assert "Bye!!" not in console_logs[0].getvalue()

    if cleanup_fails:
        with pytest.raises(RuntimeError, match="cleanup failed"):
            asyncio.run(run())
    else:
        asyncio.run(run())
    # Then: even a failed DB close still attempts Redis/storage, without a false goodbye.
    assert order == ["database", "redis", "storage"]
    output = console_logs[0].getvalue()
    assert "check=Not opened" in output
    assert "Shutdown service=Storage stack=Local enabled=yes check=Closed" in output
    assert ("Bye!!" in output) is not cleanup_fails
    if cleanup_fails:
        assert "Shutdown service=Database stack=PostgreSQL enabled=yes check=Failed" in output
    else:
        assert output.index("Cleanup complete") < output.index("Bye!!")
    assert not hasattr(app.state, "object_storage")


@pytest.mark.parametrize(
    "args,env,expected",
    [
        (["uvicorn", "--workers", "2"], {}, True),
        (["uvicorn", "--workers=3"], {}, True),
        (["uvicorn"], {"WEB_CONCURRENCY": "2"}, True),
        (["uvicorn"], {"UVICORN_WORKERS": "2"}, True),
        (["uvicorn", "--reload"], {}, False),
    ],
)
def test_worker_detection_prevents_shared_terminal_animation(
    settings, monkeypatch, args, env, expected
):
    """Scenario: explicit Uvicorn worker counts disable cursor-based rendering."""
    import sys

    # Given: an isolated invocation/environment.
    monkeypatch.setattr(sys, "argv", args)
    for name in ("WEB_CONCURRENCY", "UVICORN_WORKERS"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    # When: worker count is inspected.
    multiple = settings.has_multiple_server_workers()
    # Then: only known shared-console worker configurations require fallback.
    assert multiple is expected


def test_cache_failure_aborts_before_integrations_and_closes_storage(
    settings, monkeypatch, console_logs
):
    """Scenario: failed Redis startup cannot become a green check or reach SMTP/DB."""
    import app.main as main

    # Given: a failing cache probe and safe cleanup boundaries.
    monkeypatch.setattr(main, "SETTINGS", settings)
    monkeypatch.setattr(Settings, "validate_runtime_mode", lambda _: None)
    probe = AsyncMock(side_effect=TimeoutError())
    monkeypatch.setattr(main.RedisManager, "verify_startup", probe)
    redis_close = AsyncMock()
    monkeypatch.setattr(main.RedisManager, "close", redis_close)
    storage = AsyncMock()
    monkeypatch.setattr(
        "app.core.object_storage.create_object_storage", AsyncMock(return_value=storage)
    )
    mail = AsyncMock()
    monkeypatch.setattr(main.MAIL_SERVICE, "initialize", mail)
    monkeypatch.setattr(main, "dispose_db", AsyncMock())

    # When: startup tries to connect to Redis.
    async def run():
        with pytest.raises(TimeoutError):
            async with main.lifespan(FastAPI()):
                pytest.fail("Failed cache must abort startup")

    asyncio.run(run())
    # Then: no later integration runs and all acquired clients are cleaned up.
    probe.assert_awaited_once()
    mail.assert_not_awaited()
    redis_close.assert_awaited_once()
    storage.close.assert_awaited_once()
    assert (
        "service=Cache stack=Redis · In-memory enabled=yes check=Failed"
        in console_logs[0].getvalue()
    )
    assert "Bye!!" not in console_logs[0].getvalue()


@pytest.mark.parametrize("error", [RuntimeError("failed"), asyncio.CancelledError()])
def test_failed_cache_creation_closes_unpublished_client(monkeypatch, error):
    """Scenario: a failed/cancelled Redis PING closes its pool before propagating."""
    from app.core.cache.redis import RedisManager
    from app.core.config.settings import SETTINGS

    # Given: a newly constructed Redis client that cannot finish its first PING.
    client = AsyncMock()
    client.ping.side_effect = error
    monkeypatch.setattr(SETTINGS, "REDIS_IN_MEMORY", False)
    monkeypatch.setattr("app.core.cache.redis.redis.from_url", lambda *args, **kwargs: client)
    monkeypatch.setattr(RedisManager, "_client", None)
    # When: creating the client fails.
    with pytest.raises(type(error)):
        asyncio.run(RedisManager.verify_startup())
    # Then: the unpublished client is closed and cannot be reused as verified.
    client.aclose.assert_awaited_once()
    assert RedisManager._client is None


def test_existing_cache_client_is_pinged_again(monkeypatch):
    """Scenario: an existing client still needs fresh startup connection evidence."""
    from app.core.cache.redis import RedisManager

    # Given: an existing cached connection object.
    client = AsyncMock()
    monkeypatch.setattr(RedisManager, "_client", client)
    # When: a new lifespan verifies cache availability.
    asyncio.run(RedisManager.verify_startup())
    # Then: reuse is not mistaken for a successful health check.
    client.ping.assert_awaited_once()


@pytest.mark.parametrize(
    "mode,login,expected",
    [
        ("development", True, "Mode: Development    Login: Enabled"),
        ("development", False, "Mode: Development    Login: Disabled · Bootstrap session"),
        ("production", True, "Mode: Production    Login: Enabled"),
    ],
)
def test_runtime_summary_shows_mode_and_login_policy(settings, console_logs, mode, login, expected):
    """Scenario: startup identifies the actual runtime mode and login policy."""
    # Given: runtime configuration independent of telemetry APP_ENV.
    settings.APP_MODE = mode
    settings.LOGIN_ENABLED = login
    settings.APP_ENV = "irrelevant-telemetry-label"
    settings.STARTUP_DISPLAY = "plain"
    display = StartupDisplay(settings)
    # When: startup begins.
    with display.activate():
        pass
    # Then: both terminal and plain representations describe runtime/login behavior.
    assert display.runtime_summary().plain == expected
    assert expected in console_logs[0].getvalue()
    assert "irrelevant-telemetry-label" not in console_logs[0].getvalue()


def test_redirected_auto_output_retains_banner_and_static_result(
    settings, console_logs, monkeypatch
):
    """Scenario: Docker-style redirected output keeps a static panel without ANSI updates."""
    # Given: redirected output with automatic presentation enabled.
    settings.STARTUP_DISPLAY = "auto"
    monkeypatch.setattr(Settings, "has_multiple_server_workers", lambda _: False)
    output = io.StringIO()
    display = StartupDisplay(
        settings, console=Console(file=output, force_terminal=False, width=100)
    )
    # When: startup checks complete without a live terminal.
    with display.activate(), startup_step("storage"):
        assert display.live is None
    # Then: the banner and final box remain, with no cursor controls or duplicate row logs.
    rendered = output.getvalue()
    assert "Blueprint for Agents" in rendered
    assert "╭─ Startup" in rendered
    assert "Verified" in rendered
    assert "Mode: Development" in rendered
    assert "Startup checks complete" in rendered
    assert "\x1b" not in rendered
    assert "service=Storage" not in console_logs[0].getvalue()
