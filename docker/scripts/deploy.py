"""Single-host monolithic deployments; never print the resolved environment."""

import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from urllib.error import URLError
from urllib.request import Request, urlopen

DOCKER_DIR = Path(__file__).resolve().parents[1]
ROOT = DOCKER_DIR.parent


class DeployError(Exception):
    """Safe operator-facing diagnostic without configuration values."""


def require(condition, message):
    if not condition:
        raise DeployError(message)


def selected_env():
    path = Path(os.environ.get("DOCKER_ENV_FILE") or str(DOCKER_DIR / ".env"))
    return path.resolve()


def initialize():
    path = selected_env()
    require(
        not path.exists(),
        "Environment file already exists; edit it explicitly. No values changed.",
    )
    domain = os.environ.get("PUBLIC_DOMAIN", "").strip()
    require(
        not domain or valid_domain(domain),
        "PUBLIC_DOMAIN must be a hostname, without a scheme, port or path.",
    )
    values = {
        "SECRET_KEY": secrets.token_urlsafe(48),
        "DB_PASSWORD": secrets.token_urlsafe(32),
        "REDIS_PASSWORD": secrets.token_urlsafe(32),
        "APP_ENV": "production",
        "SWAGGER_ENABLED": "false",
    }
    if domain:
        origin = "https://" + domain
        values.update(
            PUBLIC_DOMAIN=domain,
            COMPOSE_FILE="docker-compose.yml:docker-compose.https.yml",
            APP_BASE_URL=origin,
            CORS_ORIGINS=origin,
            VITE_PUBLIC_SITE_URL=origin,
        )
    content = (DOCKER_DIR / ".env.example").read_text()
    for key, value in values.items():
        content = re.sub(
            rf"^{key}=.*$", lambda _: f"{key}={value}", content, flags=re.MULTILINE
        )
    # Atomic create: never rotate existing credentials or overwrite another deployment.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(content)
    print(
        "Created private deployment environment (0600); credentials were not printed."
    )
    print("Review settings, then run make docker-check and make docker-deploy.")
    if not domain:
        print("No public hostname selected; app access remains loopback-only.")


def valid_domain(value):
    return len(value) <= 253 and all(
        re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
        for label in value.split(".")
    )


class Deployment:
    def __init__(self):
        path = selected_env()
        require(
            path.is_file(),
            "Deployment environment is missing. Run make docker-init first.",
        )
        self.env = dict(os.environ, DOCKER_ENV_FILE=str(path))
        self.prefix = [
            "docker",
            "compose",
            "--project-directory",
            str(DOCKER_DIR),
            "--env-file",
            str(path),
        ]
        timeout = self.env.get("HEALTH_TIMEOUT_SECONDS") or "120"
        require(
            timeout.isdigit() and int(timeout) > 0,
            "HEALTH_TIMEOUT_SECONDS must be a positive integer.",
        )
        self.timeout = timeout
        self.model = None

    def compose(self, *args, capture=False):
        result = subprocess.run(
            self.prefix + list(args),
            cwd=DOCKER_DIR,
            env=self.env,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            check=True,
        )
        return result.stdout if capture else None

    def resolve(self):
        if self.model is None:
            self.model = json.loads(
                self.compose(
                    "--profile", "*", "config", "--format", "json", capture=True
                )
            )
        return self.model

    def settings(self):
        return self.resolve()["services"]["app"].get("environment", {})

    def services(self):
        settings = self.settings()
        services = []
        if (
            str(settings.get("DB_DRIVER", "")).startswith("postgresql")
            and settings.get("DB_HOST") == "postgres"
        ):
            services.append("postgres")
        mail = self.enabled("EMAIL_ENABLED") and self.enabled("LOGIN_ENABLED", "true")
        from urllib.parse import urlsplit

        broker = settings.get("CELERY_BROKER_URL", "") or ""
        broker_host = (
            urlsplit(broker).hostname if broker else settings.get("REDIS_HOST")
        )
        if (
            not self.enabled("REDIS_IN_MEMORY", "true")
            and settings.get("REDIS_HOST") == "redis"
        ) or (mail and broker_host == "redis"):
            services.append("redis")
        if mail:
            services.append("celery-worker")
        services.append("app")
        if "caddy" in self.resolve()["services"]:
            services.append("caddy")
        return services

    def enabled(self, key, default="false"):
        return str(self.settings().get(key, default)).lower() == "true"

    def check(self):
        settings = self.settings()
        from urllib.parse import urlsplit

        raw_base_path = str(settings.get("APP_BASE_PATH", "") or "")
        require(
            raw_base_path in ("", "/")
            or re.fullmatch(r"/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*/?", raw_base_path),
            "Invalid APP_BASE_PATH.",
        )
        base_path = raw_base_path.rstrip("/")
        require(
            not base_path
            or urlsplit(str(settings.get("APP_BASE_URL", ""))).path.rstrip("/")
            == base_path,
            "APP_BASE_URL must include APP_BASE_PATH.",
        )
        require(
            not base_path or "caddy" not in self.resolve()["services"],
            "Prefix deployments use an external reverse proxy; disable the root-only Caddy overlay.",
        )
        driver = settings.get("DB_DRIVER", "")
        if driver.startswith("sqlite"):
            path = PurePosixPath(settings.get("DB_NAME", ""))
            require(
                path.is_absolute()
                and PurePosixPath("/var/lib/b4fastapi/database") in path.parents
                and ".." not in path.parts,
                "SQLite deployment requires DB_NAME=/var/lib/b4fastapi/database/<file>. Back up and move existing data before recreation.",
            )
        if settings.get("APP_MODE") == "production":
            require(
                self.enabled("LOGIN_ENABLED", "true"),
                "Production requires LOGIN_ENABLED=true.",
            )
            key = settings.get("SECRET_KEY", "") or ""
            minimum = {"HS256": 32, "HS384": 48, "HS512": 64}.get(
                settings.get("ALGORITHM", "HS256")
            )
            require(
                minimum
                and key == key.strip()
                and len(key.encode()) >= minimum
                and not key.startswith("CHANGE_ME"),
                "Set a random production SECRET_KEY of sufficient length for ALGORITHM; existing keys must not be casually rotated.",
            )
            if driver.startswith("postgresql"):
                require(
                    settings.get("DB_PASSWORD")
                    not in (None, "", "postgres", "CHANGE_ME"),
                    "Set a non-default DB_PASSWORD; existing database credentials require a separate coordinated change.",
                )
            if "redis" in self.services():
                require(
                    bool(settings.get("REDIS_PASSWORD")),
                    "Set REDIS_PASSWORD for the local production Redis service.",
                )
        if "caddy" in self.resolve()["services"]:
            domain = self.resolve()["services"]["caddy"]["environment"].get(
                "PUBLIC_DOMAIN", ""
            )
            require(
                valid_domain(domain),
                "PUBLIC_DOMAIN must be a hostname without scheme, port or path.",
            )
            origin = "https://" + domain
            require(
                str(settings.get("APP_BASE_URL", "")).rstrip("/") == origin,
                "APP_BASE_URL must match the HTTPS PUBLIC_DOMAIN origin.",
            )
            origins = [
                value.strip()
                for value in str(settings.get("CORS_ORIGINS", "")).split(",")
            ]
            require(
                origin in origins,
                "CORS_ORIGINS must include the HTTPS PUBLIC_DOMAIN origin.",
            )
            sharing = (
                self.resolve()["services"]["app"]
                .get("build", {})
                .get("args", {})
                .get("VITE_PUBLIC_SITE_URL", "")
            )
            require(
                not sharing or sharing.rstrip("/") == origin,
                "VITE_PUBLIC_SITE_URL must match the monolithic HTTPS origin or remain empty.",
            )
        print(
            "Preflight passed. Selected services: " + ", ".join(self.services()),
            flush=True,
        )

    def validate_image(self):
        # Validate with the shipped Settings class, without host uv or exposing errors' input values.
        code = """import sys
try:
 from app.core.config import SETTINGS
 errors = SETTINGS.get_smtp_validation_errors() + SETTINGS.get_oauth_validation_errors()
 if errors:
  print("Enabled email/OAuth settings are incomplete; review the deployment environment.", file=sys.stderr)
  sys.exit(1)
except Exception:
 print("Application settings validation failed; review the deployment environment (values suppressed).", file=sys.stderr)
 sys.exit(1)
print("Image application settings passed.")"""
        self.compose(
            "run",
            "--pull",
            "never",
            "--rm",
            "--no-deps",
            "--entrypoint",
            "./.venv/bin/python",
            "app",
            "-c",
            code,
        )

    def prepare(self, source, extra=()):
        require(
            source in ("build", "pull", "local"),
            "DEPLOY_SOURCE must be build, pull or local.",
        )
        if source == "build":
            require(
                (ROOT / "src/frontend/package.json").is_file(),
                "Initialize the pinned frontend: git submodule update --init --recursive",
            )
            self.compose("build", "app", *extra)
        elif source == "pull":
            self.compose("pull", "app")
        subprocess.run(
            [
                "docker",
                "image",
                "inspect",
                "--format",
                "{{.Id}}",
                self.resolve()["services"]["app"]["image"],
            ],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        )
        self.validate_image()

    def up(self, extra=()):
        for service in self.services():
            flags = (
                ["--no-recreate"] if service in ("postgres", "redis") else list(extra)
            )
            self.compose(
                "up",
                "-d",
                "--no-deps",
                "--no-build",
                *flags,
                "--wait",
                "--wait-timeout",
                self.timeout,
                service,
            )

    def smoke(self):
        if "caddy" in self.resolve()["services"]:
            origin = self.settings()["APP_BASE_URL"].rstrip("/")
        else:
            ports = self.resolve()["services"]["app"].get("ports", [])
            port = next(
                (p.get("published") for p in ports if str(p.get("target")) == "8000"),
                None,
            )
            require(
                port,
                "App HTTP port is unavailable; configure APP_HOST_PORT for local smoke checks.",
            )
            origin = "http://127.0.0.1:" + str(port)
        deadline = time.monotonic() + int(self.timeout)
        while True:
            try:
                self.probe(origin)
                break
            except (OSError, URLError, ValueError, DeployError):
                if time.monotonic() >= deadline:
                    raise DeployError(
                        "HTTP smoke failed. Check docker-status/docker-logs, DNS, TLS and configured origin; no automatic rollback was attempted."
                    ) from None
                time.sleep(2)
        print(
            "HTTP smoke passed: readiness, runtime config, SPA and built JavaScript"
            + (
                ", public route protection."
                if "caddy" in self.resolve()["services"]
                else "."
            )
        )

    def probe(self, origin):
        def fetch(path, accept="application/json"):
            request = Request(origin + path, headers={"Accept": accept})
            with urlopen(request, timeout=5) as response:
                require(response.status == 200, "Unexpected HTTP status")
                return response.read(4_000_000).decode()

        require(
            json.loads(fetch("/health/ready")).get("status") == "ok", "Readiness failed"
        )
        config = json.loads(fetch("/config"))
        require(
            config.get("app_mode") == self.settings().get("APP_MODE", "development"),
            "Runtime mode mismatch",
        )
        html = fetch("/login", "text/html")
        base_path = str(self.settings().get("APP_BASE_PATH", "") or "").rstrip("/")
        asset = re.search(
            r'<script[^>]+src="((?:\.|'
            + re.escape(base_path)
            + r')/assets/[^"<>]+\.js)"',
            html,
        )
        require(asset is not None, "Packaged frontend missing")
        require(
            "<html"
            not in fetch(
                asset.group(1)[1:]
                if asset.group(1).startswith("./")
                else asset.group(1)[len(base_path) :],
                "application/javascript",
            ).lower(),
            "JavaScript asset returned SPA fallback",
        )
        if "caddy" in self.resolve()["services"]:
            from urllib.error import HTTPError

            for path in ("/metrics", "/docs", "/openapi.json"):
                try:
                    fetch(path, "text/html")
                except HTTPError as error:
                    require(error.code == 404, "Public route protection failed")
                else:
                    raise DeployError("Public route protection failed")

    def export(self):
        image = self.resolve()["services"]["app"]["image"]
        directory = DOCKER_DIR / "artifacts"
        directory.mkdir(exist_ok=True)
        name = re.sub(r"[^a-zA-Z0-9_.-]", "_", image)
        target = directory / f"{name}-{time.strftime('%Y%m%d-%H%M%S')}.tar"
        subprocess.run(["docker", "save", "-o", str(target), image], check=True)
        print("Export complete: " + str(target))


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    extra = sys.argv[2:]
    try:
        if action == "init":
            initialize()
            return 0
        if action == "help":
            print(
                "Commands: init, check, build, up, deploy, smoke, status, logs, down, export"
            )
            return 0
        deployment = Deployment()
        if action == "check":
            deployment.check()
            subprocess.run(
                ["docker", "info", "--format", "Docker server: {{.ServerVersion}}"],
                check=True,
            )
        elif action == "build":
            deployment.check()
            deployment.prepare("build", extra)
        elif action in ("deploy", "up"):
            deployment.check()
            source = (
                (os.environ.get("DEPLOY_SOURCE") or "build")
                if action == "deploy"
                else "local"
            )
            deployment.prepare(source)
            deployment.up(("--force-recreate",) if action == "deploy" else extra)
            if action == "deploy":
                deployment.smoke()
                deployment.compose("ps")
                if (
                    deployment.settings().get("INDEXNOW_ENABLED", "false").lower()
                    == "true"
                ):
                    build_args = (
                        deployment.resolve()["services"]["app"]
                        .get("build", {})
                        .get("args", {})
                    )
                    subprocess.run(
                        [
                            sys.executable,
                            str(ROOT / "scripts/indexnow.py"),
                            "--origin",
                            deployment.settings().get("APP_BASE_URL", ""),
                            "--key",
                            str(build_args.get("VITE_INDEXNOW_KEY", "")),
                            "--state",
                            str(DOCKER_DIR / ".indexnow/accepted.json"),
                            "--submit",
                        ],
                        cwd=ROOT,
                        check=True,
                    )
                print(
                    "Deployment complete. Data volumes retained; image export is a separate command."
                )
        elif action == "smoke":
            deployment.check()
            deployment.smoke()
        elif action == "status":
            deployment.compose("ps", "--all")
            deployment.compose("images")
        elif action == "logs":
            deployment.compose("logs", "--tail", "100", "-f", *(extra or ["app"]))
        elif action == "down":
            deployment.compose("down", "--remove-orphans", *extra)
        elif action == "export":
            deployment.export()
        else:
            raise DeployError("Unknown deployment command.")
        return 0
    except (
        DeployError,
        OSError,
        subprocess.CalledProcessError,
        ValueError,
        KeyError,
    ) as error:
        message = (
            str(error)
            if isinstance(error, DeployError)
            else "Deployment command failed; check Docker availability and configuration. Secret values were not printed."
        )
        print(message, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
