"""Conservative change-scoped verification. No dependencies or network required."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from verification_cache import Receipt

LEVELS = {"none": 0, "docs": 1, "copy": 2, "behavior": 3, "ui": 4, "full": 5}


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.PIPE
    )


def content(root, ref, path):
    if ref:
        return git(root, "show", f"{ref}:{path}").decode()
    file = root / path
    if file.is_symlink():
        raise ValueError("symlink requires full verification")
    return file.read_text()


def locale_shape(value):
    if isinstance(value, dict):
        return {key: locale_shape(item) for key, item in value.items()}
    if isinstance(value, str):
        # Placeholders, nesting references and markup are part of the copy contract.
        return sorted(re.findall(r"{{.*?}}|\$t\(.*?\)|<[^>]+>", value))
    raise ValueError("only object/string locale values qualify as copy")


def parse_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(text, object_pairs_hook=unique)


def classify(root, base, head, path, parent):
    if path == "AGENTS.md" or path.endswith("/AGENTS.md"):
        return "full"
    if path.endswith(".md") and (
        "/" not in path
        or path.startswith(("notes/", "worklog/"))
        or path in ("src/backend/BACKEND.md", "src/backend/TEST.md")
    ):
        return "docs"
    if not parent and re.fullmatch(r"src/locales/[\w.-]+\.json", path):
        try:
            before = locale_shape(parse_json(content(root, base, path)))
            after = locale_shape(parse_json(content(root, head, path)))
            if before == after:
                return "copy"
        except (ValueError, OSError, subprocess.CalledProcessError):
            pass
        return "full"
    if parent:
        if path.startswith(("src/backend/app/", "src/backend/tests/")):
            return "behavior"
        return "full"
    if path.startswith(
        ("src/api/", "src/store/", "src/hooks/connectivity/", "src/hooks/realtime/")
    ) or any(
        key in path.lower()
        for key in (
            "auth",
            "login",
            "apikey",
            "config",
            "src/app.",
            "src/main.",
            "src/i18n.",
        )
    ):
        return "full"
    if path.startswith(
        ("src/components/", "src/pages/", "src/styles/", "public/", "tests/e2e/")
    ):
        return "ui"
    if path.startswith(("src/hooks/", "src/utils/", "src/tests/")) and path.endswith(
        (".ts", ".tsx")
    ):
        return "behavior"
    return "full"


def changed(root, base, head):
    args = [
        "diff",
        "--name-only",
        "--no-renames",
        "--ignore-submodules=none",
        "-z",
        base,
    ]
    if head:
        args.append(head)
    args.append("--")
    paths = git(root, *args).decode().split("\0")
    if not head:
        paths += (
            git(root, "ls-files", "--others", "--exclude-standard", "-z")
            .decode()
            .split("\0")
        )
    return sorted(set(filter(None, paths)))


def plan(root, base="HEAD", head=None, force_full=False):
    parent = (root / "src/backend").is_dir()
    result = {
        "backend": False,
        "frontend": "none",
        "files": [],
        "reason": "Changed-file classification",
    }
    try:
        paths = changed(root, base, head)
        result["files"] = paths
        levels = []
        for path in paths:
            if parent and path == "src/frontend":
                # Inspect the pinned child's commits, including dirty child files locally.
                old = git(root, "rev-parse", f"{base}:src/frontend").decode().strip()
                new = (
                    git(root, "rev-parse", f"{head}:src/frontend").decode().strip()
                    if head
                    else None
                )
                child = plan(root / path, old, new)
                levels.append(child["frontend"])
                result["child"] = child
                continue
            level = classify(root, base, head, path, parent)
            if parent and level == "behavior":
                result["backend"] = True
            else:
                levels.append(level)
                if parent and level == "full":
                    result["backend"] = True
        result["frontend"] = max(levels, key=LEVELS.get, default="none")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        force_full = True
        result["reason"] = (
            f"Cannot establish scope ({type(error).__name__}); full verification"
        )
    if force_full:
        result["backend"] = parent
        result["frontend"] = "full"
        result["reason"] = "Full verification requested or scope unavailable"
    result["node"] = LEVELS[result["frontend"]] >= LEVELS["behavior"]
    result["browser"] = LEVELS[result["frontend"]] >= LEVELS["ui"]
    return result


def lightweight(root, base, head):
    # Run even when runtime jobs are skipped. Git diff validates added whitespace.
    args = ["diff", "--check", base]
    if head:
        args.append(head)
    subprocess.run(["git", "-C", str(root), *args, "--"], check=True)
    for path in changed(root, base, head):
        if path.endswith((".md", ".json")):
            try:
                text = content(root, head, path)
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue  # Deleted files are classified conservatively above.
            if "\x00" in text or any(
                line.rstrip() != line for line in text.splitlines()
            ):
                raise ValueError(f"Invalid text/whitespace: {path}")
            if path.endswith(".json"):
                parse_json(text)
    print("Lightweight text/JSON validation passed.")


def targets(scope, parent, domain):
    commands = [["make", "hooks-test"]] if scope["frontend"] == "full" else []
    if parent and domain in ("all", "backend") and scope["backend"]:
        commands.append(
            [
                "make",
                "project-init-check",
                "project-init-test",
                "backend-architecture-check",
                "env-contract-check",
                "backend-check",
                "backend-test",
                "contract-check",
            ]
        )
    level = scope["frontend"]
    if domain == "backend" or LEVELS[level] < LEVELS["behavior"]:
        return commands
    prefix = ["make", "-C", "src/frontend"] if parent else ["make"]
    commands.append(prefix + ["check", "test"])
    if level in ("ui", "full"):
        commands.append(prefix + ["test-ui"])
    if level == "full":
        commands.append(
            (["make", "frontend-test-routes"] if parent else prefix + ["test-routes"])
        )
        commands.append(prefix + ["test-style-studio"])
    if parent:
        commands.append(
            [
                "make",
                "frontend-contract-check",
                "frontend-package-verified" if level == "full" else "frontend-package",
            ]
        )
        if level == "full":
            commands.append(["make", "project-build-test"])
    elif level != "full":
        commands.append(prefix + ["build"])
    return commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "run", "light"))
    parser.add_argument("--base", default=(os.environ.get("VERIFY_BASE") or "HEAD"))
    parser.add_argument("--head", default=os.environ.get("VERIFY_HEAD") or None)
    parser.add_argument(
        "--full", action="store_true", default=os.environ.get("VERIFY_FULL") == "1"
    )
    parser.add_argument(
        "--domain", choices=("all", "backend", "frontend"), default="all"
    )
    parser.add_argument("--github-output")
    parser.add_argument(
        "--json", action="store_true", help="Print full machine-readable plan"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    scope = plan(root, args.base, args.head, args.full)
    commands = targets(scope, (root / "src/backend").is_dir(), args.domain)
    if args.json:
        print(
            json.dumps({**scope, "commands": commands}, ensure_ascii=False, indent=2),
            flush=True,
        )
    else:
        print(
            f"Verification: backend={scope['backend']}, frontend={scope['frontend']}, changed files={len(scope['files'])}. {scope['reason']}",
            flush=True,
        )
        if args.action == "plan":
            for command in commands:
                print("  " + " ".join(command))
            if not commands:
                print(
                    "  Text/JSON only; dependency install, runtime tests, build and browser checks omitted."
                )
    if args.github_output:
        with open(args.github_output, "a") as output:
            for key in ("backend", "node", "browser"):
                output.write(f"{key}={str(scope[key]).lower()}\n")
            output.write(f"frontend={scope['frontend']}\n")
    if args.action != "plan":
        lightweight(root, args.base, args.head)
        if "child" in scope and scope["child"]["frontend"] in ("none", "docs", "copy"):
            old = git(root, "rev-parse", f"{args.base}:src/frontend").decode().strip()
            new = (
                git(root, "rev-parse", f"{args.head}:src/frontend").decode().strip()
                if args.head
                else None
            )
            lightweight(root / "src/frontend", old, new)
        if args.action == "run":
            for command in commands:
                receipt = Receipt(root, command)
                if not args.full and receipt.reusable():
                    print("Reused matching local verification: " + " ".join(command), flush=True)
                    continue
                receipt.invalidate()
                print("Running: " + " ".join(command), flush=True)
                logs = (
                    Path(git(root, "rev-parse", "--absolute-git-dir").decode().strip())
                    / "verification-logs"
                )
                logs.mkdir(exist_ok=True)
                log = logs / (str(commands.index(command)) + ".log")
                started = time.monotonic()
                with log.open("w") as output:
                    completed = subprocess.run(
                        command, cwd=root, stdout=output, stderr=subprocess.STDOUT
                    )
                if completed.returncode:
                    print(
                        "\n".join(log.read_text(errors="replace").splitlines()[-80:]),
                        file=sys.stderr,
                    )
                    raise subprocess.CalledProcessError(completed.returncode, command)
                receipt.save()
                print(
                    f"Passed ({time.monotonic() - started:.1f}s). Log: {log}",
                    flush=True,
                )


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        sys.exit(1)
