from enum import Enum

from fastapi import status

from .error import ServiceErrorCode, ServiceException


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
    OAUTH_PROVIDER_NOT_ENABLED = ServiceErrorCode(
        "OAUTH_PROVIDER_NOT_ENABLED",
        "The requested OAuth provider is not enabled.",
        status.HTTP_400_BAD_REQUEST,
    )
    OAUTH_PROVIDER_CONFIG_INVALID = ServiceErrorCode(
        "OAUTH_PROVIDER_CONFIG_INVALID",
        "OAuth provider configuration is invalid.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    OAUTH_IDENTITY_CONFLICT = ServiceErrorCode(
        "OAUTH_IDENTITY_CONFLICT",
        "OAuth identity is already linked to another user.",
        status.HTTP_409_CONFLICT,
    )
    OAUTH_SIGNUP_FAILED = ServiceErrorCode(
        "OAUTH_SIGNUP_FAILED",
        "Failed to create OAuth user account.",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
    OAUTH_PROVIDER_REQUEST_FAILED = ServiceErrorCode(
        "OAUTH_PROVIDER_REQUEST_FAILED",
        "OAuth provider request failed.",
        status.HTTP_502_BAD_GATEWAY,
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
