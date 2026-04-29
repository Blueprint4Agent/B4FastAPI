import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.core.database as database
from app.core.redis import RedisManager
from app.core.settings import SETTINGS
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


@pytest.fixture
def integration_client(tmp_path: Path):
    original_database_url = SETTINGS.DATABASE_URL
    test_db_url = f"sqlite+aiosqlite:///{(tmp_path / 'integration.db').as_posix()}"
    object.__setattr__(SETTINGS, "DATABASE_URL", test_db_url)

    database._ENGINE = None
    database._SESSION_FACTORY = None
    asyncio.run(RedisManager.close())

    from app.main import create_app

    app = create_app()
    try:
        with TestClient(app) as client:
            yield client
    finally:
        asyncio.run(RedisManager.close())
        object.__setattr__(SETTINGS, "DATABASE_URL", original_database_url)
        database._ENGINE = None
        database._SESSION_FACTORY = None
