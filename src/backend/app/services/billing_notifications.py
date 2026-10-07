"""Only confirmed subscription starts and applied plan changes produce mail."""

import stripe

from app.core.config.settings import SETTINGS
from app.core.error.billing_exception import BillingErrorCode, BillingException
from app.models.billing import BillingCustomers
from app.services.billing import BillingService
from app.services.notifications import queue_notification


def _plan(price: str) -> str | None:
    known = BillingService._known_prices().get(price)
    if not known:
        return None
    return "Pro" if known[0].startswith("pro_") else "Plus"


def _mapping(value) -> dict:
    return value if isinstance(value, dict) else {}


def _price(obj: dict) -> str:
    items = _mapping(obj.get("items")).get("data", [])
    if not isinstance(items, list) or len(items) != 1:
        return ""
    return _mapping(_mapping(items[0]).get("price")).get("id", "")


class BillingNotificationService:
    async def receive(self, payload: bytes, signature: str) -> None:
        if not SETTINGS.STRIPE_ENABLED or not SETTINGS.STRIPE_WEBHOOK_SECRET:
            raise BillingException(BillingErrorCode.BILLING_WEBHOOK_UNAVAILABLE)
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, SETTINGS.STRIPE_WEBHOOK_SECRET
            ).to_dict()
        except (ValueError, stripe.SignatureVerificationError):
            raise BillingException(BillingErrorCode.BILLING_WEBHOOK_INVALID) from None
        if event.get("livemode") != BillingService().config().livemode:
            raise BillingException(BillingErrorCode.BILLING_WEBHOOK_INVALID)
        if not SETTINGS.EMAIL_ENABLED:
            return
        data = _mapping(event.get("data"))
        obj = _mapping(data.get("object"))
        customer = obj.get("customer")
        if not isinstance(customer, str):
            return
        user = await BillingCustomers.owner(customer, event["livemode"])
        if user is None:
            return
        event_type = event.get("type")
        kind, plan, key = None, None, None
        if (
            event_type == "invoice.paid"
            and obj.get("billing_reason") == "subscription_create"
            and obj.get("status") == "paid"
        ):
            sub_id = obj.get("subscription") or obj.get("parent", {}).get(
                "subscription_details", {}
            ).get("subscription")
            if not isinstance(sub_id, str):
                return
            async with BillingService()._provider() as client:
                sub = await client.v1.subscriptions.retrieve_async(sub_id)
            if (
                sub.customer != customer
                or sub.status != "active"
                or sub.livemode != event["livemode"]
            ):
                return
            plan = _plan(_price(sub.to_dict()))
            kind, key = "subscription_started", f"subscription-started:{sub_id}"
        elif (
            event_type == "customer.subscription.updated"
            and isinstance(obj.get("id"), str)
            and isinstance(event.get("created"), int)
        ):
            previous = _mapping(data.get("previous_attributes"))
            old_price, new_price = _price(previous), _price(obj)
            if (
                not old_price
                or not new_price
                or old_price == new_price
                or obj.get("status") != "active"
                or obj.get("pending_update")
            ):
                return
            async with BillingService()._provider() as client:
                sub = await client.v1.subscriptions.retrieve_async(obj["id"])
            if (
                sub.customer != customer
                or sub.status != "active"
                or sub.livemode != event["livemode"]
                or _price(sub.to_dict()) != new_price
            ):
                return  # A delayed/out-of-order event must not describe an obsolete plan.
            plan = _plan(new_price)
            kind, key = (
                "plan_changed",
                f"plan-changed:{obj['id']}:{event['created']}:{old_price}:{new_price}",
            )
        elif (
            event_type == "customer.subscription.deleted"
            and _mapping(obj.get("cancellation_details")).get("reason") == "cancellation_requested"
        ):
            if not isinstance(obj.get("id"), str) or obj.get("status") != "canceled":
                return
            async with BillingService()._provider() as client:
                if await BillingService()._subscriptions(client, customer):
                    return  # A newer subscription must not be reported as Free.
            kind, plan, key = "plan_changed", "Free", f"subscription-ended:{obj['id']}"
        if kind is None or plan is None:
            return
        language = _mapping(obj.get("metadata")).get("b4a_language", "en")
        await queue_notification(
            key, kind, email=user.email, name=user.name, plan=plan, language=language
        )
