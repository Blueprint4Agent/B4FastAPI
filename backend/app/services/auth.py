import asyncio
import json
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request as URLRequest, urlopen

from fastapi import Request
from sqlalchemy.exc import IntegrityError

from app.core.error import AuthErrorCode, AuthException
from app.core.mail import MAIL_SERVICE
from app.core.redis import RedisManager
from app.core.settings import SETTINGS
from app.models.oauth import (
    OAuthIdentityProfile,
    OAuthProvider,
    OAuthProviderConfig,
    OAuthProviderPublicConfig,
)
from app.models.user import (
    LoginForm,
    LoginResponse,
    RefreshResponse,
    SignupForm,
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
    def get_oauth_provider_configs(self) -> list[OAuthProviderConfig]:
        if not SETTINGS.OAUTH_ENABLED:
            return []

        validation_errors = SETTINGS.get_oauth_validation_errors()
        if validation_errors:
            raise AuthException(
                code=AuthErrorCode.OAUTH_PROVIDER_CONFIG_INVALID,
                details={"errors": validation_errors},
            )

        provider_configs = SETTINGS.get_oauth_provider_configs()
        return [
            OAuthProviderConfig(
                provider=OAuthProvider(provider),
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                authorize_url=config["authorize_url"],
                token_url=config["token_url"],
                userinfo_url=config["userinfo_url"],
            )
            for provider, config in provider_configs.items()
        ]

    def get_oauth_provider_public_configs(self) -> list[OAuthProviderPublicConfig]:
        return [
            OAuthProviderPublicConfig(
                provider=config.provider,
                start_path=f"/api/v1/auth/oauth/{config.provider}/start",
            )
            for config in self.get_oauth_provider_configs()
        ]

    async def create_oauth_state(self, provider: OAuthProvider) -> str:
        state = create_refresh_token()
        redis = await RedisManager.get_client()
        await redis.setex(
            f"oauth_state:{state}",
            timedelta(minutes=SETTINGS.OAUTH_STATE_EXPIRE_MINUTES),
            provider.value,
        )
        return state

    async def consume_oauth_state(self, state: str) -> OAuthProvider | None:
        redis = await RedisManager.get_client()
        key = f"oauth_state:{state}"
        provider_value = await redis.get(key)
        if provider_value is None:
            return None
        await redis.delete(key)
        try:
            return OAuthProvider(provider_value)
        except ValueError:
            return None

    async def build_oauth_authorization_url(
        self,
        provider: OAuthProvider,
        redirect_uri: str,
    ) -> str:
        provider_config = self._get_oauth_provider_config(provider)
        state = await self.create_oauth_state(provider)

        if provider == OAuthProvider.GOOGLE:
            query = {
                "response_type": "code",
                "client_id": provider_config.client_id,
                "redirect_uri": redirect_uri,
                "scope": "openid email profile",
                "state": state,
                "access_type": "online",
                "prompt": "select_account",
            }
        else:
            query = {
                "client_id": provider_config.client_id,
                "redirect_uri": redirect_uri,
                "scope": "read:user user:email",
                "state": state,
            }

        return f"{provider_config.authorize_url}?{urlencode(query)}"

    async def oauth_callback_login(
        self,
        provider: OAuthProvider,
        code: str,
        state: str,
        redirect_uri: str,
        request: Request,
        refresh_session_id: str,
    ) -> LoginResponse:
        consumed_provider = await self.consume_oauth_state(state)
        if consumed_provider is None or consumed_provider != provider:
            raise AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Invalid OAuth state.",
            )

        provider_config = self._get_oauth_provider_config(provider)
        access_token = await self._exchange_oauth_code(
            provider=provider,
            provider_config=provider_config,
            code=code,
            redirect_uri=redirect_uri,
        )
        profile = await self._fetch_oauth_profile(provider, provider_config, access_token)

        user = await self._resolve_oauth_user(profile)
        user_ip = self._get_client_ip(request)
        await Users.update_login_metadata(
            user_id=user.id,
            provider=provider.value,
            identifier=profile.provider_user_id,
            login_ip=user_ip,
            user_agent=request.headers.get("user-agent"),
            login_time=datetime.now(UTC),
        )

        issued_access_token, refresh_token = await self._issue_session_tokens(
            user_id=user.id,
            user_email=user.email,
            refresh_session_id=refresh_session_id,
            remember_me=True,
        )
        return LoginResponse(
            access_token=issued_access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user.as_user_response(),
        )

    async def signup(self, form: SignupForm) -> UserResponse:
        try:
            user = await Users.create_signup_user(
                email=form.email,
                name=form.name,
                password_hash=hash_password(form.password),
                is_verified=not SETTINGS.EMAIL_ENABLED,
            )
        except IntegrityError as error:
            raise AuthException(code=AuthErrorCode.SIGNUP_FAILED) from error

        if SETTINGS.EMAIL_ENABLED:
            await self._send_verification_email(user.id, user.email, user.name)
        return user

    async def login(
        self, form: LoginForm, request: Request, refresh_session_id: str
    ) -> LoginResponse:
        user_ip = self._get_client_ip(request)
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
            provider="email",
            identifier=user.email,
            login_ip=user_ip,
            user_agent=request.headers.get("user-agent"),
            login_time=datetime.now(UTC),
        )

        access_token, refresh_token = await self._issue_session_tokens(
            user_id=user.id,
            user_email=user.email,
            refresh_session_id=refresh_session_id,
            remember_me=form.remember_me,
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user.as_user_response(),
        )

    async def logout(self, user_id: int) -> None:
        await delete_refresh_token(user_id)

    async def refresh_access_token(
        self,
        user_id: int,
        refresh_session_id: str,
        refresh_token: str,
        remember_me: bool = False,
    ) -> RefreshResponse:
        is_valid = await verify_refresh_token(user_id, refresh_session_id, refresh_token)
        if not is_valid:
            raise AuthException(code=AuthErrorCode.INVALID_TOKEN)

        user = await Users.get_auth_user_by_id(user_id)
        if user is None:
            raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)

        access_token = create_access_token(
            subject=str(user.id),
            email=user.email,
            expires_delta=timedelta(minutes=SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        await store_refresh_token(
            user.id,
            refresh_session_id,
            refresh_token,
            remember_me=remember_me,
        )

        return RefreshResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def _issue_session_tokens(
        self,
        user_id: int,
        user_email: str,
        refresh_session_id: str,
        remember_me: bool = False,
    ) -> tuple[str, str]:
        access_token = create_access_token(
            subject=str(user_id),
            email=user_email,
            expires_delta=timedelta(minutes=SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        refresh_token = create_refresh_token()
        await store_refresh_token(
            user_id,
            refresh_session_id,
            refresh_token,
            remember_me=remember_me,
        )
        return access_token, refresh_token

    def _get_oauth_provider_config(self, provider: OAuthProvider) -> OAuthProviderConfig:
        provider_configs = {config.provider: config for config in self.get_oauth_provider_configs()}
        if provider not in provider_configs:
            raise AuthException(
                code=AuthErrorCode.OAUTH_PROVIDER_NOT_ENABLED,
                details={"provider": provider.value},
            )
        return provider_configs[provider]

    async def _exchange_oauth_code(
        self,
        provider: OAuthProvider,
        provider_config: OAuthProviderConfig,
        code: str,
        redirect_uri: str,
    ) -> str:
        data = {
            "code": code,
            "client_id": provider_config.client_id,
            "client_secret": provider_config.client_secret,
            "redirect_uri": redirect_uri,
        }
        if provider == OAuthProvider.GOOGLE:
            data["grant_type"] = "authorization_code"

        body = urlencode(data).encode("utf-8")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        payload = await self._http_request_json(
            method="POST",
            url=provider_config.token_url,
            headers=headers,
            body=body,
        )
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="OAuth token exchange failed.",
            )
        return token

    async def _fetch_oauth_profile(
        self,
        provider: OAuthProvider,
        provider_config: OAuthProviderConfig,
        access_token: str,
    ) -> OAuthIdentityProfile:
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        payload = await self._http_request_json(
            method="GET",
            url=provider_config.userinfo_url,
            headers=headers,
        )

        if provider == OAuthProvider.GOOGLE:
            provider_user_id = str(payload.get("sub", "")).strip()
            email = str(payload.get("email", "")).strip().lower()
            name = str(payload.get("name", "")).strip() or email
            email_verified = bool(payload.get("email_verified", False))
        else:
            provider_user_id = str(payload.get("id", "")).strip()
            email = str(payload.get("email", "")).strip().lower()
            name = str(payload.get("name", "")).strip() or str(payload.get("login", "")).strip()
            verified_email, email_verified = await self._fetch_github_primary_email(
                provider_config,
                access_token,
            )
            if verified_email:
                email = verified_email

        if not provider_user_id or not email:
            raise AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="OAuth profile payload is incomplete.",
            )

        return OAuthIdentityProfile(
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            name=name or email,
            email_verified=email_verified,
        )

    async def _fetch_github_primary_email(
        self,
        provider_config: OAuthProviderConfig,
        access_token: str,
    ) -> tuple[str, bool]:
        emails_url = provider_config.userinfo_url.rstrip("/") + "/emails"
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        payload = await self._http_request_json(method="GET", url=emails_url, headers=headers)
        if not isinstance(payload, list):
            return "", False
        for item in payload:
            if not isinstance(item, Mapping):
                continue
            if item.get("primary") and item.get("verified") and item.get("email"):
                return str(item["email"]).strip().lower(), True
        for item in payload:
            if isinstance(item, Mapping) and item.get("verified") and item.get("email"):
                return str(item["email"]).strip().lower(), True
        return "", False

    async def _resolve_oauth_user(self, profile: OAuthIdentityProfile):
        if not profile.email_verified:
            raise AuthException(
                code=AuthErrorCode.INVALID_TOKEN,
                message="OAuth email is not verified.",
            )

        auth_user = await Users.get_auth_user_by_identity(
            provider=profile.provider.value,
            identifier=profile.provider_user_id,
        )
        if auth_user is not None:
            return auth_user

        existing_user = await Users.get_user_response_by_email(profile.email)
        if existing_user is not None:
            linked = await Users.link_auth_identity(
                user_id=existing_user.id,
                provider=profile.provider.value,
                identifier=profile.provider_user_id,
            )
            if not linked:
                raise AuthException(
                    code=AuthErrorCode.OAUTH_IDENTITY_CONFLICT,
                )
            linked_user = await Users.get_auth_user_by_id(existing_user.id)
            if linked_user is None:
                raise AuthException(code=AuthErrorCode.USER_NOT_FOUND)
            return linked_user

        try:
            await Users.create_oauth_user(
                email=profile.email,
                name=profile.name,
                provider=profile.provider.value,
                identifier=profile.provider_user_id,
                is_verified=profile.email_verified,
            )
        except IntegrityError as error:
            raise AuthException(
                code=AuthErrorCode.OAUTH_SIGNUP_FAILED,
            ) from error

        created_user = await Users.get_auth_user_by_identity(
            provider=profile.provider.value,
            identifier=profile.provider_user_id,
        )
        if created_user is None:
            raise AuthException(code=AuthErrorCode.OAUTH_SIGNUP_FAILED)
        return created_user

    async def _http_request_json(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
    ):
        def _do_request():
            request = URLRequest(url=url, data=body, method=method)
            for key, value in (headers or {}).items():
                request.add_header(key, value)
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8")

        try:
            raw = await asyncio.to_thread(_do_request)
            payload = json.loads(raw)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
            raise AuthException(
                code=AuthErrorCode.OAUTH_PROVIDER_REQUEST_FAILED,
                message="OAuth provider request failed.",
            ) from error

        return payload

    def _get_client_ip(self, request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        if not SETTINGS.TRUST_PROXY_HEADERS:
            return client_ip

        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            forwarded_ip = x_forwarded_for.split(",")[0].strip()
            if forwarded_ip:
                return forwarded_ip

        x_real_ip = request.headers.get("X-Real-IP")
        if x_real_ip:
            real_ip = x_real_ip.strip()
            if real_ip:
                return real_ip

        return client_ip

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

    async def update_profile_name(self, user_id: int, name: str) -> UserResponse:
        user = await Users.update_user_name(user_id=user_id, name=name)
        if user is None:
            raise AuthException(code=AuthErrorCode.PROFILE_UPDATE_FAILED)
        return user

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
