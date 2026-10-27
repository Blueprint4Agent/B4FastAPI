"""Development-only identity provisioning; never promote an existing normal account."""

from app.core.config.settings import SETTINGS
from app.core.error import AuthException
from app.models.user import UserResponse, UserRole, Users
from app.utils.token import create_access_token


class BootstrapService:
    async def client_config(self, bootstrap_user_id: int | None) -> dict[str, object]:
        """Return client settings with a fresh snapshot/token for the bootstrap user."""
        bootstrap_user = (
            await Users.get_user_response_by_id(bootstrap_user_id)
            if not SETTINGS.LOGIN_ENABLED and bootstrap_user_id is not None
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
            "app_layout": SETTINGS.APP_LAYOUT,
            "demo_enabled": SETTINGS.DEMO_ENABLED,
            "login_enabled": SETTINGS.LOGIN_ENABLED,
            "frontend_base_path": SETTINGS.APP_BASE_PATH,
            "email_enabled": SETTINGS.EMAIL_ENABLED,
            "oauth_enabled": SETTINGS.LOGIN_ENABLED and SETTINGS.OAUTH_ENABLED,
            "billing_enabled": SETTINGS.STRIPE_ENABLED,
            "oauth_providers": SETTINGS.oauth_provider_list
            if SETTINGS.LOGIN_ENABLED and SETTINGS.OAUTH_ENABLED
            else [],
            "bootstrap_user": bootstrap_user,
            "bootstrap_access_token": bootstrap_token,
        }

    async def initialize(self) -> UserResponse:
        if SETTINGS.APP_MODE != "development" or SETTINGS.LOGIN_ENABLED:
            raise ValueError("Bootstrap requires development mode with login disabled.")
        email = SETTINGS.BOOTSTRAP_USER_EMAIL.strip().lower()
        name = SETTINGS.BOOTSTRAP_USER_NAME.strip()
        if not email or not name:
            raise ValueError("Bootstrap email and name are required.")
        user = await Users.get_user_response_by_email(email)
        if user is None:
            try:
                await Users.create_oauth_user(
                    email=email,
                    name=name,
                    provider="bootstrap",
                    identifier=email,
                    is_verified=True,
                    role=UserRole.ADMIN,
                )
            except AuthException:
                # Another process may have provisioned the identity. Validate it below.
                pass
            user = await Users.get_user_response_by_email(email)
        identity = await Users.get_auth_user_by_identity("bootstrap", email)
        if (
            user is None
            or identity is None
            or identity.id != user.id
            or identity.password_hash is not None
            or identity.role != UserRole.ADMIN
        ):
            raise ValueError(
                "Bootstrap identity conflict: use a dedicated active development admin account."
            )
        return user
