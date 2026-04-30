from typing import Final

AUTH_PASSWORD_POLICY_CASES: Final[list[tuple[str, str]]] = [
    ("lowercase1!", "uppercase"),
    ("NoNumber!", "number"),
    ("NoSymbol1", "symbol"),
    ("With Space1!", "spaces"),
]

AUTH_REFRESH_REQUEST_PAYLOAD: Final[dict[str, object]] = {
    "refresh_token": "refresh-token-mock-value",
    "user_id": 1,
    "session_id": "session-mock-001",
}

API_KEY_CREATE_PAYLOAD: Final[dict[str, str]] = {"name": "local-dev"}
