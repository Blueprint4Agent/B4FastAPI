import hashlib
import hmac
import secrets

from sqlalchemy.exc import IntegrityError

from app.core.error import APIKeyErrorCode, APIKeyException
from app.core.settings import SETTINGS
from app.models.api_key import (
    APIKeyCreateForm,
    APIKeyCreateResponse,
    APIKeyResponse,
    APIKeys,
    APIKeysResponse,
)

API_KEY_PREFIX = "sk_live_"
API_KEY_SECRET_BYTES = 32
API_KEY_VISIBLE_PREFIX_LENGTH = 12


class APIKeyService:
    async def create_api_key(self, *, user_id: int, form: APIKeyCreateForm) -> APIKeyCreateResponse:
        raw_api_key = self._generate_api_key()
        key_hash = self._hash_api_key(raw_api_key)
        key_prefix = raw_api_key[:API_KEY_VISIBLE_PREFIX_LENGTH]
        try:
            created = await APIKeys.create_api_key(
                user_id=user_id,
                name=form.name.strip(),
                key_prefix=key_prefix,
                key_hash=key_hash,
            )
        except IntegrityError as error:
            message = str(error.orig).lower() if getattr(error, "orig", None) else ""
            if "uq_api_keys_user_name" in message or "api_keys.user_id, api_keys.name" in message:
                raise APIKeyException(code=APIKeyErrorCode.API_KEY_NAME_ALREADY_EXISTS) from error
            raise APIKeyException(code=APIKeyErrorCode.API_KEY_CREATE_FAILED) from error

        return APIKeyCreateResponse(api_key=raw_api_key, key=created)

    async def list_api_keys(self, *, user_id: int) -> APIKeysResponse:
        keys = await APIKeys.list_api_keys(user_id=user_id)
        return APIKeysResponse(items=keys)

    async def revoke_api_key(self, *, user_id: int, api_key_id: int) -> APIKeyResponse:
        revoked = await APIKeys.revoke_api_key(user_id=user_id, api_key_id=api_key_id)
        if revoked is None:
            raise APIKeyException(code=APIKeyErrorCode.API_KEY_NOT_FOUND)
        return revoked

    def _generate_api_key(self) -> str:
        secret = secrets.token_urlsafe(API_KEY_SECRET_BYTES)
        return f"{API_KEY_PREFIX}{secret}"

    def _hash_api_key(self, api_key: str) -> str:
        # Persist only a keyed digest so raw API keys cannot be recovered from DB.
        return hmac.new(
            SETTINGS.SECRET_KEY.encode("utf-8"),
            api_key.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
