"""Durable, encrypted lifecycle mail; dedupe IDs survive payload erasure."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String, Text, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db


class Notification(Base):
    __tablename__ = "mail_notifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    payload: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lease: Mapped[str | None] = mapped_column(String(36))
    leased_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error: Mapped[str | None] = mapped_column(String(40))


class Notifications:
    @staticmethod
    async def add(row: Notification) -> None:
        key = row.id
        async with get_db() as db:
            db.add(row)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                if await db.get(Notification, key) is None:
                    raise

    @staticmethod
    async def claim() -> Notification | None:
        now = datetime.now(UTC)
        async with get_db() as db:
            # Expired recipient data is removed even from exhausted/disabled jobs.
            await db.execute(
                update(Notification)
                .where(Notification.expires_at <= now, Notification.payload.is_not(None))
                .values(payload=None, state="expired", lease=None)
            )
            eligible = (
                Notification.payload.is_not(None),
                Notification.available_at <= now,
                or_(
                    Notification.state == "pending",
                    (Notification.state == "sending") & (Notification.leased_until < now),
                ),
            )
            key = await db.scalar(
                select(Notification.id)
                .where(*eligible)
                .order_by(Notification.available_at)
                .limit(1)
            )
            if not key:
                await db.commit()
                return None
            lease = str(uuid4())
            result = await db.execute(
                update(Notification)
                .where(Notification.id == key, *eligible)
                .values(
                    state="sending",
                    lease=lease,
                    leased_until=now + timedelta(minutes=5),
                    attempts=Notification.attempts + 1,
                )
            )
            await db.commit()
            return await db.get(Notification, key) if result.rowcount else None

    @staticmethod
    async def finish(row: Notification, *, state: str, error: str | None = None) -> None:
        values = dict(
            state=state,
            lease=None,
            leased_until=None,
            error=error,
            available_at=datetime.now(UTC) + timedelta(minutes=min(30, 2**row.attempts)),
        )
        if state in ("sent", "skipped"):
            values["payload"] = None
        async with get_db() as db:
            await db.execute(
                update(Notification)
                .where(Notification.id == row.id, Notification.lease == row.lease)
                .values(**values)
            )
            await db.commit()
