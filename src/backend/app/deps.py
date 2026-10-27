import hashlib
import hmac
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config.settings import SETTINGS
from app.core.error import (
    APIKeyErrorCode,
    APIKeyException,
    AuthErrorCode,
    AuthException,
)
from app.core.object_storage import ObjectStorage
from app.models.api_key import APIKey, APIKeys
from app.models.user import UserResponse, UserRole, Users

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)
api_key_security = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_token_user(
    token_auth: Annotated[str | None, Depends(oauth2_scheme)],
) -> UserResponse | None:
    if token_auth is None:
        return None

    try:
        payload = jwt.decode(
            token_auth,
            SETTINGS.SECRET_KEY,
            algorithms=[SETTINGS.ALGORITHM],
        )
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise AuthException(
            code=AuthErrorCode.INVALID_TOKEN,
            message="Invalid bearer token.",
        ) from None

    token_user = await Users.get_user_response_by_id(user_id)
    if token_user is None:
        raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
    await reject_production_bootstrap(token_user)
    return token_user


async def get_current_session_user(
    user: Annotated[UserResponse | None, Depends(get_current_token_user)],
) -> UserResponse:
    if user is None:
        raise AuthException(code=AuthErrorCode.INVALID_TOKEN)
    return user


async def get_current_api_key(
    api_key: Annotated[str | None, Depends(api_key_security)],
) -> APIKey | None:
    if api_key is None:
        return None

    normalized = api_key.strip()
    if not normalized:
        raise APIKeyException(code=APIKeyErrorCode.API_KEY_INVALID)

    key_hash = hmac.new(
        SETTINGS.SECRET_KEY.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    valid_key = await APIKeys.record_valid_key_use(key_hash=key_hash, now=datetime.now(UTC))
    if valid_key is None:
        raise APIKeyException(code=APIKeyErrorCode.API_KEY_INVALID)
    return valid_key


async def get_current_user(
    token_user: Annotated[UserResponse | None, Depends(get_current_token_user)],
    current_api_key: Annotated[APIKey | None, Depends(get_current_api_key)],
) -> UserResponse:
    api_key_user: UserResponse | None = None

    if current_api_key is not None:
        api_key_user = await Users.get_user_response_by_id(current_api_key.user_id)
        if api_key_user is None:
            raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)

    if token_user is None and api_key_user is None:
        raise AuthException(
            code=AuthErrorCode.INVALID_TOKEN,
            message="Bearer token or API key is required.",
        )

    if token_user is not None and api_key_user is not None and token_user.id != api_key_user.id:
        raise APIKeyException(code=APIKeyErrorCode.API_KEY_USER_MISMATCH)

    user = token_user or api_key_user
    if api_key_user is not None:
        await reject_production_bootstrap(api_key_user)
    return user


async def reject_production_bootstrap(user: UserResponse) -> None:
    if SETTINGS.APP_MODE == "production" and await Users.has_bootstrap_identity(user.id):
        raise AuthException(code=AuthErrorCode.INSUFFICIENT_ROLE)


def require_roles(*roles: UserRole):
    allowed_roles = {role.value for role in roles}

    async def _role_guard(
        current_user: Annotated[UserResponse, Depends(get_current_user)],
    ) -> UserResponse:
        if current_user.role.value not in allowed_roles:
            raise AuthException(
                code=AuthErrorCode.INSUFFICIENT_ROLE,
                details={
                    "required_roles": sorted(allowed_roles),
                    "current_role": current_user.role.value,
                },
            )
        return current_user

    return _role_guard


async def get_current_admin_user(
    current_user: Annotated[UserResponse, Depends(require_roles(UserRole.ADMIN))],
) -> UserResponse:
    return current_user


async def get_current_directory_user(
    current_user: Annotated[UserResponse, Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
) -> UserResponse:
    """Read-only directory permission; does not grant other administrator privileges."""
    return current_user


def get_object_storage(request: Request) -> ObjectStorage:
    """Inject into domain services; never construct SDK clients in routers."""
    return request.app.state.object_storage
