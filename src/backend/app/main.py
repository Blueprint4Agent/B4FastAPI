import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.database import dispose_db, init_db
from app.core.error import AuthException
from app.core.logging import get_logger, mask_email
from app.core.mail import MAIL_SERVICE
from app.core.migrations import run_startup_schema_migrations
from app.core.redis import RedisManager
from app.core.settings import SETTINGS
from app.core.task_queue.services.mail import MAIL_QUEUE_SERVICE
from app.models.user import UserResponse, UserRole, Users
from app.routers.v1 import api_key, auth, events
from app.utils.token import create_access_token

logger = get_logger("app.main")
BOOTSTRAP_USER: UserResponse | None = None
BOOTSTRAP_ACCESS_TOKEN: str | None = None


class AppConfigResponse(BaseModel):
    api_base_path: str
    login_enabled: bool
    frontend_base_path: str
    email_enabled: bool
    oauth_enabled: bool
    oauth_providers: list[str]
    bootstrap_user: UserResponse | None = None
    bootstrap_access_token: str | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global BOOTSTRAP_USER, BOOTSTRAP_ACCESS_TOKEN
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

    await MAIL_SERVICE.initialize()
    await MAIL_QUEUE_SERVICE.start_worker()
    await run_startup_schema_migrations(SETTINGS.DATABASE_URL)
    logger.info("Database schema migration check complete (target=head).")
    await init_db()
    logger.info("Database initialization complete.")
    if not SETTINGS.LOGIN_ENABLED:
        bootstrap_email = SETTINGS.BOOTSTRAP_USER_EMAIL.strip().lower()
        bootstrap_name = SETTINGS.BOOTSTRAP_USER_NAME.strip()

        if bootstrap_email and bootstrap_name:
            bootstrap_user = await Users.get_user_response_by_email(bootstrap_email)
            if bootstrap_user is None:
                # Bootstrap user for login-disabled mode.
                try:
                    await Users.create_oauth_user(
                        email=bootstrap_email,
                        name=bootstrap_name,
                        provider="bootstrap",
                        identifier=bootstrap_email,
                        is_verified=True,
                        role=UserRole.ADMIN,
                    )
                except AuthException:
                    # Another startup worker may create it concurrently.
                    pass
                bootstrap_user = await Users.get_user_response_by_email(bootstrap_email)
                logger.info(
                    "Bootstrap user created (email=%s).",
                    mask_email(bootstrap_email),
                )
            else:
                logger.info(
                    "Bootstrap user found (email=%s).",
                    mask_email(bootstrap_email),
                )
            if bootstrap_user is not None and bootstrap_user.role != UserRole.ADMIN:
                bootstrap_user = await Users.update_user_role(
                    user_id=bootstrap_user.id,
                    role=UserRole.ADMIN,
                )
                logger.info(
                    "Bootstrap user role promoted to admin (email=%s).",
                    mask_email(bootstrap_email),
                )
            BOOTSTRAP_USER = bootstrap_user
            if bootstrap_user is not None:
                BOOTSTRAP_ACCESS_TOKEN = create_access_token(
                    subject=str(bootstrap_user.id),
                    email=bootstrap_user.email,
                )
                logger.info("Bootstrap access token issued (user_id=%s).", bootstrap_user.id)
            else:
                BOOTSTRAP_ACCESS_TOKEN = None
        else:
            BOOTSTRAP_USER = None
            BOOTSTRAP_ACCESS_TOKEN = None
            logger.warning(
                "Login is disabled but bootstrap user email/name is missing; bootstrap mode unavailable."
            )
    else:
        BOOTSTRAP_USER = None
        BOOTSTRAP_ACCESS_TOKEN = None
    logger.info("Application startup sequence complete.")
    try:
        yield
    finally:
        await MAIL_QUEUE_SERVICE.stop_worker()
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
    )

    @app.exception_handler(Exception)
    async def default_exception_handler(_request, _exc):
        if isinstance(_exc, HTTPException):
            logger.error(
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

    @app.get("/ping")
    async def ping():
        return {"status": "ok", "message": "pong"}

    @app.get("/config", response_model=AppConfigResponse)
    async def config():
        return {
            "api_base_path": "/api/v1",
            "login_enabled": SETTINGS.LOGIN_ENABLED,
            "frontend_base_path": "",
            "email_enabled": SETTINGS.EMAIL_ENABLED,
            "oauth_enabled": SETTINGS.OAUTH_ENABLED,
            "oauth_providers": SETTINGS.oauth_provider_list if SETTINGS.OAUTH_ENABLED else [],
            "bootstrap_user": None if SETTINGS.LOGIN_ENABLED else BOOTSTRAP_USER,
            "bootstrap_access_token": None if SETTINGS.LOGIN_ENABLED else BOOTSTRAP_ACCESS_TOKEN,
        }

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(api_key.router, prefix="/api/v1/api-keys", tags=["API Keys"])
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

    return app


app = create_app()
