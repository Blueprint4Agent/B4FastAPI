"""Customer identity only; Stripe owns payment credentials and registration state."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, String, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.session import Base, get_db


class BillingCustomer(Base):
    __tablename__ = "billing_customers"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    livemode: Mapped[bool] = mapped_column(Boolean, primary_key=True)
    creation_key: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BillingCustomers:
    @staticmethod
    async def get(user_id: int, livemode: bool) -> BillingCustomer | None:
        async with get_db() as db:
            return await db.get(BillingCustomer, (user_id, livemode))

    @staticmethod
    async def reserve(user_id: int, livemode: bool) -> BillingCustomer:
        existing = await BillingCustomers.get(user_id, livemode)
        if existing is not None:
            return existing
        async with get_db() as db:
            row = BillingCustomer(
                user_id=user_id,
                livemode=livemode,
                creation_key=str(uuid4()),
                created_at=datetime.now(UTC),
            )
            db.add(row)
            try:
                await db.commit()
                return row
            except IntegrityError:
                await db.rollback()
                existing = await db.get(BillingCustomer, (user_id, livemode))
                if existing is None:
                    raise
                return existing

    @staticmethod
    async def bind(user_id: int, livemode: bool, customer_id: str) -> str:
        async with get_db() as db:
            await db.execute(
                update(BillingCustomer)
                .where(
                    BillingCustomer.user_id == user_id,
                    BillingCustomer.livemode == livemode,
                    BillingCustomer.stripe_customer_id.is_(None),
                )
                .values(stripe_customer_id=customer_id)
            )
            await db.commit()
            result = await db.scalar(
                select(BillingCustomer.stripe_customer_id).where(
                    BillingCustomer.user_id == user_id, BillingCustomer.livemode == livemode
                )
            )
            if result is None:
                raise RuntimeError("Billing customer reservation no longer exists.")
            return result


class BillingConfigResponse(BaseModel):
    enabled: bool
    livemode: bool


class BillingSetupForm(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID = Field(description="Reuse this UUID when retrying the same setup request.")


class BillingSetupResponse(BaseModel):
    id: str
    url: str


class BillingSetupStatusResponse(BaseModel):
    id: str
    status: Literal["open", "complete", "expired"]
    registered: bool


class BillingPaymentMethodResponse(BaseModel):
    id: str
    type: Literal["card", "link"]
    brand: str | None = None
    last4: str | None = None
    exp_month: int | None = None
    exp_year: int | None = None


class BillingPaymentMethodsResponse(BaseModel):
    items: list[BillingPaymentMethodResponse]
    has_more: bool
    next_cursor: str | None = None
