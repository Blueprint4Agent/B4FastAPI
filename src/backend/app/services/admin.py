import asyncio
from datetime import UTC, datetime
from urllib.parse import urlsplit

from app.core.config import SETTINGS
from app.core.db.session import get_engine
from app.core.error.admin_exception import AdminErrorCode, AdminException
from app.core.mail.service import MAIL_SERVICE
from app.core.object_storage import ObjectStorage
from app.core.observability.health import check_dependencies
from app.core.observability.integration_health import INTEGRATION_HEALTH
from app.core.observability.service import observe_service
from app.core.observability.startup_checks import STARTUP_CHECKS, StartupCheck
from app.models.admin import (
    AdminConnection,
    AdminEnvironment,
    AdminEnvironmentValues,
    AdminStatusResponse,
)
from app.services.billing import BillingService


class AdminService:
    @observe_service("admin.status")
    async def status(self, storage: ObjectStorage | None = None) -> AdminStatusResponse:
        try:
            billing_service = BillingService()
            billing = billing_service.config()

            async def storage_probe() -> None:
                if storage is None:
                    raise RuntimeError("Storage is not initialized")
                await storage.check_connection()

            checks, email_check, billing_check, storage_check = await asyncio.gather(
                check_dependencies(),
                INTEGRATION_HEALTH.check(
                    "email", SETTINGS.EMAIL_ENABLED, MAIL_SERVICE.check_connection
                ),
                INTEGRATION_HEALTH.check(
                    "billing", billing.enabled, billing_service.check_connection
                ),
                INTEGRATION_HEALTH.check("object_storage", True, storage_probe),
            )
            transport, storage_port = "filesystem", None
            if SETTINGS.OBJECT_STORAGE_PROVIDER != "local":
                transport = "https"
                storage_port = 443
                endpoint = SETTINGS.OBJECT_STORAGE_S3_ENDPOINT_URL
                if endpoint:
                    try:
                        parsed = urlsplit(endpoint)
                        transport = parsed.scheme if parsed.scheme in {"https", "http"} else None
                        storage_port = (
                            (parsed.port or (443 if transport == "https" else 80))
                            if transport
                            else None
                        )
                    except ValueError:
                        transport, storage_port = None, None
            engine = get_engine()
            dialect = engine.dialect.name
            database = (
                dialect if dialect in {"sqlite", "postgresql", "mysql", "mariadb"} else "database"
            )
            cache_host, cache_port = None, None
            if not SETTINGS.REDIS_IN_MEMORY:
                try:
                    redis_url = urlsplit(SETTINGS.REDIS_URL)
                    if redis_url.scheme in {"redis", "rediss"}:
                        cache_host, cache_port = redis_url.hostname, redis_url.port or 6379
                except ValueError:
                    pass  # Failed connectivity is reported without returning malformed secrets.
            return AdminStatusResponse(
                status="ok"
                if all(check.status == "ok" for check in checks.values())
                and all(
                    check.status in {"ok", "disabled"}
                    for check in (email_check, billing_check, storage_check)
                )
                else "degraded",
                checked_at=datetime.now(UTC),
                integration_checks={"email": email_check, "billing": billing_check},
                startup_checks={
                    name: STARTUP_CHECKS.get(name, StartupCheck(status="unverified")).model_copy()
                    for name in ("email", "billing", "oauth")
                },
                connections=[
                    AdminConnection(id="server", technology="fastapi", status="ok"),
                    AdminConnection(
                        id="database",
                        technology=database,
                        host=engine.url.host,
                        port=engine.url.port
                        or {"postgresql": 5432, "mysql": 3306, "mariadb": 3306}.get(dialect),
                        **checks["database"].model_dump(),
                    ),
                    AdminConnection(
                        id="cache",
                        technology="memory" if SETTINGS.REDIS_IN_MEMORY else "redis",
                        host=cache_host,
                        port=cache_port,
                        **checks["redis"].model_dump(),
                    ),
                    AdminConnection(
                        id="object_storage",
                        technology=SETTINGS.OBJECT_STORAGE_PROVIDER,
                        status=storage_check.status,
                        latency_ms=storage_check.latency_ms,
                        checked_at=storage_check.checked_at,
                        transport=transport,
                        port=storage_port,
                        probe="local_io"
                        if SETTINGS.OBJECT_STORAGE_PROVIDER == "local"
                        else "bucket_access",
                    ),
                ],
                environment_values=AdminEnvironmentValues(
                    APP_MODE=SETTINGS.APP_MODE,
                    EMAIL_ENABLED=SETTINGS.EMAIL_ENABLED,
                    LOGIN_ENABLED=SETTINGS.LOGIN_ENABLED,
                    OAUTH_ENABLED=SETTINGS.OAUTH_ENABLED,
                    STRIPE_ENABLED=SETTINGS.STRIPE_ENABLED,
                    REDIS_IN_MEMORY=SETTINGS.REDIS_IN_MEMORY,
                ),
                environment=AdminEnvironment(
                    app_mode=SETTINGS.APP_MODE,
                    email_enabled=SETTINGS.EMAIL_ENABLED,
                    login_enabled=SETTINGS.LOGIN_ENABLED,
                    oauth_enabled=SETTINGS.LOGIN_ENABLED and SETTINGS.OAUTH_ENABLED,
                    oauth_providers=SETTINGS.oauth_provider_list
                    if SETTINGS.LOGIN_ENABLED and SETTINGS.OAUTH_ENABLED
                    else [],
                    billing_configured=SETTINGS.STRIPE_ENABLED,
                    billing_enabled=billing.enabled,
                    billing_mode=("live" if billing.livemode else "test")
                    if billing.enabled
                    else "disabled",
                    developer_enabled=SETTINGS.APP_MODE == "development",
                    redis_in_memory=SETTINGS.REDIS_IN_MEMORY,
                ),
            )
        except Exception as exc:
            raise AdminException(AdminErrorCode.STATUS_FAILED) from exc
