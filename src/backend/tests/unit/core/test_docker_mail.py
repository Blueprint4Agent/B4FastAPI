"""Exercise deployment ordering without touching the developer's Docker stack."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[5]


@pytest.mark.parametrize(
    ("email", "login", "broker", "expected"),
    [
        ("true", "true", "", ["redis", "celery-worker", "app"]),
        ("true", "true", "redis://external:6379/0", ["celery-worker", "app"]),
        ("false", "true", "", ["app"]),
        ("true", "false", "", ["app"]),
    ],
)
def test_deploy_starts_mail_consumer_before_api(tmp_path, email, login, broker, expected):
    """Scenario: only enabled mail starts a worker, and its broker precedes the API."""
    # Given: an isolated Compose model with API fakeredis.
    settings = {
        "EMAIL_ENABLED": email,
        "LOGIN_ENABLED": login,
        "CELERY_BROKER_URL": broker,
        "REDIS_IN_MEMORY": "true",
        "REDIS_HOST": "redis",
        "DB_DRIVER": "sqlite",
    }
    run, calls = deployment_fixture(tmp_path, settings)
    # When: deploying with recreation requested.
    result = run()
    # Then: only the needed services start, with worker readiness before API startup.
    assert result.returncode == 0, result.stderr
    commands = [json.loads(line) for line in calls.read_text().splitlines()]
    starts = [command for command in commands if "up" in command]
    assert [command[-1] for command in starts] == expected
    for command in starts:
        assert "--wait" in command
        if command[-1] == "redis":
            assert "--no-recreate" in command
            assert "--force-recreate" not in command
        else:
            assert "--force-recreate" in command


def test_failed_mail_worker_prevents_api_rollout(tmp_path):
    """Scenario: failed worker health prevents deployment of a new mail producer."""
    # Given: a worker readiness failure.
    run, calls = deployment_fixture(
        tmp_path,
        {
            "EMAIL_ENABLED": "true",
            "LOGIN_ENABLED": "true",
            "REDIS_HOST": "redis",
            "REDIS_IN_MEMORY": "false",
        },
        fail_worker=True,
    )
    # When: the deploy script runs.
    result = run()
    # Then: it does not start/recreate the API.
    assert result.returncode != 0
    commands = [json.loads(line) for line in calls.read_text().splitlines()]
    assert not any("up" in command and command[-1] == "app" for command in commands)


def deployment_fixture(tmp_path, settings, fail_worker=False):
    scripts = tmp_path / "docker/scripts"
    scripts.mkdir(parents=True)
    shutil.copyfile(SOURCE / "docker/scripts/docker-up.sh", scripts / "docker-up.sh")
    (tmp_path / "docker/.env").write_text("# fixture\n")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    calls = tmp_path / "calls.jsonl"
    docker = bin_dir / "docker"
    docker.write_text("""#!/usr/bin/env python3
import json, os, sys
with open(os.environ["TEST_CALLS"], "a") as output:
    output.write(json.dumps(sys.argv[1:]) + "\\n")
if "config" in sys.argv:
    print(os.environ["TEST_MODEL"])
if "up" in sys.argv and sys.argv[-1] == "celery-worker" and os.environ["TEST_FAIL"] == "1":
    sys.exit(2)
""")
    docker.chmod(0o755)
    uv = bin_dir / "uv"
    uv.write_text("""#!/usr/bin/env python3
import os, sys
index = sys.argv.index("-c")
os.execv(sys.executable, [sys.executable] + sys.argv[index:])
""")
    uv.chmod(0o755)
    env = dict(
        os.environ,
        PATH=f"{bin_dir}:{os.environ['PATH']}",
        UV=str(uv),
        TEST_CALLS=str(calls),
        TEST_MODEL=json.dumps({"services": {"app": {"environment": settings}}}),
        TEST_FAIL="1" if fail_worker else "0",
    )
    return lambda: subprocess.run(
        ["bash", str(scripts / "docker-up.sh"), "--force-recreate"],
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
    ), calls
