"""Initialize a copied blueprint from a public identity/feature manifest."""

import argparse
import io
import json
import os
from pathlib import Path
import secrets
import stat
import sys
from datetime import UTC, datetime

from dotenv.parser import parse_stream

import env as env_files
from project_identity import brand_plan, validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def env_value(entries: dict[str, str], key: str) -> str | None:
    return next(
        (
            item.value
            for item in parse_stream(io.StringIO(entries.get(key, "")))
            if item.key == key
        ),
        None,
    )


def plan(root: Path, manifest_path: Path) -> dict[Path, bytes]:
    env_files.ROOT = root
    data = validate_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    child = root / "src/frontend"
    if not (child / "scripts/project-config.mjs").is_file():
        raise ValueError(
            "Pinned B4React with project config support is required; run make frontend-init"
        )
    output = brand_plan(data, manifest_path.parent, child)
    common = {
        "APP_NAME": data["name"] + " API",
        "EMAIL_BRAND_NAME": data["name"],
        "OTEL_SERVICE_NAME": data["slug"] + "-backend",
        **{
            f"{key.upper()}_ENABLED": str(value).lower()
            for key, value in data["features"].items()
        },
    }
    for directory in ("src/backend", "src/frontend", "docker"):
        folder = root / directory
        template, template_entries = env_files.read(folder / ".env.example")
        target = folder / ".env"
        _, entries = env_files.read(target, required=False)
        values = dict(entries)
        if directory != "src/frontend":
            overrides = dict(common)
            if directory == "docker":
                overrides.update(
                    APP_IMAGE=data["slug"] + ":local", COMPOSE_PROJECT_NAME=data["slug"]
                )
            if not set(overrides).issubset(template_entries):
                raise ValueError(
                    f"{directory}/.env.example is missing initializer-owned keys"
                )
            values.update(
                {key: f"{key}='{value}'\n" for key, value in overrides.items()}
            )
            # Generate only absent/default placeholder keys, never rotate a configured secret.
            if env_value(entries, "SECRET_KEY") in {None, "", "CHANGE_ME"}:
                values["SECRET_KEY"] = f"SECRET_KEY='{secrets.token_urlsafe(48)}'\n"
        output[target] = env_files.render(template, values).encode()
    for target in output:
        # Generated files must stay in the copied repository, without following symlinks.
        if target.is_symlink() or not target.resolve().is_relative_to(root.resolve()):
            raise ValueError(
                f"Refusing output outside the project: {target.relative_to(root)}"
            )
    return output


def apply_plan(root: Path, changes: dict[Path, bytes]) -> None:
    """Back up first, replace each file atomically, roll back completed writes on error."""
    previous = {
        path: (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        if path.exists()
        else None
        for path in changes
    }
    backup_root = (
        root / ".project-backups" / datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    )
    for path, old in previous.items():
        if old is not None:
            backup = backup_root / path.relative_to(root)
            backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(old[0])
    applied = []
    try:
        for path, content in changes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            write_atomic(path, content, previous[path][1] if previous[path] else 0o600)
            applied.append(path)
    except OSError:
        for path in reversed(applied):
            old = previous[path]
            if old is None:
                path.unlink(missing_ok=True)
            else:
                write_atomic(path, old[0], old[1])
        raise
    if any(old is not None for old in previous.values()):
        print(f"[backup] {backup_root.relative_to(root)}")


def write_atomic(path: Path, content: bytes, mode: int) -> None:
    import tempfile

    descriptor, name = tempfile.mkstemp(prefix=".project-init-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def run(command: str, root: Path, manifest: Path) -> int:
    output = plan(root, manifest)
    changes = {
        path: content
        for path, content in output.items()
        if not path.exists() or path.read_bytes() != content
    }
    for path in output:
        print(f"[{'change' if path in changes else 'ok'}] {path.relative_to(root)}")
    if command == "check":
        return int(bool(changes))
    if command == "apply" and changes:
        apply_plan(root, changes)
    print(
        f"[{command}] {len(changes)} file(s) {'updated' if command == 'apply' else 'would change'}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "check"))
    parser.add_argument(
        "--config", default=os.environ.get("PROJECT_CONFIG", "project.json")
    )
    args = parser.parse_args()
    try:
        return run(args.command, ROOT, Path(args.config).resolve())
    except (OSError, UnicodeError, json.JSONDecodeError):
        print(
            "[error] Cannot read/write project inputs. Check JSON, local logo paths and file permissions. Start with project.example.json.",
            file=sys.stderr,
        )
    except ValueError as error:
        print(f"[error] {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
