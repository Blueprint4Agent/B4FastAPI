import logging

UVICORN_ERROR_LOGGER_NAME = "uvicorn.error"


def get_logger(name: str | None = None) -> logging.Logger:
    if not name:
        return logging.getLogger(UVICORN_ERROR_LOGGER_NAME)
    return logging.getLogger(f"{UVICORN_ERROR_LOGGER_NAME}.{name}")


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
