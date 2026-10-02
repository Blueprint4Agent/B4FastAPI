"""Hosted registration and subscriptions; Stripe remains the billing source of truth."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import urlsplit

import stripe

from app.core.config.settings import SETTINGS
from app.core.error.billing_exception import BillingErrorCode, BillingException
from app.core.observability.logging import get_logger
from app.core.observability.service import observe_service
from app.models.billing import (
    BillingCheckoutForm,
    BillingCheckouts,
    BillingCheckoutStatusResponse,
    BillingConfigResponse,
    BillingCustomers,
    BillingPaymentMethodResponse,
    BillingPaymentMethodsResponse,
    BillingPlansResponse,
    BillingPriceResponse,
    BillingSetupForm,
    BillingSetupResponse,
    BillingSetupStatusResponse,
    BillingSubscriptionResponse,
)

logger = get_logger("app.service.billing")


class BillingService:
    def _configuration_errors(self) -> list[str]:
        key = SETTINGS.STRIPE_SECRET_KEY.strip()
        prefixes = ("sk_test_", "rk_test_", "sk_live_", "rk_live_")
        livemode = key.startswith(("sk_live_", "rk_live_"))
        errors = []
        if not any(key.startswith(prefix) and len(key) > len(prefix) for prefix in prefixes):
            errors.append("STRIPE_SECRET_KEY must be a Stripe secret or restricted API key.")
        for name, url in (
            ("STRIPE_SETUP_SUCCESS_URL", SETTINGS.STRIPE_SETUP_SUCCESS_URL),
            ("STRIPE_SETUP_CANCEL_URL", SETTINGS.STRIPE_SETUP_CANCEL_URL),
        ):
            if not self._valid_url(url, livemode):
                errors.append(
                    f"{name} must be an absolute HTTP(S) URL without credentials or a fragment; "
                    "live mode requires HTTPS."
                )
        if SETTINGS.STRIPE_SUBSCRIPTIONS_ENABLED:
            for name in ("STRIPE_CHECKOUT_SUCCESS_URL", "STRIPE_CHECKOUT_CANCEL_URL"):
                if not self._valid_url(getattr(SETTINGS, name), livemode):
                    errors.append(f"{name} must be a valid absolute return URL.")
            if "{CHECKOUT_SESSION_ID}" not in SETTINGS.STRIPE_CHECKOUT_SUCCESS_URL:
                errors.append("STRIPE_CHECKOUT_SUCCESS_URL must contain {CHECKOUT_SESSION_ID}.")
            for price in self._price_ids().values():
                if not price.startswith("price_"):
                    errors.append("All subscription Price IDs must be configured.")
        if "{CHECKOUT_SESSION_ID}" not in SETTINGS.STRIPE_SETUP_SUCCESS_URL:
            errors.append("STRIPE_SETUP_SUCCESS_URL must contain {CHECKOUT_SESSION_ID}.")
        return errors

    def config(self) -> BillingConfigResponse:
        return BillingConfigResponse(
            enabled=SETTINGS.STRIPE_ENABLED and not self._configuration_errors(),
            livemode=SETTINGS.STRIPE_SECRET_KEY.strip().startswith(("sk_live_", "rk_live_")),
        )

    async def initialize(self) -> None:
        if not SETTINGS.STRIPE_ENABLED:
            logger.info("Stripe integration is disabled.")
            return
        errors = self._configuration_errors()
        if errors:
            raise RuntimeError("Invalid Stripe configuration: " + " ".join(errors))
        mode = "live" if self.config().livemode else "test"
        logger.info("Stripe startup verification started (mode=%s).", mode)
        try:
            async with self._provider() as client:
                try:
                    # Authenticate against the API this integration actually uses.
                    # Read at most one entry; never create resources or log its contents.
                    await client.v1.checkout.sessions.list_async(params={"limit": 1})
                    if SETTINGS.STRIPE_SUBSCRIPTIONS_ENABLED:
                        for (plan, currency), price_id in self._price_ids().items():
                            await self._price(client, plan, currency, price_id)
                except stripe.AuthenticationError:
                    raise RuntimeError(
                        "Stripe startup verification failed: authentication rejected. "
                        "Check STRIPE_SECRET_KEY."
                    ) from None
                except stripe.PermissionError:
                    raise RuntimeError(
                        "Stripe startup verification failed: Billing read permission denied. "
                        "Check the Stripe API key permissions."
                    ) from None
        except BillingException as error:
            if error.code.error == "BILLING_PLAN_UNAVAILABLE":
                raise RuntimeError(
                    "Stripe startup verification failed: configured recurring prices do not match the required plan, currency or mode."
                ) from None
            raise RuntimeError(
                "Stripe startup verification failed: Billing API request failed or timed out. "
                "Check network connectivity, Stripe availability and API key permissions."
            ) from None
        logger.info("Stripe startup verification succeeded (mode=%s).", mode)

    @staticmethod
    def _valid_url(url: str, livemode: bool) -> bool:
        try:
            parsed = urlsplit(url)
            _ = parsed.port  # Reject malformed/out-of-range ports during configuration validation.
            return bool(
                parsed.scheme in ("http", "https")
                and parsed.hostname
                and not parsed.username
                and not parsed.password
                and not parsed.fragment
                and (not livemode or parsed.scheme == "https")
            )
        except ValueError:
            return False

    @asynccontextmanager
    async def _provider(self) -> AsyncIterator[stripe.StripeClient]:
        if not self.config().enabled:
            raise BillingException(BillingErrorCode.BILLING_DISABLED)
        http = stripe.HTTPXClient(timeout=5)
        client = stripe.StripeClient(
            SETTINGS.STRIPE_SECRET_KEY.strip(), http_client=http, max_network_retries=1
        )
        try:
            async with asyncio.timeout(20):
                yield client
        except (stripe.StripeError, TimeoutError):
            # Never expose provider exception text, keys, URLs or payment payloads.
            raise BillingException(BillingErrorCode.BILLING_UNAVAILABLE) from None
        finally:
            await http.close_async()
            http.close()

    async def _customer(self, client: stripe.StripeClient, user_id: int) -> str:
        livemode = self.config().livemode
        row = await BillingCustomers.reserve(user_id, livemode)
        if row.stripe_customer_id:
            return row.stripe_customer_id
        created = row.created_at.replace(tzinfo=UTC)
        # Stripe may prune idempotency keys after 24h. Do not create a duplicate
        # after an ambiguous remote success/local commit failure outside that window.
        if datetime.now(UTC) - created >= timedelta(hours=23):
            raise BillingException(BillingErrorCode.BILLING_RECONCILIATION_REQUIRED)
        customer = await client.v1.customers.create_async(
            params={"metadata": {"billing_identity": row.creation_key, "user_id": str(user_id)}},
            options={"idempotency_key": f"billing-customer:{row.creation_key}"},
        )
        return await BillingCustomers.bind(user_id, livemode, customer.id)

    @observe_service("billing.create_setup")
    async def create_setup(self, user_id: int, form: BillingSetupForm) -> BillingSetupResponse:
        async with self._provider() as client:
            customer_id = await self._customer(client, user_id)
            session = await client.v1.checkout.sessions.create_async(
                params={
                    "mode": "setup",
                    "customer": customer_id,
                    "client_reference_id": str(user_id),
                    "payment_method_types": ["card", "link"],
                    "success_url": SETTINGS.STRIPE_SETUP_SUCCESS_URL,
                    "cancel_url": SETTINGS.STRIPE_SETUP_CANCEL_URL,
                    "setup_intent_data": {"metadata": {"user_id": str(user_id)}},
                },
                options={"idempotency_key": f"billing-setup:{customer_id}:{form.request_id}"},
            )
            if not session.url:
                raise BillingException(BillingErrorCode.BILLING_UNAVAILABLE)
            return BillingSetupResponse(id=session.id, url=session.url)

    @observe_service("billing.setup_status")
    async def setup_status(self, user_id: int, session_id: str) -> BillingSetupStatusResponse:
        async with self._provider() as client:
            row = await BillingCustomers.get(user_id, self.config().livemode)
            if row is None or row.stripe_customer_id is None:
                raise BillingException(BillingErrorCode.BILLING_NOT_FOUND)
            try:
                session = await client.v1.checkout.sessions.retrieve_async(
                    session_id, params={"expand": ["setup_intent"]}
                )
            except stripe.InvalidRequestError as exc:
                if exc.code == "resource_missing":
                    raise BillingException(BillingErrorCode.BILLING_NOT_FOUND) from None
                raise
            if (
                session.mode != "setup"
                or session.customer != row.stripe_customer_id
                or session.client_reference_id != str(user_id)
                or session.livemode != row.livemode
            ):
                raise BillingException(BillingErrorCode.BILLING_NOT_FOUND)
            intent = session.setup_intent
            registered = bool(
                session.status == "complete"
                and intent
                and not isinstance(intent, str)
                and intent.status == "succeeded"
                and intent.customer == row.stripe_customer_id
                and intent.payment_method
            )
            return BillingSetupStatusResponse(
                id=session.id, status=session.status, registered=registered
            )

    @observe_service("billing.list_payment_methods")
    async def list_payment_methods(
        self,
        user_id: int,
        method_type: Literal["card", "link"],
        limit: int,
        starting_after: str | None,
    ) -> BillingPaymentMethodsResponse:
        async with self._provider() as client:
            row = await BillingCustomers.get(user_id, self.config().livemode)
            if row is None or row.stripe_customer_id is None:
                return BillingPaymentMethodsResponse(items=[], has_more=False)
            params = {"type": method_type, "limit": limit}
            if starting_after:
                params["starting_after"] = starting_after
            methods = await client.v1.customers.payment_methods.list_async(
                row.stripe_customer_id, params=params
            )
            items = []
            for method in methods.data:
                card = method.card if method.type == "card" else None
                items.append(
                    BillingPaymentMethodResponse(
                        id=method.id,
                        type=method.type,
                        brand=card.brand if card else None,
                        last4=card.last4 if card else None,
                        exp_month=card.exp_month if card else None,
                        exp_year=card.exp_year if card else None,
                    )
                )
            return BillingPaymentMethodsResponse(
                items=items,
                has_more=methods.has_more,
                next_cursor=items[-1].id if methods.has_more and items else None,
            )

    @staticmethod
    def _price_ids() -> dict[tuple[str, str], str]:
        return {
            (plan, currency): getattr(
                SETTINGS, f"STRIPE_{plan.upper()}_{currency.upper()}_PRICE_ID"
            ).strip()
            for plan in ("monthly", "annual")
            for currency in ("krw", "usd")
        }

    async def _price(
        self, client: stripe.StripeClient, plan: str, currency: str, price_id: str
    ) -> BillingPriceResponse:
        price = await client.v1.prices.retrieve_async(price_id)
        recurring = price.recurring
        if (
            not price.active
            or price.livemode != self.config().livemode
            or price.currency != currency
            or price.unit_amount is None
            or price.unit_amount <= 0
            or price.billing_scheme != "per_unit"
            or not recurring
            or recurring.interval != ("month" if plan == "monthly" else "year")
            or recurring.interval_count != 1
            or recurring.usage_type != "licensed"
        ):
            raise BillingException(BillingErrorCode.BILLING_PLAN_UNAVAILABLE)
        return BillingPriceResponse(plan=plan, currency=currency, amount=price.unit_amount)

    @observe_service("billing.plans")
    async def plans(self) -> BillingPlansResponse:
        config = self.config()
        if not config.enabled or not SETTINGS.STRIPE_SUBSCRIPTIONS_ENABLED:
            return BillingPlansResponse(enabled=False, livemode=config.livemode, prices=[])
        async with self._provider() as client:
            prices = [
                await self._price(client, plan, currency, price_id)
                for (plan, currency), price_id in self._price_ids().items()
            ]
        return BillingPlansResponse(enabled=True, livemode=config.livemode, prices=prices)

    async def _subscriptions(
        self, client: stripe.StripeClient, customer_id: str
    ) -> list[stripe.Subscription]:
        subscriptions = await client.v1.subscriptions.list_async(
            params={
                "customer": customer_id,
                "status": "all",
                "limit": 100,
            }
        )
        # Never silently treat an incomplete page as Free or permit another purchase.
        if subscriptions.has_more:
            raise BillingException(BillingErrorCode.BILLING_RECONCILIATION_REQUIRED)
        return [
            item
            for item in subscriptions.data
            if item.status not in ("canceled", "incomplete_expired")
        ]

    def _subscription_response(
        self, subscription: stripe.Subscription
    ) -> BillingSubscriptionResponse:
        items = subscription["items"].data
        mapped = {value: key for key, value in self._price_ids().items()}
        match = mapped.get(items[0].price.id) if len(items) == 1 else None
        return BillingSubscriptionResponse(
            plan=match[0] if match else "unknown",
            status=subscription.status,
            currency=subscription.currency,
            current_period_end=getattr(items[0], "current_period_end", None)
            if len(items) == 1
            else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
            has_subscription=True,
        )

    @observe_service("billing.subscription")
    async def subscription(self, user_id: int) -> BillingSubscriptionResponse:
        async with self._provider() as client:
            row = await BillingCustomers.get(user_id, self.config().livemode)
            if row is None or row.stripe_customer_id is None:
                return BillingSubscriptionResponse(plan="free", status="none")
            subscriptions = await self._subscriptions(client, row.stripe_customer_id)
            if len(subscriptions) > 1:
                raise BillingException(BillingErrorCode.BILLING_RECONCILIATION_REQUIRED)
            return (
                self._subscription_response(subscriptions[0])
                if subscriptions
                else BillingSubscriptionResponse(plan="free", status="none")
            )

    @observe_service("billing.create_checkout")
    async def create_checkout(
        self, user_id: int, form: BillingCheckoutForm
    ) -> BillingSetupResponse:
        if not SETTINGS.STRIPE_SUBSCRIPTIONS_ENABLED:
            raise BillingException(BillingErrorCode.BILLING_PLAN_UNAVAILABLE)
        async with self._provider() as client:
            price_id = self._price_ids()[(form.plan, form.currency)]
            await self._price(client, form.plan, form.currency, price_id)
            customer_id = await self._customer(client, user_id)
            reservation = await BillingCheckouts.reserve(user_id, self.config().livemode, price_id)
            # This read follows reservation so a just-completed expired attempt is observed.
            if await self._subscriptions(client, customer_id):
                raise BillingException(BillingErrorCode.BILLING_CHECKOUT_CONFLICT)
            expires_at = int(reservation.expires_at.replace(tzinfo=UTC).timestamp())
            if (
                reservation.price_id != price_id
                or expires_at - int(datetime.now(UTC).timestamp()) < 31 * 60
            ):
                # Never change the parameters of an ambiguous reserved attempt or extend it.
                raise BillingException(BillingErrorCode.BILLING_CHECKOUT_CONFLICT)
            session = await client.v1.checkout.sessions.create_async(
                params={
                    "mode": "subscription",
                    "customer": customer_id,
                    "client_reference_id": str(user_id),
                    "line_items": [{"price": price_id, "quantity": 1}],
                    "payment_method_types": ["card", "link"],
                    "success_url": SETTINGS.STRIPE_CHECKOUT_SUCCESS_URL,
                    "cancel_url": SETTINGS.STRIPE_CHECKOUT_CANCEL_URL,
                    "expires_at": expires_at,
                    "subscription_data": {"metadata": {"user_id": str(user_id)}},
                },
                options={
                    "idempotency_key": f"billing-checkout:{customer_id}:{reservation.creation_key}"
                },
            )
            if session.status != "open" or not session.url:
                raise BillingException(BillingErrorCode.BILLING_CHECKOUT_CONFLICT)
            return BillingSetupResponse(id=session.id, url=session.url)

    @observe_service("billing.checkout_status")
    async def checkout_status(self, user_id: int, session_id: str) -> BillingCheckoutStatusResponse:
        async with self._provider() as client:
            row = await BillingCustomers.get(user_id, self.config().livemode)
            if row is None or row.stripe_customer_id is None:
                raise BillingException(BillingErrorCode.BILLING_NOT_FOUND)
            try:
                session = await client.v1.checkout.sessions.retrieve_async(
                    session_id, params={"expand": ["subscription"]}
                )
            except stripe.InvalidRequestError as exc:
                if exc.code == "resource_missing":
                    raise BillingException(BillingErrorCode.BILLING_NOT_FOUND) from None
                raise
            if (
                session.mode != "subscription"
                or session.customer != row.stripe_customer_id
                or session.client_reference_id != str(user_id)
                or session.livemode != row.livemode
            ):
                raise BillingException(BillingErrorCode.BILLING_NOT_FOUND)
            subscription = session.subscription
            paid = bool(
                session.status == "complete"
                and session.payment_status == "paid"
                and subscription
                and not isinstance(subscription, str)
                and subscription.customer == row.stripe_customer_id
                and subscription.status == "active"
            )
            return BillingCheckoutStatusResponse(id=session.id, status=session.status, paid=paid)
