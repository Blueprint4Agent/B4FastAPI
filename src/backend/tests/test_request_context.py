import logging

from fastapi.testclient import TestClient

from app.core.logging import configure_request_context_logging, get_logger
from app.core.request_context import (
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
