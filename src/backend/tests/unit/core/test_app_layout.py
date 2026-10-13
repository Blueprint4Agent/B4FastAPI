"""Deployment layout is runtime configuration, not a frontend build option."""

import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config.settings import SETTINGS, Settings
from app.main import create_app


@pytest.mark.parametrize("layout", ["sidebar", "topnav", "focused"])
def test_config_exposes_deployment_layout(monkeypatch, layout):
    # Given: a deployment chooses its layout without changing static assets.
    monkeypatch.setattr(SETTINGS, "APP_LAYOUT", layout)
    monkeypatch.setattr(SETTINGS, "LOGIN_ENABLED", True)
    # When: the existing public configuration endpoint is read.
    response = TestClient(create_app()).get("/config")
    # Then: clients receive the current choice without cache reuse.
    assert response.status_code == 200
    assert response.json()["app_layout"] == layout
    assert response.headers["cache-control"] == "no-store"


def test_layout_rejects_unknown_value():
    with pytest.raises(ValidationError, match="APP_LAYOUT"):
        Settings(APP_LAYOUT="navbar")


@pytest.mark.parametrize("layout", ["topnav", "focused", "invalid"])
def test_layout_reads_and_validates_process_environment(layout):
    # A fresh process exercises the environment-backed default rather than a model override.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from app.core.config.settings import SETTINGS; print(SETTINGS.APP_LAYOUT)",
        ],
        env={**os.environ, "APP_LAYOUT": layout},
        capture_output=True,
        text=True,
        check=False,
    )
    if layout == "invalid":
        assert result.returncode != 0
        assert "APP_LAYOUT" in result.stderr
    else:
        assert result.returncode == 0
        assert result.stdout.strip() == layout
