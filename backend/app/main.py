import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.core.database import dispose_db, init_db
from app.core.mail import MAIL_SERVICE
from app.core.redis import RedisManager
from app.core.settings import SETTINGS
from app.routers.v1 import auth

logger = logging.getLogger("uvicorn.error")


class AppConfigResponse(BaseModel):
    api_base_path: str
    login_enabled: bool
    frontend_base_path: str
    email_enabled: bool
    oauth_enabled: bool
    oauth_providers: list[str]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if not SETTINGS.OAUTH_ENABLED:
        logger.info("OAuth integration is disabled.")
    else:
        logger.info(
            "OAuth integration enabled (providers=%s).",
            ",".join(SETTINGS.oauth_provider_list),
        )

    oauth_errors = SETTINGS.get_oauth_validation_errors()
    if oauth_errors:
        raise RuntimeError(
            "Invalid OAuth configuration: " + " ".join(oauth_errors)
        )
    if SETTINGS.OAUTH_ENABLED:
        logger.info("OAuth configuration validation succeeded.")

    await MAIL_SERVICE.initialize()
    await init_db()
    try:
        yield
    finally:
        await dispose_db()
        await RedisManager.close()


def create_app() -> FastAPI:
    static_dist_dir = (Path(__file__).resolve().parent / "static" / "dist").resolve()

    app = FastAPI(
        title=SETTINGS.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if SETTINGS.SWAGGER_ENABLED else None,
        redoc_url="/redoc" if SETTINGS.SWAGGER_ENABLED else None,
        openapi_url="/openapi.json" if SETTINGS.SWAGGER_ENABLED else None,
    )

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
            return JSONResponse(status_code=_exc.status_code, content={"detail": _exc.detail})
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
            "login_enabled": True,
            "frontend_base_path": "",
            "email_enabled": SETTINGS.EMAIL_ENABLED,
            "oauth_enabled": SETTINGS.OAUTH_ENABLED,
            "oauth_providers": SETTINGS.oauth_provider_list if SETTINGS.OAUTH_ENABLED else [],
        }

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

    if static_dist_dir.exists():
        app.mount("/", StaticFiles(directory=static_dist_dir, html=True), name="frontend")

        @app.exception_handler(404)
        async def spa_fallback(request: Request, _exc):
            accepts_html = "text/html" in request.headers.get("accept", "")
            is_api_path = request.url.path.startswith("/api/")
            if request.method in {"GET", "HEAD"} and accepts_html and not is_api_path:
                index_path = static_dist_dir / "index.html"
                if index_path.exists():
                    return FileResponse(index_path)
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

    return app


app = create_app()
