"""Refresh stale DB subscription snapshots without browser polling."""

import asyncio

from app.core.celery.app import celery_app
from app.core.db.session import dispose_db


@celery_app.task(name="b4fastapi.billing.reconcile")
def reconcile_billing() -> None:
    from app.services.billing_reconciliation import reconcile_subscriptions

    async def run():
        try:
            await reconcile_subscriptions()
        finally:
            await dispose_db()

    asyncio.run(run())
