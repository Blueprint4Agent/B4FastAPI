from datetime import timedelta

from fastapi import Request, Response

from app.core.settings import SETTINGS

REFRESH_COOKIE_NAME = "template_refresh_token"
REFRESH_SID_COOKIE_NAME = "template_refresh_sid"


def _is_https_request(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto:
        first_proto = forwarded_proto.split(",")[0].strip().lower()
        if first_proto == "https":
            return True
    return request.url.scheme == "https"


def get_refresh_cookie_value(request: Request) -> tuple[str | None, str | None]:
    return (
        request.cookies.get(REFRESH_COOKIE_NAME),
        request.cookies.get(REFRESH_SID_COOKIE_NAME),
    )


def set_refresh_cookies(
    response: Response,
    request: Request,
    refresh_token: str,
    refresh_session_id: str,
    remember_me: bool = True,
) -> None:
    secure = _is_https_request(request)
    cookie_params = {
        "httponly": True,
        "secure": secure,
        "samesite": "none" if secure else "lax",
        "path": "/",
    }

    if remember_me:
        ttl_seconds = int(timedelta(days=SETTINGS.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
        cookie_params["max_age"] = ttl_seconds
        cookie_params["expires"] = ttl_seconds

    response.set_cookie(REFRESH_COOKIE_NAME, refresh_token, **cookie_params)
    response.set_cookie(REFRESH_SID_COOKIE_NAME, refresh_session_id, **cookie_params)


def clear_refresh_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
    response.delete_cookie(REFRESH_SID_COOKIE_NAME, path="/")
