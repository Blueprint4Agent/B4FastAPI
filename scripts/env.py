"""Synchronize env keys without evaluating or replacing existing values."""

import argparse
import io
import os
import re
import stat
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from dotenv.parser import parse_stream

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("src/backend", "src/frontend", "docker")
DOCKER_ONLY_KEYS = {"APP_IMAGE"}


def value_span(assignment: str) -> tuple[int, int]:
    """Locate the literal value, retaining its quoting and escape semantics."""
    prefix = re.match(
        r"\s*(?:export[^\S\r\n]+)?(?:'[^']*'|[^=\#\s]+)[^\S\r\n]*=[^\S\r\n]*",
        assignment,
    )
    if prefix is None:
        raise ValueError("Unsupported env assignment syntax")
    start = prefix.end()
    tail = assignment[start:]
    if tail.startswith(("'", '"')):
        quote = tail[0]
        match = re.match(r"'((?:\\'|[^'])*)'" if quote == "'" else r'"((?:\\"|[^"])*)"', tail)
        if match is None:
            raise ValueError("Unterminated quoted env value")
        return start, start + match.end()
    line = re.split(r"[\r\n]", tail, maxsplit=1)[0]
    value = re.split(r"\s+#", line, maxsplit=1)[0].rstrip()
    return start, start + len(value)


def render(template: str, existing: dict[str, str]) -> str:
    """Use template layout and comments, replacing only value tokens."""
    chunks = []
    expected = set()
    for binding in parse_stream(io.StringIO(template)):
        original = binding.original.string
        if binding.key is not None:
            expected.add(binding.key)
            if binding.key in existing:
                start, end = value_span(original)
                old = existing[binding.key]
                old_start, old_end = value_span(old)
                original = original[:start] + old[old_start:old_end] + original[end:]
        chunks.append(original)
    result = "".join(chunks)
    extra = sorted(set(existing) - expected)
    if extra:
        newline = "\r\n" if "\r\n" in template else "\n"
        result = result.rstrip("\r\n") + newline * 2
        result += "# Additional keys not in .env.example (retained)" + newline
        result += "".join(existing[key].strip() + newline for key in extra)
    return result


def read(path: Path, *, required: bool = True) -> tuple[str, dict[str, str]]:
    if not path.exists():
        if required:
            target = "docker-env-sync" if path.parent.name == "docker" else "env-sync"
            raise ValueError(f"{path.relative_to(ROOT)}: missing file; run make {target}")
        return "", {}
    with path.open(encoding="utf-8", newline="") as stream:
        content = stream.read()
    entries = {}
    for binding in parse_stream(io.StringIO(content)):
        location = f"{path.relative_to(ROOT)}:{binding.original.line}"
        if binding.error:
            raise ValueError(f"{location}: invalid env syntax")
        if binding.key is None:
            continue
        if binding.value is None:
            raise ValueError(f"{location}: assignment required for {binding.key}")
        if binding.key in entries:
            raise ValueError(f"{location}: duplicate key {binding.key}")
        entries[binding.key] = binding.original.string
    return content, entries


def write(path: Path, content: str) -> None:
    # Write beside the destination so replacement is atomic. Keep existing modes.
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    if path.exists():
        backup_dir = ROOT / ".env-backups"
        backup_dir.mkdir(mode=0o700, exist_ok=True)
        name = "-".join(path.relative_to(ROOT).parts[:-1])
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        backup_fd, backup_name = tempfile.mkstemp(
            prefix=f"{name}-{timestamp}-", suffix=".env.bak", dir=backup_dir
        )
        with os.fdopen(backup_fd, "wb") as backup:
            backup.write(path.read_bytes())
        print(f"[backup] {Path(backup_name).relative_to(ROOT)}")
    descriptor, temporary = tempfile.mkstemp(prefix=".env-sync-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sync", "check", "contract-check"))
    parser.add_argument("--scope", choices=("dev", "docker"), default="dev")
    args = parser.parse_args()
    directories = ("src/backend", "src/frontend") if args.scope == "dev" else ("docker",)
    try:
        # Read every file before making changes; malformed files block updates.
        templates = {
            directory: read(ROOT / directory / ".env.example")
            for directory in DIRECTORIES
            if directory != "src/frontend"
            or (args.scope == "dev" and args.command != "contract-check")
        }
        backend_keys = set(templates["src/backend"][1])
        docker_keys = set(templates["docker"][1]) - DOCKER_ONLY_KEYS
        if backend_keys != docker_keys:
            for path, missing in (
                ("docker/.env.example", backend_keys - docker_keys),
                ("src/backend/.env.example", docker_keys - backend_keys),
            ):
                if missing:
                    print(f"[error] {path}: missing shared keys: {', '.join(sorted(missing))}")
            return 1
        if args.command == "contract-check":
            print("[ok] backend/docker example keys match (excluding Docker-only APP_IMAGE)")
            return 0
        actual = {
            directory: read(ROOT / directory / ".env", required=args.command == "check")
            for directory in directories
        }
        rendered = {
            directory: render(templates[directory][0], actual[directory][1])
            for directory in directories
        }
        failed = False
        for directory in directories:
            path = ROOT / directory / ".env"
            _, expected = templates[directory]
            content, existing = actual[directory]
            updated = rendered[directory]
            missing = [key for key in expected if key not in existing]
            extra = sorted(set(existing) - set(expected))
            if extra:
                print(f"[warn] {directory}/.env: additional keys retained: {', '.join(extra)}")
            if args.command == "sync":
                if not path.exists():
                    write(path, updated)
                    print(f"[created] {directory}/.env")
                elif content != updated:
                    write(path, updated)
                    print(f"[updated] {directory}/.env: synchronized template layout and keys")
                else:
                    print(f"[ok] {directory}/.env: already synchronized")
            elif missing:
                print(f"[error] {directory}/.env: missing keys: {', '.join(missing)}")
                failed = True
            elif content != updated:
                print(
                    f"[error] {directory}/.env: comments or layout differ from template; run sync"
                )
                failed = True
            else:
                print(f"[ok] {directory}/.env: keys and template layout match")
        return int(failed)
    except (OSError, UnicodeError):
        print("[error] Unable to read or write env files; check paths and permissions.")
        return 1
    except ValueError as error:
        print(f"[error] {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
