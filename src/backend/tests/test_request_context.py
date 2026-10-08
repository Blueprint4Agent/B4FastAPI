import logging

from fastapi.testclient import TestClient

from app.core.observability.logging import configure_request_context_logging, get_logger
from app.core.observability.request_context import (
    REQUEST_ID_HEADER,
    TRACE_ID_HEADER,
    reset_request_context,
    set_request_context,
)
from app.main import app


def test_request_context_headers_are_generated() -> None:
    with TestClient(app) as client:
        response = client.get("/ping")

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER]
    assert response.headers[TRACE_ID_HEADER]
    assert len(response.headers[TRACE_ID_HEADER]) == 32


def test_request_context_preserves_inbound_request_id() -> None:
    request_id = "client-request-123"

    with TestClient(app) as client:
        response = client.get("/ping", headers={REQUEST_ID_HEADER: request_id})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == request_id


def test_request_context_uses_traceparent_trace_id() -> None:
    trace_id = "0af7651916cd43dd8448eb211c80319c"
    traceparent = f"00-{trace_id}-b7ad6b7169203331-01"

    with TestClient(app) as client:
        response = client.get("/ping", headers={"traceparent": traceparent})

    assert response.status_code == 200
    assert response.headers[TRACE_ID_HEADER] == trace_id


def test_log_record_includes_request_context(caplog) -> None:
    request_id = "test-request-id"
    trace_id = "0af7651916cd43dd8448eb211c80319c"
    logger = get_logger("test.request_context")
    configure_request_context_logging()
    tokens = set_request_context(request_id=request_id, trace_id=trace_id)

    try:
        with caplog.at_level(logging.INFO, logger=logger.name):
            logger.info("Test log event (sample=%s).", "value")
    finally:
        reset_request_context(tokens)

    matching_records = [
        record for record in caplog.records if record.name == logger.name and record.message
    ]
    assert matching_records
    assert matching_records[-1].request_id == request_id
    assert matching_records[-1].trace_id == trace_id


def test_metrics_access_filter_preserves_other_requests_and_diagnostics():
    from app.core.observability.logging import MetricsAccessFilter

    access_filter = MetricsAccessFilter()
    for path, expected in [
        ("/metrics", False),
        ("/metrics?format=text", False),
        ("/api/v1/billing/subscription", True),
        ("/metrics-extra", True),
    ]:
        record = logging.LogRecord(
            "uvicorn.access",
            logging.INFO,
            "",
            0,
            "%s %s %s %s %s",
            ("127.0.0.1", "GET", path, "1.1", 200),
            None,
        )
        assert access_filter.filter(record) is expected
    diagnostic = logging.LogRecord(
        "uvicorn.error", logging.ERROR, "", 0, "metrics failed", (), None
    )
    assert access_filter.filter(diagnostic)


def test_metrics_filter_registration_is_idempotent():
    from app.core.observability.logging import MetricsAccessFilter

    configure_request_context_logging()
    configure_request_context_logging()
    filters = logging.getLogger("uvicorn.access").filters
    assert sum(isinstance(item, MetricsAccessFilter) for item in filters) == 1


def test_compact_access_console_preserves_original_file_records(monkeypatch, tmp_path):
    """Scenario: compact console output hides successful preflight without losing original file logs."""
    import io
    import re

    from app.core.observability.logging import SuccessfulPreflightConsoleFilter

    # Given: independent console and file sinks on the same Uvicorn access logger.
    output = io.StringIO()
    console_handler = logging.StreamHandler(output)
    file_path = tmp_path / "access.log"
    file_handler = logging.FileHandler(file_path)
    access = logging.getLogger("uvicorn.access")
    monkeypatch.setattr(access, "handlers", [console_handler, file_handler])
    monkeypatch.setattr(access, "level", logging.INFO)
    configure_request_context_logging()
    configure_request_context_logging()
    message = '%s - "%s %s HTTP/%s" %d'
    query_path = "/api/v1/auth/admin/users?page=1&page_size=10&search=test"
    # When: successful/failed preflights and normal requests reach both sinks.
    try:
        for method, path, status in [
            ("OPTIONS", "/api/v1/admin/status", 200),
            ("OPTIONS", "/api/v1/admin/status", 204),
            ("OPTIONS", "/api/v1/admin/status", 400),
            ("GET", query_path, 200),
            ("GET", "/api/v1/admin/status", 500),
        ]:
            access.info(message, "127.0.0.1:55894", method, path, "1.1", status)
        file_handler.flush()
        # Then: full paths and failures remain visible, while original file messages are intact.
        rendered = output.getvalue()
        lines = rendered.splitlines()
        assert len(lines) == 3
        assert all(re.match(r"\d{2}:\d{2}:\d{2}  (GET|OPTIONS)\s+", line) for line in lines)
        assert query_path in rendered
        assert "400 Bad Request" in rendered
        assert "500 Internal Server Error" in rendered
        assert "127.0.0.1" not in rendered
        assert "HTTP/1.1" not in rendered
        assert "INFO:" not in rendered
        assert "\x1b" not in rendered
        original = file_path.read_text()
        assert len(original.splitlines()) == 5
        assert '127.0.0.1:55894 - "OPTIONS /api/v1/admin/status HTTP/1.1" 200' in original
        assert query_path in original
        assert (
            sum(isinstance(f, SuccessfulPreflightConsoleFilter) for f in console_handler.filters)
            == 1
        )
        assert not file_handler.filters
    finally:
        file_handler.close()


def test_compact_access_formatter_keeps_args_and_nonstandard_messages():
    """Scenario: formatting never removes client/protocol evidence from the original record."""
    from app.core.observability.logging import CompactAccessFormatter

    # Given: a standard Uvicorn record and an unexpected diagnostic on its logger.
    formatter = CompactAccessFormatter(
        fmt="%(asctime)s %(method)s %(path)s %(status_code)s", datefmt="%H:%M:%S", use_colors=False
    )
    args = ("127.0.0.1:55894", "POST", "/api/v1/example", "1.1", 201)
    record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0, "%s %s %s %s %s", args, None)
    original = record.getMessage()
    # When: the compact console formatter processes the record.
    rendered = formatter.format(record)
    # Then: status names remain readable and exporters can still inspect the original data.
    assert "201 Created" in rendered
    assert record.args == args
    assert record.getMessage() == original
    diagnostic = logging.LogRecord("uvicorn.access", logging.WARNING, "", 0, "diagnostic", (), None)
    assert formatter.format(diagnostic) == "diagnostic"


def test_compact_levels_keep_error_context_traceback_and_file_formatter(monkeypatch, tmp_path):
    """Scenario: all console levels are aligned without losing error IDs, traceback or file formatting."""
    import io
    import re

    import app.core.observability.logging as app_logging

    # Given: a console and a caller-configured file handler, with normal INFO context policy.
    output = io.StringIO()
    console_handler = logging.StreamHandler(output)
    file_path = tmp_path / "app.log"
    file_handler = logging.FileHandler(file_path)
    original_formatter = logging.Formatter("%(name)s | %(levelname)s | %(message)s")
    file_handler.setFormatter(original_formatter)
    target = logging.getLogger("uvicorn")
    monkeypatch.setattr(target, "handlers", [console_handler, file_handler])
    monkeypatch.setattr(target, "level", logging.DEBUG)
    monkeypatch.setattr(app_logging, "_REQUEST_CONTEXT_LOG_ENABLED", False)
    configure_request_context_logging()
    logger = get_logger("services.example")
    tokens = set_request_context(request_id="request-test", trace_id="trace-test")
    # When: an application emits each standard level and an exception.
    try:
        logger.info("Information")
        logger.warning("Retry scheduled")
        logger.debug("Debug details")
        try:
            raise ValueError("Example failure")
        except ValueError:
            logger.exception("Request failed")
        logger.critical("Critical failure")
        file_handler.flush()
        # Then: aligned readable headers coexist with the original diagnostic evidence.
        rendered = output.getvalue()
        for level in ("INFO", "WARNING", "DEBUG", "ERROR", "CRITICAL"):
            assert re.search(rf"\d{{2}}:\d{{2}}:\d{{2}}  {level}\s+", rendered)
        assert "[services.example] Debug details" in rendered
        assert (
            "[services.example] Request failed request_id=request-test trace_id=trace-test"
            in rendered
        )
        assert "Traceback (most recent call last)" in rendered
        assert "ValueError: Example failure" in rendered
        assert "\x1b" not in rendered
        assert file_handler.formatter is original_formatter
        assert "uvicorn.app.services.example | WARNING | Retry scheduled" in file_path.read_text()
    finally:
        reset_request_context(tokens)
        file_handler.close()


def test_debug_mode_keeps_source_and_request_ids(monkeypatch):
    """Scenario: DEBUG mode retains source and correlation IDs even for INFO messages."""
    import app.core.observability.logging as app_logging

    # Given: verbose diagnostic context with the compact visual format.
    monkeypatch.setattr(app_logging, "_REQUEST_CONTEXT_LOG_ENABLED", True)
    tokens = set_request_context(request_id="debug-request", trace_id="debug-trace")
    formatter = app_logging.CompactLogFormatter(
        fmt=app_logging.LOG_FORMAT_CONSOLE, datefmt=app_logging.LOG_DATE_FORMAT, use_colors=False
    )
    # When: an INFO message is formatted in DEBUG mode.
    try:
        record = get_logger("services.example").makeRecord(
            "uvicorn.app.services.example", logging.INFO, "", 0, "Checked", (), None
        )
        rendered = formatter.format(record)
    finally:
        reset_request_context(tokens)
    # Then: compact formatting preserves the configured diagnostic context.
    assert "[services.example] Checked" in rendered
    assert "request_id=debug-request trace_id=debug-trace" in rendered
    assert record.msg == "Checked"


def test_request_field_colors_preserve_visible_alignment_and_original_records():
    """Scenario: HTTP verbs, time and API path use distinct colors without shifting columns."""
    from rich.text import Text

    from app.core.observability.logging import CompactAccessFormatter

    # Given: explicitly enabled terminal colors and a plain formatter for comparison.
    format_string = "%(asctime)s  %(method)s %(path)s %(status_code)s"
    colored = CompactAccessFormatter(fmt=format_string, datefmt="%H:%M:%S", use_colors=True)
    plain = CompactAccessFormatter(fmt=format_string, datefmt="%H:%M:%S", use_colors=False)
    methods = {
        "GET": 32,
        "POST": 36,
        "PUT": 33,
        "PATCH": 35,
        "DELETE": 31,
        "HEAD": 34,
        "OPTIONS": 90,
    }
    status_columns = set()
    # When: each HTTP verb is rendered using identical request fields.
    for method, ansi_color in methods.items():
        args = ("127.0.0.1:12345", method, "/api/v1/example?q=test", "1.1", 200)
        record = logging.LogRecord(
            "uvicorn.access", logging.INFO, "", 0, "%s %s %s %s %s", args, None
        )
        rendered = colored.format(record)
        visible = Text.from_ansi(rendered).plain
        # Then: the requested palette is distinct while visible text and original args stay intact.
        assert f"\x1b[{ansi_color}m{method}" in rendered
        assert "\x1b[38;5;75m/api/v1/example?q=test" in rendered
        assert rendered.startswith("\x1b[38;5;245m")
        assert visible == plain.format(record)
        assert record.args == args
        status_columns.add(visible.index("200 OK"))
    assert len(status_columns) == 1


def test_console_color_detection_respects_no_color_and_redirected_streams(monkeypatch):
    """Scenario: NO_COLOR and nonterminal output never acquire ANSI escape sequences."""
    import io

    from app.core.observability.logging import _console_uses_colors

    # Given: redirected output and an emulated color-capable terminal.
    class Terminal(io.StringIO):
        def isatty(self):
            return True

    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("TERM", "xterm-256color")
    # When/Then: only a terminal without NO_COLOR supports colored fields.
    assert not _console_uses_colors(logging.StreamHandler(io.StringIO()))
    assert _console_uses_colors(logging.StreamHandler(Terminal()))
    monkeypatch.setenv("NO_COLOR", "1")
    assert not _console_uses_colors(logging.StreamHandler(Terminal()))
