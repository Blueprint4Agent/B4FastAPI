import pytest

from app.core.config.settings import Settings


@pytest.mark.parametrize(
    "key",
    [
        "",
        " ",
        "CHANGE_ME",
        "CHANGE_ME_FOR_PRODUCTION",
        "CHANGE_ME" + "x" * 64,
        "x" * 31,
        " " + "x" * 64,
    ],
)
def test_production_rejects_unsafe_keys_without_disclosure(key):
    """Scenario: unsafe production keys fail before startup without revealing the value."""
    # Given/When: production settings contain a missing, example, short or padded key.
    with pytest.raises(ValueError, match="Production SECRET_KEY") as caught:
        Settings(APP_MODE="production", LOGIN_ENABLED=True, SECRET_KEY=key)
    # Then: error text explains the policy without serializing the configured secret.
    if len(key) > 8:
        assert key not in str(caught.value)


@pytest.mark.parametrize("algorithm,size", [("HS256", 32), ("HS384", 48), ("HS512", 64)])
def test_production_key_size_matches_signing_algorithm(algorithm, size):
    """Scenario: the configured HMAC digest sets the production key size boundary."""
    # Given: deterministic test-only key material at the algorithm boundary.
    kwargs = dict(APP_MODE="production", LOGIN_ENABLED=True, ALGORITHM=algorithm)
    # When/Then: one byte below fails while the required byte length succeeds.
    with pytest.raises(ValueError, match="Production SECRET_KEY"):
        Settings(**kwargs, SECRET_KEY="a" * (size - 1))
    assert Settings(**kwargs, SECRET_KEY="a" * size).ALGORITHM == algorithm


def test_development_keeps_placeholder_compatibility():
    """Scenario: development retains the documented local example configuration."""
    # Given/When/Then: production hardening does not break local initialization.
    assert Settings(APP_MODE="development", SECRET_KEY="CHANGE_ME").APP_MODE == "development"
