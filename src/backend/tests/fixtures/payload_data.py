from typing import Final

VALID_PASSWORD: Final = "ValidPass1!"
INVALID_EMAIL: Final = "invalid-email-format"


def build_signup_payload(
    *,
    email: str = "tester@example.com",
    name: str = "Tester",
    password: str = VALID_PASSWORD,
) -> dict[str, object]:
    return {
        "email": email,
        "name": name,
        "password": password,
    }


def build_login_payload(
    *,
    email: str = "tester@example.com",
    password: str = VALID_PASSWORD,
    remember_me: bool = False,
) -> dict[str, object]:
    return {
        "email": email,
        "password": password,
        "remember_me": remember_me,
    }
