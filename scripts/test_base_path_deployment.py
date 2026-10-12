"""Build two monolithic images and verify them through an isolated real Nginx.

Requires Docker, installed frontend dependencies and Playwright Chromium.
No developer env files, host services or existing volumes are modified.
"""

import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def main():
    task = "b4-prefix-" + secrets.token_hex(4)
    prefixes = ["/qa/nested", "/another-app"]
    containers = []
    images = []
    network_created = False
    with tempfile.TemporaryDirectory(prefix=task) as temporary:
        temporary = Path(temporary)
        try:
            for index, prefix in enumerate(prefixes):
                tag = f"{task}:{index}"
                images.append(tag)
                run(
                    "docker",
                    "build",
                    "-f",
                    "docker/Dockerfile",
                    "--build-arg",
                    f"APP_BASE_PATH={prefix}",
                    "-t",
                    tag,
                    ".",
                    cwd=ROOT,
                )
            run("docker", "network", "create", task)
            network_created = True
            template = (ROOT / "docker/nginx/app-location.conf.template").read_text()
            fragments = [
                template.replace("${APP_BASE_PATH}", prefix).replace(
                    "${APP_UPSTREAM}", f"app-{index}:8000"
                )
                for index, prefix in enumerate(prefixes)
            ]
            config = temporary / "default.conf"
            config.write_text(
                "server { listen 80; server_name _;\n" + "\n".join(fragments) + "\n}"
            )
            # Create upstreams first because Nginx resolves upstream DNS at startup.
            for index, prefix in enumerate(prefixes):
                name = f"{task}-app-{index}"
                containers.append(name)
                run(
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--network",
                    task,
                    "--network-alias",
                    f"app-{index}",
                    "-e",
                    f"APP_BASE_PATH={prefix}",
                    "-e",
                    f"APP_BASE_URL=http://localhost{prefix}",
                    "-e",
                    "APP_MODE=development",
                    "-e",
                    "LOGIN_ENABLED=true",
                    "-e",
                    "EMAIL_ENABLED=false",
                    "-e",
                    "OAUTH_ENABLED=false",
                    "-e",
                    "STRIPE_ENABLED=false",
                    "-e",
                    "STARTUP_DISPLAY=off",
                    "-e",
                    "DB_DRIVER=sqlite+aiosqlite",
                    "-e",
                    "DB_NAME=/var/lib/b4fastapi/database/test.db",
                    "-e",
                    "OBJECT_STORAGE_LOCAL_ROOT=/var/lib/b4fastapi/objects",
                    "-e",
                    "REDIS_IN_MEMORY=true",
                    "-e",
                    "SSE_HEARTBEAT_SECONDS=1",
                    "-e",
                    f"SECRET_KEY={secrets.token_urlsafe(48)}",
                    images[index],
                )
            proxy = task + "-nginx"
            containers.append(proxy)
            run(
                "docker",
                "run",
                "-d",
                "--name",
                proxy,
                "--network",
                task,
                "-p",
                "127.0.0.1::80",
                "-v",
                f"{config}:/etc/nginx/conf.d/default.conf:ro",
                "nginx:stable-alpine",
            )
            port = (
                run("docker", "port", proxy, "80", capture_output=True)
                .stdout.strip()
                .rsplit(":", 1)[1]
            )
            origin = "http://127.0.0.1:" + port
            for prefix in prefixes:
                deadline = time.monotonic() + 60
                while True:
                    try:
                        with urlopen(
                            origin + prefix + "/health/ready", timeout=2
                        ) as response:
                            if json.load(response).get("status") == "ok":
                                break
                    except OSError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError(
                            "Isolated prefix instance did not become ready"
                        )
                    time.sleep(1)
            env = {
                **os.environ,
                "B4_DEPLOYMENT_TEST_URL": origin,
                "B4_DEPLOYMENT_TEST_PREFIXES": json.dumps(prefixes),
            }
            run(
                "npm",
                "run",
                "test:e2e",
                "--",
                "--config",
                "playwright.deployment.config.ts",
                cwd=ROOT / "src/frontend",
                env=env,
            )
            print("Two monolithic prefix deployments passed through Nginx.")
        except Exception:
            for name in containers:
                subprocess.run(["docker", "logs", "--tail", "25", name], check=False)
            raise
        finally:
            for name in reversed(containers):
                subprocess.run(
                    ["docker", "rm", "-f", name], check=False, stdout=subprocess.DEVNULL
                )
            if network_created:
                subprocess.run(
                    ["docker", "network", "rm", task],
                    check=False,
                    stdout=subprocess.DEVNULL,
                )
            for tag in images:
                subprocess.run(
                    ["docker", "image", "rm", tag],
                    check=False,
                    stdout=subprocess.DEVNULL,
                )


if __name__ == "__main__":
    main()
