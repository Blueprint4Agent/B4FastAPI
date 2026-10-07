import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.cache.redis import RedisManager
from app.core.config.settings import SETTINGS
from app.core.db.migrations import run_startup_schema_migrations
from app.core.db.session import dispose_db, init_db
from app.core.error import ServiceException, service_exception_to_http
from app.core.mail.service import MAIL_SERVICE
from app.core.observability.error_logging import exception_log_level
from app.core.observability.health import HealthCheckResult, ReadinessResponse, get_readiness
from app.core.observability.integration_health import INTEGRATION_HEALTH
from app.core.observability.log_export import setup_log_export
from app.core.observability.logging import configure_request_context_logging, get_logger
from app.core.observability.metrics import setup_metrics
from app.core.observability.request_context import (
    add_request_context_headers,
    reset_request_context,
    resolve_request_id,
    resolve_trace_id,
    set_request_context,
)
from app.core.observability.startup_checks import STARTUP_CHECKS, record_startup_check
from app.core.observability.tracing import setup_tracing
from app.core.openapi import register_openapi_contracts
from app.models.user import UserResponse, Users
from app.routers.v1 import admin, api_key, auth, billing, billing_webhook, events
from app.services.billing import BillingService
from app.utils.token import create_access_token

logger = get_logger("app.main")
BOOTSTRAP_USER: UserResponse | None = None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        http_exc = service_exception_to_http(exc)
        logger.log(
            exception_log_level(http_exc.status_code, error_code=exc.code.error),
            "Service exception handled globally (method=%s, path=%s, status=%s, code=%s).",
            request.method,
            request.url.path,
            http_exc.status_code,
            exc.code.error,
        )
        return JSONResponse(status_code=http_exc.status_code, content={"detail": http_exc.detail})

    @app.exception_handler(Exception)
    async def default_exception_handler(_request, _exc):
        if isinstance(_exc, HTTPException):
            logger.log(
                exception_log_level(_exc.status_code),
                "HTTP exception handled globally (status=%s, detail=%s).",
                _exc.status_code,
                _exc.detail,
            )
            return JSONResponse(status_code=_exc.status_code, content={"detail": _exc.detail})
        logger.exception("Unhandled server exception.")
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
        )


class AppConfigResponse(BaseModel):
    api_base_path: str
    app_mode: Literal["development", "production"]
    login_enabled: bool
    frontend_base_path: str
    email_enabled: bool
    oauth_enabled: bool
    billing_enabled: bool
    oauth_providers: list[str]
    bootstrap_user: UserResponse | None = None
    bootstrap_access_token: str | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global BOOTSTRAP_USER
    await INTEGRATION_HEALTH.reset()
    STARTUP_CHECKS.clear()
    SETTINGS.validate_runtime_mode()
    if not SETTINGS.OAUTH_ENABLED:
        logger.info("OAuth integration is disabled.")
    else:
        logger.info(
            "OAuth integration enabled (providers=%s).",
            ",".join(SETTINGS.oauth_provider_list),
        )

    oauth_errors = SETTINGS.get_oauth_validation_errors()
    if oauth_errors:
        raise RuntimeError("Invalid OAuth configuration: " + " ".join(oauth_errors))
    if SETTINGS.OAUTH_ENABLED:
        logger.info("OAuth configuration validation succeeded.")

    record_startup_check("oauth", "configured" if SETTINGS.OAUTH_ENABLED else "disabled")
    await MAIL_SERVICE.initialize()
    record_startup_check(
        "email",
        "disabled"
        if not SETTINGS.EMAIL_ENABLED
        else "ok"
        if SETTINGS.SMTP_VALIDATE_ON_STARTUP
        else "configured",
    )
    await BillingService().initialize()
    record_startup_check("billing", "ok" if SETTINGS.STRIPE_ENABLED else "disabled")
    await run_startup_schema_migrations(SETTINGS.DATABASE_URL)
    logger.info("Database schema migration check complete (target=head).")
    await init_db()
    logger.info("Database initialization complete.")
    BOOTSTRAP_USER = None
    if not SETTINGS.LOGIN_ENABLED:
        from app.services.bootstrap import BootstrapService

        BOOTSTRAP_USER = await BootstrapService().initialize()
    logger.info("Application startup sequence complete.")
    try:
        yield
    finally:
        await INTEGRATION_HEALTH.reset()
        await dispose_db()
        await RedisManager.close()


def create_app() -> FastAPI:
    static_dist_dir = (Path(__file__).resolve().parent / "static" / "dist").resolve()
    log_level_name = SETTINGS.LOG_LEVEL.upper()
    log_level_value = logging.getLevelName(log_level_name)
    if not isinstance(log_level_value, int):
        log_level_name = "INFO"
        log_level_value = logging.INFO

    logging.getLogger("uvicorn.error").setLevel(log_level_value)
    logging.getLogger("uvicorn.access").setLevel(log_level_value)
    logging.getLogger("uvicorn").setLevel(log_level_value)
    configure_request_context_logging()
    setup_log_export()

    app = FastAPI(
        title=SETTINGS.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if SETTINGS.SWAGGER_ENABLED else None,
        redoc_url="/redoc" if SETTINGS.SWAGGER_ENABLED else None,
        openapi_url="/openapi.json" if SETTINGS.SWAGGER_ENABLED else None,
    )

    logger.info("App log level set to %s.", log_level_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=SETTINGS.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Trace-ID"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = resolve_request_id(request)
        trace_id = resolve_trace_id(request)
        tokens = set_request_context(request_id=request_id, trace_id=trace_id)
        try:
            response = await call_next(request)
            add_request_context_headers(
                response,
                request_id=request_id,
                trace_id=trace_id,
            )
            return response
        finally:
            reset_request_context(tokens)

    register_exception_handlers(app)

    @app.get("/ping")
    async def ping():
        return {"status": "ok", "message": "pong"}

    @app.get("/health/live", response_model=HealthCheckResult)
    async def health_live():
        return HealthCheckResult(status="ok")

    @app.get(
        "/health/ready",
        response_model=ReadinessResponse,
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "model": ReadinessResponse,
                "description": "One or more required dependencies are unavailable",
            },
        },
    )
    async def health_ready():
        readiness = await get_readiness()
        if readiness.status != "ok":
            return JSONResponse(status_code=503, content=readiness.model_dump())
        return readiness

    @app.get("/config", response_model=AppConfigResponse)
    async def config(response: Response):
        response.headers["Cache-Control"] = "no-store"
        bootstrap_user = (
            await Users.get_user_response_by_id(BOOTSTRAP_USER.id)
            if not SETTINGS.LOGIN_ENABLED and BOOTSTRAP_USER
            else None
        )
        bootstrap_token = (
            create_access_token(subject=str(bootstrap_user.id), email=bootstrap_user.email)
            if bootstrap_user
            else None
        )
        return {
            "api_base_path": "/api/v1",
            "app_mode": SETTINGS.APP_MODE,
            "login_enabled": SETTINGS.LOGIN_ENABLED,
            "frontend_base_path": "",
            "email_enabled": SETTINGS.EMAIL_ENABLED,
            "oauth_enabled": SETTINGS.LOGIN_ENABLED and SETTINGS.OAUTH_ENABLED,
            "billing_enabled": SETTINGS.STRIPE_ENABLED,
            "oauth_providers": SETTINGS.oauth_provider_list
            if SETTINGS.LOGIN_ENABLED and SETTINGS.OAUTH_ENABLED
            else [],
            "bootstrap_user": bootstrap_user,
            "bootstrap_access_token": bootstrap_token,
        }

    setup_metrics(app)
    setup_tracing(app)

    app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(api_key.router, prefix="/api/v1/api-keys", tags=["API Keys"])
    app.include_router(billing_webhook.router, prefix="/api/v1/billing", tags=["Billing"])
    app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
    app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])

    if static_dist_dir.exists():
        app.mount("/", StaticFiles(directory=static_dist_dir, html=True), name="frontend")

        @app.exception_handler(404)
        async def spa_fallback(request: Request, exc):
            accepts_html = "text/html" in request.headers.get("accept", "")
            is_api_path = request.url.path.startswith("/api/")
            if request.method in {"GET", "HEAD"} and accepts_html and not is_api_path:
                index_path = static_dist_dir / "index.html"
                if index_path.exists():
                    return FileResponse(index_path)

            # Preserve API error payload shape for domain 404 responses.
            if is_api_path:
                detail = getattr(exc, "detail", "Not Found")
                return JSONResponse(status_code=404, content={"detail": detail})

            return JSONResponse(status_code=404, content={"detail": "Not Found"})

    register_openapi_contracts(app)
    return app


app = create_app()
