from datetime import UTC, datetime, timedelta

from fastapi import Request

from app.core.error import AuthErrorCode, AuthException
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
    create_access_token,
    create_refresh_token,
    delete_refresh_token,
    store_refresh_token,
    verify_refresh_token,
)


class AuthService:
    async def signup(self, form: SignupForm) -> UserResponse:
        try:
            return await Users.create_signup_user(
                email=form.email,
                name=form.name,
                password_hash=hash_password(form.password),
            )
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
