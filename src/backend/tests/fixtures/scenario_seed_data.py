from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class SeedUserSchema:
    email: str
    name: str
    password: str
    is_verified: bool = True


@dataclass(frozen=True)
class SeedProfileSchema:
    profile_name: str
    primary_user: SeedUserSchema
    existing_user_count: int
    existing_user_email_prefix: str = "seeded-user"
    existing_user_name_prefix: str = "Seeded User"
    existing_user_start_index: int = 1


DEFAULT_SEED_PROFILE: Final = SeedProfileSchema(
    profile_name="default-baseline",
    primary_user=SeedUserSchema(
        email="seeded-primary@example.com",
        name="Seeded Primary User",
        password="SeededPass1!",
        is_verified=True,
    ),
    existing_user_count=50,
)

# Compatibility exports for scenario tests that assert specific baseline values.
SEEDED_PRIMARY_EMAIL: Final = DEFAULT_SEED_PROFILE.primary_user.email
SEEDED_PRIMARY_NAME: Final = DEFAULT_SEED_PROFILE.primary_user.name
SEEDED_PRIMARY_PASSWORD: Final = DEFAULT_SEED_PROFILE.primary_user.password
SEEDED_EXISTING_USER_COUNT: Final = DEFAULT_SEED_PROFILE.existing_user_count
