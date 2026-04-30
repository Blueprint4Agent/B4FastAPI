import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.core.database as database
from app.core.redis import RedisManager
from app.core.settings import SETTINGS
from app.models.user import AuthIdentity, Credential, User, UserResponse
from app.utils.security import hash_password
from tests.fixtures.scenario_seed_data import (
    DEFAULT_SEED_PROFILE,
    SeedProfileSchema,
)


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


async def _seed_default_users(
    *,
    seed_profile: SeedProfileSchema = DEFAULT_SEED_PROFILE,
) -> None:
    session_factory = database.get_session_factory()
    shared_password_hash = hash_password(seed_profile.primary_user.password)

    async with session_factory() as session:
        seed_users: list[User] = []

        primary_user = User(
            email=seed_profile.primary_user.email,
            name=seed_profile.primary_user.name,
            is_verified=seed_profile.primary_user.is_verified,
        )
        primary_user.credential = Credential(password_hash=shared_password_hash)
        primary_user.auth_identities = [
            AuthIdentity(provider="email", identifier=seed_profile.primary_user.email)
        ]
        seed_users.append(primary_user)

        start_index = seed_profile.existing_user_start_index
        end_index = start_index + seed_profile.existing_user_count
        for index in range(start_index, end_index):
            email = f"{seed_profile.existing_user_email_prefix}-{index:02d}@example.com"
            user = User(
                email=email,
                name=f"{seed_profile.existing_user_name_prefix} {index:02d}",
                is_verified=True,
            )
            user.credential = Credential(password_hash=shared_password_hash)
            user.auth_identities = [AuthIdentity(provider="email", identifier=email)]
            seed_users.append(user)

        session.add_all(seed_users)
        await session.commit()


@pytest.fixture
def seeded_integration_client(integration_client: TestClient):
    asyncio.run(_seed_default_users())
    yield integration_client
