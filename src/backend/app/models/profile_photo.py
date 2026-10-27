"""Photo reference persistence with compare-and-swap against the visible revision."""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.core.db.session import get_db
from app.core.error import AuthErrorCode, AuthException
from app.models.user import User


@dataclass(frozen=True)
class PhotoSnapshot:
    url: str | None
    reference: dict | None


class PhotoPersistenceError(Exception):
    """Photo reference could not be read or written; commit outcome may be unknown."""


class ProfilePhotos:
    @staticmethod
    async def get(user_id: int) -> PhotoSnapshot:
        try:
            async with get_db() as db:
                row = (
                    await db.execute(
                        select(User.profile_image_url, User.profile_photo).where(
                            User.id == user_id, User.is_active.is_(True)
                        )
                    )
                ).first()
                if row is None:
                    raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
                return PhotoSnapshot(row.profile_image_url, row.profile_photo)
        except SQLAlchemyError as error:
            raise PhotoPersistenceError("Profile photo persistence failed") from error

    @staticmethod
    async def replace(
        user_id: int, expected_url: str | None, url: str | None, reference: dict | None
    ) -> bool:
        try:
            async with get_db() as db:
                result = await db.execute(
                    update(User)
                    .where(
                        User.id == user_id,
                        User.is_active.is_(True),
                        User.profile_image_url == expected_url,
                    )
                    .values(
                        profile_image_url=url, profile_photo=reference, updated_at=datetime.now(UTC)
                    )
                )
                await db.commit()
                return result.rowcount == 1
        except SQLAlchemyError as error:
            raise PhotoPersistenceError("Profile photo persistence failed") from error
