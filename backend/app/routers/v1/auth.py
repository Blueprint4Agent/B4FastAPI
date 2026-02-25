from fastapi import APIRouter, Body, Depends, Request, Response

from app.core.error import AuthErrorCode, AuthException, service_exception_to_http
from app.deps import get_current_user
from app.models.user import LoginForm, LoginResponse, RefreshResponse, SignupForm, UserResponse
from app.services.auth import AuthService
from app.utils.cookies import clear_refresh_cookies, get_refresh_cookie_value, set_refresh_cookies

router = APIRouter()


def _raise_http_error(error: AuthException):
    raise service_exception_to_http(error)


@router.post("/signup", response_model=UserResponse)
async def signup(form: SignupForm, service: AuthService = Depends(AuthService)):
    try:
        return await service.signup(form)
    except AuthException as error:
        _raise_http_error(error)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    form: LoginForm,
    service: AuthService = Depends(AuthService),
):
    try:
        token_payload = await service.login(form, request)
    except AuthException as error:
        _raise_http_error(error)

    set_refresh_cookies(
        response=response,
        request=request,
        refresh_token=token_payload.refresh_token,
        user_id=token_payload.user.id,
        remember_me=form.remember_me,
    )
    return token_payload


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
    service: AuthService = Depends(AuthService),
):
    await service.logout(current_user.id)
    clear_refresh_cookies(response)
    return {"message": "Successfully logged out."}


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Request,
    response: Response,
    refresh_token: str | None = Body(default=None, embed=True),
    user_id: int | None = Body(default=None, embed=True),
    service: AuthService = Depends(AuthService),
):
    cookie_token, cookie_user_id = get_refresh_cookie_value(request)
    refresh_token_value = refresh_token or cookie_token
    user_id_value = user_id or cookie_user_id

    if not refresh_token_value or not user_id_value:
        clear_refresh_cookies(response)
        _raise_http_error(
            AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Refresh token and user_id are required.",
            )
        )

    try:
        token_payload = await service.refresh_access_token(
            user_id=int(user_id_value),
            refresh_token=refresh_token_value,
        )
    except (AuthException, ValueError) as error:
        clear_refresh_cookies(response)
        if isinstance(error, AuthException):
            _raise_http_error(error)
        _raise_http_error(
            AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Invalid refresh token payload.",
            )
        )

    set_refresh_cookies(
        response=response,
        request=request,
        refresh_token=token_payload.refresh_token,
        user_id=int(user_id_value),
    )
    return token_payload
