from fastapi import FastAPI

from app.core import tracing
from app.core.settings import SETTINGS


def test_tracing_setup_is_noop_when_disabled() -> None:
    original_tracing_enabled = SETTINGS.TRACING_ENABLED
    object.__setattr__(SETTINGS, "TRACING_ENABLED", False)
    app = FastAPI()

    try:
        setup_result = tracing.setup_tracing(app)
    finally:
        object.__setattr__(SETTINGS, "TRACING_ENABLED", original_tracing_enabled)

    assert setup_result is None
    assert not any(
        "OpenTelemetryMiddleware" in repr(middleware.cls) for middleware in app.user_middleware
    )


def test_trace_sample_ratio_is_clamped() -> None:
    original_ratio = SETTINGS.OTEL_TRACE_SAMPLE_RATIO
    try:
        object.__setattr__(SETTINGS, "OTEL_TRACE_SAMPLE_RATIO", -1.0)
        assert tracing._trace_sample_ratio() == 0.0

        object.__setattr__(SETTINGS, "OTEL_TRACE_SAMPLE_RATIO", 2.0)
        assert tracing._trace_sample_ratio() == 1.0
    finally:
        object.__setattr__(SETTINGS, "OTEL_TRACE_SAMPLE_RATIO", original_ratio)
