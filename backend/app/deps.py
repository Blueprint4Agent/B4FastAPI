import hashlib
import hmac
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select

from app.core.database import get_db
from app.core.error import (
    APIKeyErrorCode,
    APIKeyException,
    AuthErrorCode,
    AuthException,
    service_exception_to_http,
)
from app.core.settings import SETTINGS
from app.models.api_key import APIKey
from app.models.user import UserResponse, Users

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
        raise service_exception_to_http(
            AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Invalid bearer token.",
            )
        ) from None

    token_user = await Users.get_user_response_by_id(user_id)
    if token_user is None:
        raise service_exception_to_http(AuthException(code=AuthErrorCode.USER_NOT_FOUND))
    return token_user


async def get_current_api_key(
    api_key: Annotated[str | None, Depends(api_key_security)],
) -> APIKey | None:
    if api_key is None:
        return None

    normalized = api_key.strip()
    if not normalized:
        raise service_exception_to_http(APIKeyException(code=APIKeyErrorCode.API_KEY_INVALID))

    key_hash = hmac.new(
        SETTINGS.SECRET_KEY.encode("utf-8"),
        normalized.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    async with get_db() as db:
        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.revoked_at.is_(None),
            )
        )
        valid_key = result.scalar_one_or_none()
        if valid_key is None:
            raise service_exception_to_http(APIKeyException(code=APIKeyErrorCode.API_KEY_INVALID))

        valid_key.last_used_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(valid_key)
        return valid_key


async def get_current_user(
    token_user: Annotated[UserResponse | None, Depends(get_current_token_user)],
    current_api_key: Annotated[APIKey | None, Depends(get_current_api_key)],
) -> UserResponse:
    api_key_user: UserResponse | None = None

    if current_api_key is not None:
        api_key_user = await Users.get_user_response_by_id(current_api_key.user_id)
        if api_key_user is None:
            raise service_exception_to_http(AuthException(code=AuthErrorCode.USER_NOT_FOUND))

    if token_user is None and api_key_user is None:
        raise service_exception_to_http(
            AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Bearer token or API key is required.",
            )
        )

    if token_user is not None and api_key_user is not None and token_user.id != api_key_user.id:
        raise service_exception_to_http(
            APIKeyException(code=APIKeyErrorCode.API_KEY_USER_MISMATCH)
        )

    return token_user or api_key_user
