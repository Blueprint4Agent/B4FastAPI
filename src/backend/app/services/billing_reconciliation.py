"""Bounded server-side reconciliation recovers missed webhook deliveries."""

from datetime import UTC, datetime, timedelta

from app.core.config.settings import SETTINGS
from app.core.observability.logging import get_logger
from app.models.billing import BillingCustomers
from app.services.billing import BillingService

logger = get_logger(__name__)


async def reconcile_subscriptions() -> None:
    if not SETTINGS.STRIPE_ENABLED:
        return
    service = BillingService()
    cutoff = datetime.now(UTC) - timedelta(minutes=5)
    users = await BillingCustomers.list_reconciliation_user_ids(
        livemode=service.config().livemode, cutoff=cutoff, limit=50
    )
    for user_id in users:
        try:
            await service.sync_subscription(user_id)
        except Exception:
            logger.warning("Subscription reconciliation failed (user_id=%s).", user_id)
