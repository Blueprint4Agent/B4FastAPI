"""Only confirmed subscription starts and applied plan changes produce mail."""

import stripe

from app.core.config.settings import SETTINGS
from app.core.error.billing_exception import BillingErrorCode, BillingException
from app.models.billing import BillingCustomers
from app.models.inbox import INBOX
from app.services.billing import BillingService
from app.services.inbox import InboxService
from app.services.notifications import queue_notification
from app.utils.billing import subscription_price_id


def _mapping(value) -> dict:
    return value if isinstance(value, dict) else {}


def _invoice_price(obj: dict) -> str:
    lines = _mapping(obj.get("lines"))
    items = lines.get("data", [])
    if lines.get("has_more") or not isinstance(items, list) or len(items) != 1:
        return ""
    line = _mapping(items[0])
    return _mapping(line.get("price")).get("id", "") or _mapping(
        _mapping(line.get("pricing")).get("price_details")
    ).get("price", "")


class BillingNotificationService:
    async def receive(self, payload: bytes, signature: str) -> None:
        billing = BillingService()
        if not SETTINGS.STRIPE_ENABLED or not SETTINGS.STRIPE_WEBHOOK_SECRET:
            raise BillingException(BillingErrorCode.BILLING_WEBHOOK_UNAVAILABLE)
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, SETTINGS.STRIPE_WEBHOOK_SECRET
            ).to_dict()
        except (ValueError, stripe.SignatureVerificationError):
            raise BillingException(BillingErrorCode.BILLING_WEBHOOK_INVALID) from None
        if event.get("livemode") != billing.config().livemode:
            raise BillingException(BillingErrorCode.BILLING_WEBHOOK_INVALID)
        data = _mapping(event.get("data"))
        obj = _mapping(data.get("object"))
        customer = obj.get("customer")
        if not isinstance(customer, str):
            return
        user = await BillingCustomers.owner(customer, event["livemode"])
        if user is None:
            return
        event_type = event.get("type")
        sync_events = {
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
            "customer.subscription.paused",
            "customer.subscription.resumed",
            "invoice.paid",
            "invoice.payment_failed",
            "invoice.payment_action_required",
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
            "checkout.session.async_payment_failed",
            "subscription_schedule.updated",
            "subscription_schedule.released",
            "subscription_schedule.canceled",
            "subscription_schedule.completed",
            "subscription_schedule.aborted",
        }
        if event_type in sync_events:
            # Fetch current provider state under a customer lock: duplicate or older payloads
            # cannot roll the DB back to an obsolete plan. Failure returns non-2xx for redelivery.
            await billing.sync_subscription(user.id)
        kind, plan, key = None, None, None
        previous_key = None
        if (
            event_type == "invoice.paid"
            and obj.get("billing_reason") == "subscription_create"
            and obj.get("status") == "paid"
        ):
            sub_id = obj.get("subscription") or _mapping(
                _mapping(obj.get("parent")).get("subscription_details")
            ).get("subscription")
            if not isinstance(sub_id, str):
                return
            plan = await billing.confirmed_notification_plan(
                customer_id=customer,
                subscription_id=sub_id,
                livemode=event["livemode"],
                expected_price_id=_invoice_price(obj),
            )
            if plan is None:
                return
            kind, key = "subscription_started", f"subscription-started:{sub_id}"
        elif (
            event_type == "customer.subscription.updated"
            and isinstance(obj.get("id"), str)
            and isinstance(event.get("id"), str)
        ):
            previous = _mapping(data.get("previous_attributes"))
            old_price, new_price = subscription_price_id(previous), subscription_price_id(obj)
            if (
                not old_price
                or not new_price
                or old_price == new_price
                or obj.get("status") != "active"
                or obj.get("pending_update")
            ):
                return
            plan = await billing.confirmed_notification_plan(
                customer_id=customer,
                subscription_id=obj["id"],
                livemode=event["livemode"],
                expected_price_id=new_price,
                reject_pending_update=True,
            )
            if plan is None:
                return  # A delayed/out-of-order event must not describe an obsolete plan.
            kind, key = (
                "plan_changed",
                f"plan-changed:{obj['id']}:{event['id']}",
            )
            if isinstance(event.get("created"), int):
                previous_key = (
                    f"plan-changed:{obj['id']}:{event['created']}:{old_price}:{new_price}"
                )
        elif (
            event_type == "customer.subscription.deleted"
            and _mapping(obj.get("cancellation_details")).get("reason") == "cancellation_requested"
        ):
            if not isinstance(obj.get("id"), str) or obj.get("status") != "canceled":
                return
            if await billing.has_current_subscription(customer):
                return  # A newer subscription must not be reported as Free.
            kind, plan, key = "plan_changed", "Free", f"subscription-ended:{obj['id']}"
        if kind is None or plan is None:
            return
        created = await INBOX.deliver(
            key=key,
            user_id=user.id,
            kind=kind,
            title="Subscription started" if kind == "subscription_started" else "Plan changed",
            body=plan,
            action_path="/settings?section=billing",
        )
        if created:
            await InboxService().changed(user.id)
        if not SETTINGS.EMAIL_ENABLED:
            return
        # Provider customer locales survive invoice metadata differences and delayed events.
        language = await billing.notification_language(
            customer_id=customer, livemode=event["livemode"]
        )
        await queue_notification(
            key,
            kind,
            previous_key=previous_key,
            email=user.email,
            name=user.name,
            plan=plan,
            language=language,
        )
