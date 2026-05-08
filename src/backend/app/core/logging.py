import logging

from app.core.request_context import get_request_id, get_trace_id

UVICORN_ERROR_LOGGER_NAME = "uvicorn.error"
LOG_FORMAT = (
    "%(asctime)s level=%(levelname)s logger=%(name)s "
    "request_id=%(request_id)s trace_id=%(trace_id)s message=%(message)s"
)
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
_ORIGINAL_LOG_RECORD_FACTORY = logging.getLogRecordFactory()
_REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED = False


def _request_context_log_record_factory(*args, **kwargs) -> logging.LogRecord:
    record = _ORIGINAL_LOG_RECORD_FACTORY(*args, **kwargs)
    record.request_id = get_request_id() or "-"
    record.trace_id = get_trace_id() or "-"
    return record


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.trace_id = get_trace_id() or "-"
        return True


def get_logger(name: str | None = None) -> logging.Logger:
    if not name:
        return logging.getLogger(UVICORN_ERROR_LOGGER_NAME)
    return logging.getLogger(f"{UVICORN_ERROR_LOGGER_NAME}.{name}")


def configure_request_context_logging() -> None:
    global _REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED
    if not _REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED:
        logging.setLogRecordFactory(_request_context_log_record_factory)
        _REQUEST_CONTEXT_RECORD_FACTORY_CONFIGURED = True

    context_filter = RequestContextFilter()
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
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
