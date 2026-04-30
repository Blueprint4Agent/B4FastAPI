from dataclasses import dataclass
from typing import Final

from tests.fixtures.scenario_seed_data import (
    SEEDED_PRIMARY_EMAIL,
    SEEDED_PRIMARY_PASSWORD,
)


@dataclass(frozen=True)
class FullSystemScenarioSchema:
    scenario_name: str
    login_email: str
    login_password: str
    profile_update_name: str
    invalid_login_password: str
    malformed_signup_email: str
    api_key_name: str
    expect_disabled_api_key_rejected: bool = True
    expect_duplicate_api_key_name_rejected: bool = True


DEFAULT_FULL_SYSTEM_SCENARIO: Final = FullSystemScenarioSchema(
    scenario_name="seeded-primary-user-full-system-flow",
    login_email=SEEDED_PRIMARY_EMAIL,
    login_password=SEEDED_PRIMARY_PASSWORD,
    profile_update_name="Seeded Primary User Updated",
    invalid_login_password="WrongPass1!",
    malformed_signup_email="invalid-email-format",
    api_key_name="scenario-primary-key",
    expect_disabled_api_key_rejected=True,
    expect_duplicate_api_key_name_rejected=True,
)
