"""Deployment behavior tested with fake Docker and real local HTTP, never user stacks."""

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[5]
SPEC = importlib.util.spec_from_file_location("deployment", SOURCE / "docker/scripts/deploy.py")
deployment = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(deployment)


@pytest.fixture
def project(tmp_path):
    scripts = tmp_path / "docker/scripts"
    scripts.mkdir(parents=True)
    shutil.copyfile(SOURCE / "docker/scripts/deploy.py", scripts / "deploy.py")
    shutil.copyfile(SOURCE / "docker/.env.example", tmp_path / "docker/.env.example")
    (tmp_path / "src/frontend").mkdir(parents=True)
    (tmp_path / "src/frontend/package.json").write_text("{}")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text("""#!/usr/bin/env python3
import json, os, sys
args=sys.argv[1:]
with open(os.environ["TEST_CALLS"], "a") as output:
 output.write(json.dumps(args)+"\\n")
if "config" in args:
 print(os.environ["TEST_MODEL"])
if os.environ.get("TEST_FAIL_ACTION") in args:
 sys.exit(7)
""")
    docker.chmod(0o755)
    env_path = tmp_path / "chosen.env"
    calls = tmp_path / "calls.jsonl"
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "DOCKER_ENV_FILE": str(env_path),
        "TEST_CALLS": str(calls),
        "HEALTH_TIMEOUT_SECONDS": "1",
        "PUBLIC_DOMAIN": "",
        "DEPLOY_SOURCE": "local",
    }
    model = {
        "services": {
            "app": {
                "image": "example:reviewed",
                "environment": {
                    "APP_MODE": "development",
                    "DB_DRIVER": "sqlite+aiosqlite",
                    "DB_NAME": "/var/lib/b4fastapi/database/app.db",
                    "REDIS_IN_MEMORY": "true",
                },
            }
        }
    }

    def run(action, **overrides):
        return subprocess.run(
            ["python3", str(scripts / "deploy.py"), action],
            env={**env, "TEST_MODEL": json.dumps(model), **overrides},
            text=True,
            capture_output=True,
            timeout=15,
        )

    return run, model, env_path, calls


def test_init_generates_private_settings_without_overwriting(project):
    # Given: a new server hostname and no existing configuration.
    run, _, env_path, _ = project
    result = run("init", PUBLIC_DOMAIN="app.example.test")
    # When/Then: credentials are generated privately and HTTPS selection persists.
    assert result.returncode == 0, result.stderr
    content = env_path.read_text()
    assert stat.S_IMODE(env_path.stat().st_mode) == 0o600
    assert "COMPOSE_FILE=docker-compose.yml:docker-compose.https.yml" in content
    assert "APP_BASE_URL=https://app.example.test" in content
    assert "SECRET_KEY=CHANGE_ME" not in content
    secret = next(
        line.split("=", 1)[1] for line in content.splitlines() if line.startswith("SECRET_KEY=")
    )
    assert len(secret) >= 64
    assert secret not in result.stdout + result.stderr
    assert run("init", PUBLIC_DOMAIN="other.example.test").returncode != 0
    assert env_path.read_text() == content


def test_unsafe_settings_stop_before_build_or_recreation(project):
    # Given: a production placeholder secret in an explicitly selected file.
    run, model, env_path, calls = project
    env_path.write_text("# private\n")
    model["services"]["app"]["environment"].update(APP_MODE="production", SECRET_KEY="CHANGE_ME")
    # When: the complete deploy command is called.
    result = run("deploy", DEPLOY_SOURCE="build")
    # Then: no image/container mutation and no secret value disclosure.
    assert result.returncode != 0
    commands = [json.loads(line) for line in calls.read_text().splitlines()]
    assert all("config" in command for command in commands)
    assert "CHANGE_ME" not in result.stderr
    assert str(env_path) in commands[0]


def test_proxy_requires_matching_origin_and_starts_after_app(project):
    # Given: a selected HTTPS overlay.
    run, model, env_path, calls = project
    env_path.write_text("# fixture\n")
    model["services"]["caddy"] = {"environment": {"PUBLIC_DOMAIN": "app.example.test"}}
    settings = model["services"]["app"]["environment"]
    settings.update(APP_BASE_URL="http://wrong.test", CORS_ORIGINS="https://app.example.test")
    assert run("up").returncode != 0
    settings["APP_BASE_URL"] = "https://app.example.test"
    # When: the matching origin is deployed.
    result = run("up")
    # Then: app readiness precedes the proxy; the selected env is used for every call.
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in calls.read_text().splitlines()]
    assert [c[-1] for c in commands if "up" in c] == ["app", "caddy"]
    assert all(str(env_path) in c for c in commands if "compose" in c)


@pytest.mark.parametrize("action,source", [("pull", "pull"), ("run", "local"), ("build", "build")])
def test_image_failure_prevents_recreation(project, action, source):
    # Given: image pull/build/settings validation fails.
    run, _, env_path, calls = project
    env_path.write_text("# fixture\n")
    result = run("deploy", DEPLOY_SOURCE=source, TEST_FAIL_ACTION=action)
    # Then: existing app and infrastructure remain untouched.
    assert result.returncode != 0
    assert not any("up" in json.loads(line) for line in calls.read_text().splitlines())


@pytest.mark.parametrize("served_mode", ["development", "production"])
def test_deploy_checks_real_http_without_forcing_an_export(project, served_mode):
    # Given: a real local HTTP service serving the expected packaged contract.
    run, model, env_path, calls = project
    env_path.write_text("# fixture\n")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/login" and "text/html" not in self.headers.get("Accept", ""):
                self.send_response(404)
                self.end_headers()
                return
            body = {
                "/health/ready": '{"status":"ok"}',
                "/config": json.dumps({"app_mode": served_mode}),
                "/login": '<html><script src="/assets/app.js"></script></html>',
                "/assets/app.js": "window.ready = true;",
            }[self.path]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    model["services"]["app"]["ports"] = [{"target": 8000, "published": str(server.server_port)}]
    try:
        # When: using a previously prepared image.
        result = run("deploy")
        # Then: HTTP checks precede success and no archive/build/pull is forced.
        if served_mode != "development":
            assert result.returncode != 0
            assert "Deployment complete" not in result.stdout
            return
        assert result.returncode == 0, result.stderr
        assert "HTTP smoke passed" in result.stdout
        assert "Deployment complete" in result.stdout
        commands = [json.loads(line) for line in calls.read_text().splitlines()]
        assert not any(any(action in c for action in ("save", "build", "pull")) for c in commands)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_spa_fallback_cannot_pass_as_a_javascript_asset(monkeypatch):
    # Given: an otherwise healthy deployment returning HTML for its JavaScript URL.
    instance = object.__new__(deployment.Deployment)
    instance.model = {"services": {"app": {"environment": {"APP_MODE": "development"}}}}
    responses = iter(
        [
            '{"status":"ok"}',
            '{"app_mode":"development"}',
            '<html><script src="/assets/app.js"></script></html>',
            "<html>fallback</html>",
        ]
    )

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, size):
            return next(responses).encode()

    monkeypatch.setattr(deployment, "urlopen", lambda *args, **kwargs: Response())
    # When/Then: readiness alone cannot report successful frontend delivery.
    with pytest.raises(deployment.DeployError, match="JavaScript"):
        instance.probe("http://127.0.0.1")


@pytest.mark.parametrize("smoke_fails", [False, True])
def test_indexnow_runs_only_after_successful_deployment_smoke(monkeypatch, smoke_fails):
    # Given: an explicitly enabled IndexNow deployment with all Docker work faked.
    from unittest.mock import MagicMock

    instance = MagicMock()
    instance.settings.return_value = {
        "INDEXNOW_ENABLED": "true",
        "APP_BASE_URL": "https://example.test",
    }
    instance.resolve.return_value = {
        "services": {"app": {"build": {"args": {"VITE_INDEXNOW_KEY": "public-key-123"}}}}
    }
    if smoke_fails:
        instance.smoke.side_effect = deployment.DeployError("smoke failed")
    monkeypatch.setattr(deployment, "Deployment", lambda: instance)
    monkeypatch.setattr(deployment.sys, "argv", ["deploy.py", "deploy"])
    send = MagicMock()
    monkeypatch.setattr(deployment.subprocess, "run", send)
    # When: completing the deployment entry point.
    result = deployment.main()
    # Then: failed readiness cannot notify search engines; success uses explicit submission.
    assert result == (1 if smoke_fails else 0)
    if smoke_fails:
        send.assert_not_called()
    else:
        instance.smoke.assert_called_once()
        args = send.call_args.args[0]
        assert "--submit" in args
        assert args[args.index("--origin") + 1] == "https://example.test"


def test_prefix_preflight_requires_public_url_without_build_arguments(project):
    run, model, env_path, _ = project
    env_path.write_text("APP_MODE=development\n")
    app = model["services"]["app"]
    app["environment"].update(
        APP_BASE_PATH="/demos/alpha", APP_BASE_URL="https://example.test/demos/alpha"
    )
    assert run("check").returncode == 0
    app["environment"]["APP_BASE_URL"] = "https://example.test"
    assert run("check").returncode != 0


@pytest.mark.parametrize("asset_path", ["/demos/alpha/assets/app.js", "./assets/app.js"])
def test_prefix_smoke_fetches_stripped_upstream_asset(monkeypatch, asset_path):
    instance = object.__new__(deployment.Deployment)
    instance.model = {
        "services": {
            "app": {"environment": {"APP_MODE": "development", "APP_BASE_PATH": "/demos/alpha"}}
        }
    }
    responses = iter(
        [
            '{"status":"ok"}',
            '{"app_mode":"development"}',
            f'<html><script src="{asset_path}"></script></html>',
            "window.loaded=true;",
        ]
    )
    requests = []

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, size):
            return next(responses).encode()

    def fetch(request, **kwargs):
        requests.append(request.full_url)
        return Response()

    monkeypatch.setattr(deployment, "urlopen", fetch)
    instance.probe("http://127.0.0.1:8001")
    assert requests[-1] == "http://127.0.0.1:8001/assets/app.js"
