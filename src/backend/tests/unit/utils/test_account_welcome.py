import asyncio
from unittest.mock import AsyncMock

from app.models.oauth import OAuthIdentityProfile, OAuthProvider
from app.services.auth import AuthService


def test_oauth_greeting_is_only_queued_for_new_identity(monkeypatch, sample_user):
    """Scenario: first OAuth creation greets the user but repeated login does not."""
    # Given: a new provider identity with verified email.
    profile = OAuthIdentityProfile(
        provider=OAuthProvider.GOOGLE,
        provider_user_id="example-id",
        email=sample_user.email,
        name=sample_user.name,
        email_verified=True,
    )
    lookup = AsyncMock(side_effect=[None, sample_user, sample_user])
    monkeypatch.setattr("app.services.auth.Users.get_auth_user_by_identity", lookup)
    monkeypatch.setattr(
        "app.services.auth.Users.get_user_response_by_email", AsyncMock(return_value=None)
    )
    create = AsyncMock(return_value=sample_user)
    monkeypatch.setattr("app.services.auth.Users.create_oauth_user", create)
    enqueue = AsyncMock()
    monkeypatch.setattr("app.services.auth.MAIL_QUEUE_SERVICE.enqueue_welcome", enqueue)
    service = AuthService()
    # When: the provider identity is resolved twice.
    asyncio.run(service._resolve_oauth_user(profile, "ko"))
    asyncio.run(service._resolve_oauth_user(profile, "ko"))
    # Then: only account creation publishes a greeting.
    create.assert_awaited_once()
    enqueue.assert_awaited_once_with(
        to_email=sample_user.email, user_name=sample_user.name, language="ko"
    )
