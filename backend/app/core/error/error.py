from dataclasses import dataclass

from fastapi import HTTPException


@dataclass(frozen=True)
class ServiceErrorCode:
    error: str
    default_message: str
    status_code: int


class ServiceException(Exception):
    def __init__(
        self,
        code: ServiceErrorCode,
        message: str | None = None,
        details: dict | None = None,
    ):
        super().__init__(message or code.default_message)
        self.code = code
        self.message = message or code.default_message
        self.details = details


def service_exception_to_http(exc: ServiceException) -> HTTPException:
    payload: dict[str, str | dict] = {
        "error": exc.code.error,
        "message": exc.message,
    }
    if exc.details is not None:
        payload["details"] = exc.details
    return HTTPException(status_code=exc.code.status_code, detail=payload)
