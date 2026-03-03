from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urljoin

from fastapi import Request

from app.core.error import AuthErrorCode, AuthException
from app.core.mail import MAIL_SERVICE
from app.core.redis import RedisManager
from app.core.settings import SETTINGS
from app.models.user import (
    LoginForm,
    LoginResponse,
    RefreshResponse,
    SignupForm,
    UserDAOError,
    UserResponse,
    Users,
)
from app.utils.security import hash_password, verify_password
from app.utils.token import (
    consume_email_verification_token,
    consume_password_reset_token,
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    delete_refresh_token,
    store_email_verification_token,
    store_password_reset_token,
    store_refresh_token,
    verify_refresh_token,
)


class AuthService:
    async def signup(self, form: SignupForm) -> UserResponse:
        try:
            user = await Users.create_signup_user(
                email=form.email,
                name=form.name,
                password_hash=hash_password(form.password),
                is_verified=not SETTINGS.EMAIL_ENABLED,
            )
            if SETTINGS.EMAIL_ENABLED:
                await self._send_verification_email(user.id, user.email, user.name)
            return user
        except UserDAOError as error:
            if error.code == "EMAIL_ALREADY_EXISTS":
                raise AuthException(
                    code=AuthErrorCode.EMAIL_ALREADY_EXISTS,
                    message=error.message,
                ) from error
            raise AuthException(
                code=AuthErrorCode.SIGNUP_FAILED,
                message=error.message,
            ) from error

    async def login(self, form: LoginForm, request: Request) -> LoginResponse:
        user_ip = request.headers.get("X-Forwarded-For") or (
            request.client.host if request.client else "unknown"
        )
        await self._check_login_limit(user_ip)

        user = await Users.get_auth_user_by_email(form.email)

        if user is None or not user.password_hash:
            remaining_attempts = await self._register_login_failure(user_ip)
            raise AuthException(
                code=AuthErrorCode.INVALID_CREDENTIALS,
                details={"remaining_attempts": remaining_attempts},
            )

        if not verify_password(form.password, user.password_hash):
            remaining_attempts = await self._register_login_failure(user_ip)
            raise AuthException(
                code=AuthErrorCode.INVALID_CREDENTIALS,
                details={"remaining_attempts": remaining_attempts},
            )

        if SETTINGS.EMAIL_ENABLED and not user.is_verified:
            raise AuthException(code=AuthErrorCode.EMAIL_NOT_VERIFIED)

        await self._reset_login_fail_count(user_ip)
        await Users.update_login_metadata(
            user_id=user.id,
            login_ip=user_ip,
            user_agent=request.headers.get("user-agent"),
            login_time=datetime.now(UTC),
        )

        access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            expires_delta=timedelta(minutes=SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token()
        await store_refresh_token(user.id, refresh_token)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user.as_user_response(),
        )

    async def logout(self, user_id: int) -> None:
        await delete_refresh_token(user_id)

    async def refresh_access_token(self, user_id: int, refresh_token: str) -> RefreshResponse:
        is_valid = await verify_refresh_token(user_id, refresh_token)
        if not is_valid:
            raise AuthException(code=AuthErrorCode.INVALID_TOKEN)

        user = await Users.get_auth_user_by_id(user_id)
        if user is None:
            raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)

        access_token = create_access_token(subject=str(user.id), email=user.email)
        new_refresh_token = create_refresh_token()
        await store_refresh_token(user.id, new_refresh_token)

        return RefreshResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def verify_email(self, token: str) -> UserResponse:
        user_id = await consume_email_verification_token(token)
        if user_id is None:
            raise AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Invalid or expired email verification token.",
            )

        user = await Users.mark_email_verified(user_id)
        if user is None:
            raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
        return user

    async def resend_verification_email(self, email: str) -> None:
        if not SETTINGS.EMAIL_ENABLED:
            return
        user = await Users.get_auth_user_by_email(email)
        if user is None:
            return
        if user.is_verified:
            return
        await self._send_verification_email(user.id, user.email, user.name)

    async def request_password_reset(self, email: str) -> None:
        if not SETTINGS.EMAIL_ENABLED:
            raise AuthException(code=AuthErrorCode.EMAIL_DISABLED)

        user = await Users.get_auth_user_by_email(email)
        if user is None:
            return

        await self._send_password_reset_email(user.id, user.email, user.name)

    async def reset_password(self, token: str, password: str) -> None:
        if not SETTINGS.EMAIL_ENABLED:
            raise AuthException(code=AuthErrorCode.EMAIL_DISABLED)

        user_id = await consume_password_reset_token(token)
        if user_id is None:
            raise AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Invalid or expired password reset token.",
            )

        is_updated = await Users.update_password_hash(user_id, hash_password(password))
        if not is_updated:
            raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)

        await delete_refresh_token(user_id)

    async def _check_login_limit(self, user_ip: str) -> None:
        redis = await RedisManager.get_client()
        key = f"login_fail:{user_ip}"
        fails = await redis.get(key)

        if fails and int(fails) >= SETTINGS.LOGIN_FAILED_LIMIT:
            remaining_seconds = max(0, await redis.ttl(key))
            raise AuthException(
                code=AuthErrorCode.ACCOUNT_LOCKED,
                details={"remaining_seconds": remaining_seconds},
            )

    async def _register_login_failure(self, user_ip: str) -> int:
        redis = await RedisManager.get_client()
        key = f"login_fail:{user_ip}"
        count = await redis.incr(key)

        if count == 1:
            await redis.expire(key, timedelta(minutes=SETTINGS.LOGIN_LOCKED_MINUTES))

        remaining_attempts = max(0, SETTINGS.LOGIN_FAILED_LIMIT - count)

        if remaining_attempts <= 0:
            remaining_seconds = max(0, await redis.ttl(key))
            raise AuthException(
                code=AuthErrorCode.ACCOUNT_LOCKED,
                details={"remaining_seconds": remaining_seconds},
            )

        return remaining_attempts

    async def _reset_login_fail_count(self, user_ip: str) -> None:
        redis = await RedisManager.get_client()
        await redis.delete(f"login_fail:{user_ip}")

    async def _send_verification_email(self, user_id: int, email: str, name: str) -> None:
        verification_token = create_email_verification_token()
        await store_email_verification_token(user_id, verification_token)

        verify_path = "/verify-email"
        verify_query = urlencode({"token": verification_token})
        verify_link = urljoin(f"{SETTINGS.APP_BASE_URL.rstrip('/')}/", verify_path.lstrip("/"))
        verify_link = f"{verify_link}?{verify_query}"

        await MAIL_SERVICE.send_signup_verification_email(
            to_email=email,
            user_name=name,
            link=verify_link,
        )

    async def _send_password_reset_email(self, user_id: int, email: str, name: str) -> None:
        reset_token = create_password_reset_token()
        await store_password_reset_token(user_id, reset_token)

        reset_path = "/reset-password"
        reset_query = urlencode({"token": reset_token})
        reset_link = urljoin(f"{SETTINGS.APP_BASE_URL.rstrip('/')}/", reset_path.lstrip("/"))
        reset_link = f"{reset_link}?{reset_query}"

        await MAIL_SERVICE.send_password_reset_email(
            to_email=email,
            user_name=name,
            link=reset_link,
        )
