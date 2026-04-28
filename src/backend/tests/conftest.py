from datetime import UTC, datetime

import pytest

from app.models.user import UserResponse


@pytest.fixture
def sample_user() -> UserResponse:
    return UserResponse(
        id=1,
        email="tester@example.com",
        name="Tester",
        profile_image_url=None,
        oauth_providers=[],
        is_verified=True,
        created_at=datetime.now(UTC),
    )
