"""Customer identities and bounded Checkout reservations; Stripe owns billing state."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, String, select, text, update
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
    @asynccontextmanager
    async def locked(user_id: int, livemode: bool) -> AsyncIterator[BillingCustomer | None]:
        """Serialize changes across workers; release the lock when provider work finishes."""
        async with get_db() as db:
            if db.bind.dialect.name == "sqlite":
                await db.execute(text("BEGIN IMMEDIATE"))
            row = await db.scalar(
                select(BillingCustomer)
                .where(BillingCustomer.user_id == user_id, BillingCustomer.livemode == livemode)
                .with_for_update()
            )
            yield row
            await db.commit()

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


class BillingCheckout(Base):
    """One bounded Checkout attempt per customer/mode, shared across devices/workers."""

    __tablename__ = "billing_checkouts"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    livemode: Mapped[bool] = mapped_column(Boolean, primary_key=True)
    creation_key: Mapped[str] = mapped_column(String(36), nullable=False)
    price_id: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BillingCheckouts:
    @staticmethod
    async def reserve(user_id: int, livemode: bool, price_id: str) -> BillingCheckout:
        from datetime import timedelta

        now = datetime.now(UTC)
        values = dict(
            creation_key=str(uuid4()), price_id=price_id, expires_at=now + timedelta(hours=1)
        )
        async with get_db() as db:
            await db.execute(
                update(BillingCheckout)
                .where(
                    BillingCheckout.user_id == user_id,
                    BillingCheckout.livemode == livemode,
                    BillingCheckout.expires_at <= now,
                )
                .values(**values)
            )
            await db.commit()
            row = await db.get(BillingCheckout, (user_id, livemode))
            if row is not None:
                return row
            row = BillingCheckout(user_id=user_id, livemode=livemode, **values)
            db.add(row)
            try:
                await db.commit()
                return row
            except IntegrityError:
                await db.rollback()
                existing = await db.get(BillingCheckout, (user_id, livemode))
                if existing is None:
                    raise
                return existing


class BillingPriceResponse(BaseModel):
    plan: Literal["monthly", "annual"]
    currency: Literal["krw", "usd"]
    amount: int = Field(ge=0, description="Minor currency units; KRW has no decimal places.")


class BillingPlansResponse(BaseModel):
    enabled: bool
    livemode: bool
    prices: list[BillingPriceResponse]


class BillingCheckoutForm(BillingSetupForm):
    plan: Literal["monthly", "annual"]
    currency: Literal["krw", "usd"]


class BillingSubscriptionResponse(BaseModel):
    plan: Literal["free", "monthly", "annual", "unknown"]
    status: str
    currency: str | None = None
    current_period_end: int | None = None
    cancel_at_period_end: bool = False
    has_subscription: bool = False
    can_manage: bool = False
    change_version: str | None = None
    pending_plan: Literal["free", "monthly", "annual"] | None = None
    pending_effective_at: int | None = None


class BillingCheckoutStatusResponse(BaseModel):
    id: str
    status: Literal["open", "complete", "expired"]
    paid: bool


class BillingChangeForm(BillingSetupForm):
    plan: Literal["free", "monthly", "annual", "keep"]
    expected_version: str = Field(pattern=r"^[a-f0-9]{64}$")


class BillingProfileResponse(BaseModel):
    email: str | None = None
    name: str | None = None
    address: list[str] = Field(default_factory=list)
    default_payment_method: str | None = None
    portal_enabled: bool = False


class BillingInvoiceResponse(BaseModel):
    id: str
    number: str | None = None
    created: int
    status: str
    amount: int
    currency: str
    url: str | None = None


class BillingInvoicesResponse(BaseModel):
    items: list[BillingInvoiceResponse]
    has_more: bool


class BillingPortalForm(BillingSetupForm):
    flow: Literal["overview", "payment_method_update", "customer_update"] = "overview"
