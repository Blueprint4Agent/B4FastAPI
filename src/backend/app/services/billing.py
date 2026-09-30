"""Charge-free registration; Stripe remains the authoritative payment-method store."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Literal
from urllib.parse import urlsplit

import stripe

from app.core.config.settings import SETTINGS
from app.core.error.billing_exception import BillingErrorCode, BillingException
from app.core.observability.service import observe_service
from app.models.billing import (
    BillingConfigResponse,
    BillingCustomers,
    BillingPaymentMethodResponse,
    BillingPaymentMethodsResponse,
    BillingSetupForm,
    BillingSetupResponse,
    BillingSetupStatusResponse,
)


class BillingService:
    def config(self) -> BillingConfigResponse:
        key = SETTINGS.STRIPE_SECRET_KEY.strip()
        livemode = key.startswith(("sk_live_", "rk_live_"))
        valid_key = key.startswith(("sk_test_", "rk_test_", "sk_live_", "rk_live_"))
        urls = [SETTINGS.STRIPE_SETUP_SUCCESS_URL, SETTINGS.STRIPE_SETUP_CANCEL_URL]
        valid_urls = all(self._valid_url(url, livemode) for url in urls)
        return BillingConfigResponse(
            enabled=bool(
                SETTINGS.STRIPE_ENABLED
                and valid_key
                and valid_urls
                and "{CHECKOUT_SESSION_ID}" in urls[0]
            ),
            livemode=livemode,
        )

    @staticmethod
    def _valid_url(url: str, livemode: bool) -> bool:
        try:
            parsed = urlsplit(url)
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
