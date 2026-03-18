from urllib.parse import urlencode, urljoin

from fastapi import APIRouter, Body, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse

from app.core.error import AuthErrorCode, AuthException, service_exception_to_http
from app.core.settings import SETTINGS
from app.deps import get_current_user
from app.models.oauth import OAuthProvider, OAuthProvidersResponse
from app.models.user import (
    ForgotPasswordForm,
    ForgotPasswordResponse,
    LoginForm,
    LoginResponse,
    RefreshResponse,
    ResendVerificationForm,
    ResendVerificationResponse,
    ResetPasswordForm,
    ResetPasswordResponse,
    SignupForm,
    UserResponse,
    VerifyEmailForm,
    VerifyEmailResponse,
)
from app.services.auth import AuthService
from app.utils.cookies import clear_refresh_cookies, get_refresh_cookie_value, set_refresh_cookies
from app.utils.token import create_refresh_session_id, get_refresh_session

router = APIRouter()


def _raise_http_error(error: AuthException):
    raise service_exception_to_http(error)


@router.post("/signup", response_model=UserResponse)
async def signup(form: SignupForm, service: AuthService = Depends(AuthService)):
    try:
        return await service.signup(form)
    except AuthException as error:
        _raise_http_error(error)


@router.get("/oauth/providers", response_model=OAuthProvidersResponse)
async def oauth_providers(service: AuthService = Depends(AuthService)):
    try:
        providers = service.get_oauth_provider_public_configs()
        return OAuthProvidersResponse(providers=providers)
    except AuthException as error:
        _raise_http_error(error)


@router.get("/oauth/{provider}/start")
async def oauth_start(
    provider: OAuthProvider,
    request: Request,
    service: AuthService = Depends(AuthService),
):
    try:
        redirect_uri = str(request.url_for("oauth_callback", provider=provider.value))
        authorization_url = await service.build_oauth_authorization_url(provider, redirect_uri)
        return RedirectResponse(url=authorization_url, status_code=307)
    except AuthException as error:
        _raise_http_error(error)


@router.get("/oauth/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: OAuthProvider,
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    service: AuthService = Depends(AuthService),
):
    if error:
        failure_query = urlencode({"error": error})
        failure_url = urljoin(
            f"{SETTINGS.APP_BASE_URL.rstrip('/')}/",
            SETTINGS.OAUTH_FRONTEND_FAILURE_PATH.lstrip("/"),
        )
        return RedirectResponse(url=f"{failure_url}?{failure_query}", status_code=307)

    if not code or not state:
        _raise_http_error(
            AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="OAuth callback requires code and state.",
            )
        )

    refresh_session_id = create_refresh_session_id()
    try:
        token_payload = await service.oauth_callback_login(
            provider=provider,
            code=code,
            state=state,
            redirect_uri=str(request.url_for("oauth_callback", provider=provider.value)),
            request=request,
            refresh_session_id=refresh_session_id,
        )
    except AuthException as auth_error:
        failure_query = urlencode(
            {
                "error": auth_error.code.error,
                "message": auth_error.message,
            }
        )
        failure_url = urljoin(
            f"{SETTINGS.APP_BASE_URL.rstrip('/')}/",
            SETTINGS.OAUTH_FRONTEND_FAILURE_PATH.lstrip("/"),
        )
        return RedirectResponse(url=f"{failure_url}?{failure_query}", status_code=307)

    success_url = urljoin(
        f"{SETTINGS.APP_BASE_URL.rstrip('/')}/",
        SETTINGS.OAUTH_FRONTEND_SUCCESS_PATH.lstrip("/"),
    )
    response = RedirectResponse(url=success_url, status_code=307)
    set_refresh_cookies(
        response=response,
        request=request,
        refresh_token=token_payload.refresh_token,
        refresh_session_id=refresh_session_id,
        remember_me=True,
    )
    return response


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    form: LoginForm,
    service: AuthService = Depends(AuthService),
):
    refresh_session_id = create_refresh_session_id()
    try:
        token_payload = await service.login(form, request, refresh_session_id=refresh_session_id)
    except AuthException as error:
        _raise_http_error(error)

    set_refresh_cookies(
        response=response,
        request=request,
        refresh_token=token_payload.refresh_token,
        refresh_session_id=refresh_session_id,
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
    session_id: str | None = Body(default=None, embed=True),
    service: AuthService = Depends(AuthService),
):
    cookie_token, cookie_session_id = get_refresh_cookie_value(request)
    refresh_token_value = refresh_token or cookie_token
    session_id_value = session_id or cookie_session_id
    user_id_value = user_id
    remember_me = False

    if session_id_value:
        session = await get_refresh_session(session_id_value)
        if session is not None:
            session_user_id, session_remember_me = session
            remember_me = session_remember_me
            if user_id_value is None:
                user_id_value = session_user_id

    if not refresh_token_value or not session_id_value or not user_id_value:
        clear_refresh_cookies(response)
        _raise_http_error(
            AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Refresh token and session_id are required.",
            )
        )

    try:
        token_payload = await service.refresh_access_token(
            user_id=int(user_id_value),
            refresh_session_id=session_id_value,
            refresh_token=refresh_token_value,
            remember_me=remember_me,
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
        refresh_session_id=session_id_value,
        remember_me=remember_me,
    )
    return token_payload


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    form: VerifyEmailForm,
    service: AuthService = Depends(AuthService),
):
    try:
        user = await service.verify_email(form.token)
        return VerifyEmailResponse(message="Email verified successfully.", user=user)
    except AuthException as error:
        _raise_http_error(error)


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification_email(
    form: ResendVerificationForm,
    service: AuthService = Depends(AuthService),
):
    try:
        await service.resend_verification_email(form.email)
        return ResendVerificationResponse(
            message="If an unverified account exists, a verification email has been sent.",
        )
    except AuthException as error:
        _raise_http_error(error)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    form: ForgotPasswordForm,
    service: AuthService = Depends(AuthService),
):
    try:
        await service.request_password_reset(form.email)
        return ForgotPasswordResponse(
            message="If the account exists, a password reset email has been sent.",
        )
    except AuthException as error:
        _raise_http_error(error)


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    form: ResetPasswordForm,
    service: AuthService = Depends(AuthService),
):
    try:
        await service.reset_password(form.token, form.password)
        return ResetPasswordResponse(message="Password reset completed successfully.")
    except AuthException as error:
        _raise_http_error(error)
