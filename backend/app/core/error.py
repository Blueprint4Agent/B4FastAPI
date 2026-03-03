from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, status


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


class AuthErrorCode(Enum):
    SIGNUP_FAILED = ServiceErrorCode(
        "SIGNUP_FAILED",
        "Failed to create the user account.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    EMAIL_ALREADY_EXISTS = ServiceErrorCode(
        "EMAIL_ALREADY_EXISTS",
        "User with this email already exists.",
        status.HTTP_409_CONFLICT,
    )
    INVALID_CREDENTIALS = ServiceErrorCode(
        "INVALID_CREDENTIALS",
        "Incorrect email or password.",
        status.HTTP_401_UNAUTHORIZED,
    )
    ACCOUNT_LOCKED = ServiceErrorCode(
        "ACCOUNT_LOCKED",
        "Account is temporarily locked.",
        status.HTTP_423_LOCKED,
    )
    EMAIL_NOT_VERIFIED = ServiceErrorCode(
        "EMAIL_NOT_VERIFIED",
        "Email verification is required.",
        status.HTTP_403_FORBIDDEN,
    )
    EMAIL_DISABLED = ServiceErrorCode(
        "EMAIL_DISABLED",
        "Email-based features are disabled.",
        status.HTTP_403_FORBIDDEN,
    )
    INVALID_TOKEN = ServiceErrorCode(
        "INVALID_TOKEN",
        "Invalid refresh token.",
        status.HTTP_401_UNAUTHORIZED,
    )
    USER_NOT_FOUND = ServiceErrorCode(
        "USER_NOT_FOUND",
        "User not found.",
        status.HTTP_404_NOT_FOUND,
    )

    @property
    def code(self) -> ServiceErrorCode:
        return self.value


class AuthException(ServiceException):
    def __init__(
        self,
        code: AuthErrorCode,
        message: str | None = None,
        details: dict | None = None,
    ):
        super().__init__(code=code.code, message=message, details=details)


def service_exception_to_http(exc: ServiceException) -> HTTPException:
    payload: dict[str, str | dict] = {
        "error": exc.code.error,
        "message": exc.message,
    }
    if exc.details is not None:
        payload["details"] = exc.details
    return HTTPException(status_code=exc.code.status_code, detail=payload)
