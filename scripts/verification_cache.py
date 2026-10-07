"""Local, content-bound command receipts; never a remote CI attestation."""
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import shutil
import subprocess
import time

TTL_SECONDS = 24 * 60 * 60


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL)


def snapshot(root):
    digest = hashlib.sha256()
    paths = set(git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0"))
    # Local identity/environment can affect builds/tests. Only their digest is stored.
    paths.update((".env", "project.local.json", "project.json", "src/backend/.env", "node_modules/.package-lock.json", "src/backend/.venv/pyvenv.cfg"))
    paths.add(os.environ.get("PROJECT_CONFIG", "project.json"))
    branding = root / "public/project-brand"
    if branding.is_dir():
        paths.update(str(file.relative_to(root)) for file in branding.rglob("*") if file.is_file())
    for name in sorted(paths - {""}):
        # Worklogs are always checked by lightweight validation and Git governance.
        if name.startswith("worklog/") and name.endswith(".md"):
            continue
        path = root / name
        digest.update(name.encode() + b"\0")
        if path.is_symlink():
            digest.update(b"symlink:" + os.readlink(path).encode())
        elif path.is_file():
            digest.update(str(stat.S_IMODE(path.stat().st_mode)).encode())
            digest.update(path.read_bytes())
        elif path.is_dir() and (path / ".git").exists():
            digest.update(snapshot(path).encode())
        else:
            digest.update(b"missing")
    return digest.hexdigest()


def normalized_path(value):
    # Git prepends its helper directory in hooks. It is not a project toolchain override.
    try:
        helper = subprocess.check_output(["git", "--exec-path"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        helper = None
    return os.pathsep.join(dict.fromkeys(
        entry for entry in value.split(os.pathsep) if entry != helper
    ))


def context():
    result = {"python": platform.python_version(), "platform": platform.platform()}
    # Record resolved tools as well as versions; genuinely different toolchains must rerun.
    for tool in ("node", "npm", "uv", "git", "make"):
        try:
            result[tool] = subprocess.check_output([tool, "--version"], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            result[tool] = "unavailable"
    selected = {key: value for key, value in os.environ.items() if key.startswith(("VITE_", "TAURI_", "B4F_", "PYTEST_")) or key in ("PATH", "CI", "NPM", "UV", "PROJECT_CONFIG", "FRONTEND_DIR", "BACKEND_DIR", "NODE_ENV", "GIT_EXEC_PATH")}
    # Git exports this default during hooks; absent and explicitly-default are equivalent.
    try:
        selected["GIT_EXEC_PATH"] = subprocess.check_output(["git", "--exec-path"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        selected["GIT_EXEC_PATH"] = selected.get("GIT_EXEC_PATH", "unavailable")
    selected["PATH"] = normalized_path(selected.get("PATH", ""))
    selected["PROJECT_CONFIG"] = selected.get("PROJECT_CONFIG") or "project.json"
    result["executables"] = {
        tool: str(Path(found).resolve()) if found else "unavailable"
        for tool in ("python3", "node", "npm", "uv", "git", "make")
        for found in [shutil.which(tool, path=selected["PATH"])]
    }
    result["environment"] = hashlib.sha256(json.dumps(selected, sort_keys=True).encode()).hexdigest()
    return result


def command_root(root, command):
    if command[:3] == ["make", "-C", "src/frontend"]:
        return root / "src/frontend", ["make", *command[3:]]
    return root, command


def artifacts(root, command):
    # Build-producing receipts are reusable only while their outputs still exist unchanged.
    if not any(target in command for target in ("build", "test-routes", "frontend-test-routes", "frontend-package", "frontend-package-verified")):
        return "none"
    directory = root / ("src/frontend/dist" if (root / "src/backend").is_dir() else "dist")
    if not (directory / "index.html").is_file():
        return None
    digest = hashlib.sha256()
    for file in sorted(directory.rglob("*")):
        if file.is_file():
            digest.update(str(file.relative_to(directory)).encode() + file.read_bytes())
    # Packaging mutates a second output directory, so always rerun this cheap integration step.
    if any(target.startswith("frontend-package") for target in command):
        return None
    return digest.hexdigest()


class Receipt:
    def __init__(self, root, command):
        self.root, self.command = command_root(root, command)
        self.enabled = os.environ.get("VERIFY_FULL") != "1" and not os.environ.get("CI")
        self.key = {"version": 2, "source": snapshot(self.root), "command": self.command, "context": context()}
        directory = Path(git(self.root, "rev-parse", "--absolute-git-dir").decode().strip()) / "verification-receipts"
        self.path = directory / (hashlib.sha256(json.dumps(self.command).encode()).hexdigest() + ".json")

    def miss_reason(self):
        if not self.enabled:
            return "forced/CI verification"
        try:
            value = json.loads(self.path.read_text())
            differences = [name for name in self.key if value["key"].get(name) != self.key[name]]
            if differences:
                return "changed " + ", ".join(differences)
            if not 0 <= time.time() - value["time"] < TTL_SECONDS:
                return "expired receipt"
            if value["artifacts"] is None or value["artifacts"] != artifacts(self.root, self.command):
                return "missing or changed build output"
            return "matching receipt"
        except (OSError, ValueError, KeyError, TypeError):
            return "no valid receipt"

    def reusable(self):
        if not self.enabled:
            return False
        try:
            value = json.loads(self.path.read_text())
            return (value["key"] == self.key and 0 <= time.time() - value["time"] < TTL_SECONDS
                    and value["artifacts"] is not None and value["artifacts"] == artifacts(self.root, self.command))
        except (OSError, ValueError, KeyError, TypeError):
            return False

    def invalidate(self):
        self.path.unlink(missing_ok=True)

    def save(self):
        if not self.enabled or snapshot(self.root) != self.key["source"]:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        value = {"key": self.key, "time": time.time(), "artifacts": artifacts(self.root, self.command)}
        temporary = self.path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(value))
        temporary.replace(self.path)
