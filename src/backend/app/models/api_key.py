from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    or_,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.session import Base, get_db
from app.core.error import APIKeyErrorCode, APIKeyException


class APIKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
        UniqueConstraint("user_id", "name", name="uq_api_keys_user_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    request_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="api_keys")


class APIKeyCreateForm(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None = None


class APIKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: datetime
    request_count: int
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    api_key: str
    key: APIKeyResponse


class APIKeysResponse(BaseModel):
    items: list[APIKeyResponse]


class APIKeyStatusUpdateForm(BaseModel):
    enabled: bool


class APIKeyRepository:
    async def record_valid_key_use(self, *, key_hash: str, now: datetime) -> APIKey | None:
        """Resolve a usable key and persist usage inside the repository session."""
        async with get_db() as db:
            result = await db.execute(
                select(APIKey).where(
                    APIKey.key_hash == key_hash,
                    APIKey.revoked_at.is_(None),
                    or_(APIKey.expires_at.is_(None), APIKey.expires_at > now),
                )
            )
            valid_key = result.scalar_one_or_none()
            if valid_key is None:
                return None
            valid_key.last_used_at = now
            valid_key.request_count += 1
            await db.commit()
            await db.refresh(valid_key)
            return valid_key

    async def create_api_key(
        self,
        *,
        user_id: int,
        name: str,
        key_prefix: str,
        key_hash: str,
        expires_at: datetime | None = None,
    ) -> APIKeyResponse:
        async with get_db() as db:
            api_key = APIKey(
                user_id=user_id,
                name=name,
                key_prefix=key_prefix,
                key_hash=key_hash,
                expires_at=expires_at,
            )
            db.add(api_key)
            try:
                await db.commit()
                await db.refresh(api_key)
            except IntegrityError as error:
                await db.rollback()
                message = str(error.orig).lower() if getattr(error, "orig", None) else ""
                code = (
                    APIKeyErrorCode.API_KEY_NAME_ALREADY_EXISTS
                    if "uq_api_keys_user_name" in message
                    or "api_keys.user_id, api_keys.name" in message
                    else APIKeyErrorCode.API_KEY_CREATE_FAILED
                )
                raise APIKeyException(code=code) from error
            return APIKeyResponse.model_validate(api_key)

    async def list_api_keys(self, *, user_id: int) -> list[APIKeyResponse]:
        async with get_db() as db:
            result = await db.execute(
                select(APIKey)
                .where(APIKey.user_id == user_id)
                .order_by(APIKey.created_at.desc(), APIKey.id.desc())
            )
            return [APIKeyResponse.model_validate(row) for row in result.scalars().all()]

    async def delete_api_key(self, *, user_id: int, api_key_id: int) -> APIKeyResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(APIKey).where(APIKey.id == api_key_id, APIKey.user_id == user_id)
            )
            api_key = result.scalar_one_or_none()
            if api_key is None:
                return None

            response_payload = APIKeyResponse.model_validate(api_key)
            await db.delete(api_key)
            await db.commit()
            return response_payload

    async def set_api_key_enabled(
        self,
        *,
        user_id: int,
        api_key_id: int,
        enabled: bool,
    ) -> APIKeyResponse | None:
        async with get_db() as db:
            result = await db.execute(
                select(APIKey).where(APIKey.id == api_key_id, APIKey.user_id == user_id)
            )
            api_key = result.scalar_one_or_none()
            if api_key is None:
                return None

            if enabled:
                api_key.revoked_at = None
            elif api_key.revoked_at is None:
                api_key.revoked_at = datetime.now(UTC)

            await db.commit()
            await db.refresh(api_key)
            return APIKeyResponse.model_validate(api_key)


APIKeys = APIKeyRepository()
