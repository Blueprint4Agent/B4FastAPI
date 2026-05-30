import logging

from uvicorn.logging import DefaultFormatter

from app.core.config.settings import SETTINGS
from app.core.observability.request_context import get_request_id, get_trace_id

APP_LOGGER_NAME = "uvicorn.app"
UVICORN_ERROR_LOGGER_NAME = "uvicorn.error"
LOG_FORMAT_VERBOSE = (
    "%(asctime)s %(levelprefix)s logger=%(logger_name)s%(request_context)s message=%(message)s"
)
LOG_FORMAT_SIMPLE = "%(levelprefix)s %(message)s%(request_context)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
_ORIGINAL_LOG_RECORD_FACTORY = logging.getLogRecordFactory()
_REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED = False
_REQUEST_CONTEXT_LOG_ENABLED = SETTINGS.LOG_LEVEL.upper() == "DEBUG"


def _build_logger_name(name: str) -> str:
    if name == UVICORN_ERROR_LOGGER_NAME:
        return "uvicorn.server"

    normalized = name
    if normalized.startswith("uvicorn.app."):
        normalized = normalized.removeprefix("uvicorn.app.")
    if normalized.startswith("app."):
        normalized = normalized.removeprefix("app.")
    if normalized.startswith("router."):
        normalized = "routers." + normalized.removeprefix("router.")
    if normalized.startswith("service."):
        normalized = "services." + normalized.removeprefix("service.")
    return normalized


def _build_request_context_field(request_id: str, trace_id: str) -> str:
    if not request_id and not trace_id:
        return ""
    return f" request_id={request_id or '-'} trace_id={trace_id or '-'}"


def _should_emit_request_context(*, levelno: int) -> bool:
    if _REQUEST_CONTEXT_LOG_ENABLED:
        return True
    # In non-debug environments, include request/trace ids for error tracking.
    return levelno >= logging.ERROR


def _resolve_request_context_field(*, levelno: int, request_id: str, trace_id: str) -> str:
    if not _should_emit_request_context(levelno=levelno):
        return ""
    return _build_request_context_field(request_id, trace_id)


def _request_context_log_record_factory(*args, **kwargs) -> logging.LogRecord:
    record = _ORIGINAL_LOG_RECORD_FACTORY(*args, **kwargs)
    request_id = get_request_id()
    trace_id = get_trace_id()
    record.logger_name = _build_logger_name(record.name)
    record.request_id = request_id
    record.trace_id = trace_id
    record.request_context = _resolve_request_context_field(
        levelno=record.levelno,
        request_id=request_id,
        trace_id=trace_id,
    )
    return record


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        request_id = get_request_id()
        trace_id = get_trace_id()
        record.logger_name = _build_logger_name(record.name)
        record.request_id = request_id
        record.trace_id = trace_id
        record.request_context = _resolve_request_context_field(
            levelno=record.levelno,
            request_id=request_id,
            trace_id=trace_id,
        )
        return True


def get_logger(name: str | None = None) -> logging.Logger:
    if not name:
        return logging.getLogger(APP_LOGGER_NAME)
    return logging.getLogger(f"{APP_LOGGER_NAME}.{name}")


def configure_request_context_logging() -> None:
    global _REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED
    if not _REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED:
        logging.setLogRecordFactory(_request_context_log_record_factory)
        _REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED = True

    context_filter = RequestContextFilter()
    format_string = LOG_FORMAT_VERBOSE if _REQUEST_CONTEXT_LOG_ENABLED else LOG_FORMAT_SIMPLE
    formatter = DefaultFormatter(
        fmt=format_string,
        datefmt=LOG_DATE_FORMAT,
        use_colors=True,
    )
    for logger_name in ("uvicorn.error", "uvicorn"):
        logger = logging.getLogger(logger_name)
        if not any(isinstance(item, RequestContextFilter) for item in logger.filters):
            logger.addFilter(context_filter)
        for handler in logger.handlers:
            if not any(isinstance(item, RequestContextFilter) for item in handler.filters):
                handler.addFilter(context_filter)
            handler.setFormatter(formatter)


def mask_email(email: str) -> str:
    normalized = email.strip()
    if "@" not in normalized:
        return "***"

    local_part, domain = normalized.split("@", 1)
    if not local_part:
        return f"***@{domain}"
    if len(local_part) == 1:
        return f"{local_part}***@{domain}"
    return f"{local_part[0]}***{local_part[-1]}@{domain}"
