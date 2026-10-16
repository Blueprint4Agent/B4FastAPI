"""Conservative change-scoped verification. No dependencies or network required."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from verification_scope import css_impact, frontend_impact
from verification_areas import FRONTEND_AREAS, PARENT_AREAS, owned_areas
from verification_runner import execute

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
    if path.endswith(".md"):
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
        "areas": [],
        "ownership": {},
        "reason": "Changed-file ownership",
    }
    areas, levels, app_files = set(), [], []
    try:
        paths = changed(root, base, head)
        result["files"] = paths
        for path in paths:
            if parent and path == "src/frontend":
                old = git(root, "rev-parse", f"{base}:src/frontend").decode().strip()
                new = (
                    git(root, "rev-parse", f"{head}:src/frontend").decode().strip()
                    if head
                    else None
                )
                child = plan(root / path, old, new)
                result["child"] = child
                areas.update(child["areas"])
                levels.append(child["frontend"])
                result["ownership"][path] = child["areas"]
                continue
            owner = owned_areas(path, parent)
            if owner is None:
                owner = PARENT_AREAS if parent else FRONTEND_AREAS
                result["reason"] += f"; shared/unknown path: {path}"
            if not parent and path == "src/styles/app.css":
                try:
                    css_domains = css_impact(
                        content(root, base, path), content(root, head, path)
                    )
                except (OSError, ValueError, subprocess.CalledProcessError):
                    css_domains = None
                if css_domains is None:
                    owner = owner | {"style-studio", "discovery"}
            if (
                not parent
                and re.fullmatch(r"src/locales/[\w.-]+\.json", path)
                and classify(root, base, head, path, False) != "copy"
            ):
                if path.startswith("src/locales/styleStudio."):
                    owner = owner | {"style-studio"}
                if path in {"src/locales/en.json", "src/locales/ko.json"}:
                    try:
                        before = parse_json(content(root, base, path))
                        after = parse_json(content(root, head, path))

                        def relevant(value):
                            return (
                                value.get("discovery"),
                                value.get("home", {}).get("project"),
                            )

                        discovery_changed = relevant(before) != relevant(after)
                    except (
                        OSError,
                        ValueError,
                        AttributeError,
                        subprocess.CalledProcessError,
                    ):
                        discovery_changed = True
                    if discovery_changed:
                        owner = owner | {"discovery"}
            result["ownership"][path] = sorted(owner)
            areas.update(owner)
            if "frontend-app" in owner:
                levels.append(
                    "full" if parent else classify(root, base, head, path, False)
                )
                app_files.append(path)
            elif path.endswith(".md"):
                levels.append("docs")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        force_full = True
        result["reason"] = f"Cannot establish scope ({type(error).__name__})"
    if force_full:
        areas = set(PARENT_AREAS if parent else FRONTEND_AREAS)
        levels = ["full"]
        result["reason"] = "Full verification requested or scope unavailable"
    result["areas"] = sorted(areas)
    result["forced"] = force_full
    result["backend"] = parent and bool(areas & {"backend", "deployment"})
    result["frontend"] = max(levels, key=LEVELS.get, default="none")
    if "frontend-app" in areas and result["frontend"] in ("behavior", "ui"):
        if parent and "child" in result and not app_files:
            result["impact"] = result["child"].get("impact")
        elif not parent:
            result["impact"] = frontend_impact(root, base, head, app_files, content)
        result["reason"] += "; " + (
            "affected suites selected"
            if result.get("impact")
            else "shared/unknown app impact; broad app suites retained"
        )
    app_runtime = (
        "frontend-app" in areas and LEVELS[result["frontend"]] >= LEVELS["behavior"]
    )
    result["node"] = (
        app_runtime
        or bool(areas & {"contracts", "branding", "style-studio"})
        or ("discovery" in areas)
    )
    result["browser"] = (
        (app_runtime and LEVELS[result["frontend"]] >= LEVELS["ui"])
        or bool(areas & {"contracts", "style-studio", "branding"})
        or ("discovery" in areas)
    )
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
    # Legacy callers can still supply a frontend depth; plans always include areas.
    areas = set(scope.get("areas", PARENT_AREAS if parent else FRONTEND_AREAS))
    if LEVELS[scope["frontend"]] < LEVELS["behavior"]:
        areas.discard("frontend-app")
    commands = []
    prefix = ["make", "-C", "src/frontend"] if parent else ["make"]
    if areas & {"governance", "harness"}:
        commands.append(["make", "verification-harness-test"])
        if parent and (
            ("frontend-app" in areas and "harness" in areas)
            or set(scope.get("child", {}).get("areas", [])) & {"harness", "governance"}
        ):
            commands.append(prefix + ["verification-harness-test"])
    if parent and domain in ("all", "backend"):
        if "backend" in areas and scope["backend"]:
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
        elif "deployment" in areas:
            commands.append(["make", "deployment-check"])
        if "contracts" in areas and "backend" not in areas:
            commands.append(["make", "contract-check"])
        if "publication" in areas:
            commands.append(["make", "discovery-check"])
    if domain == "backend":
        return commands
    if parent and areas & {"frontend-app", "branding"}:
        commands.append(["make", "project-brand"])
    if "frontend-app" in areas:
        level, impact = scope["frontend"], scope.get("impact")
        if impact and impact.get("checks"):
            commands.append(
                prefix + ["check-affected", "CHECK_FILES=" + " ".join(impact["checks"])]
            )
        else:
            commands.append(prefix + ["check-app"])
        if impact:
            if impact["unit"]:
                commands.append(
                    prefix + ["test-selected", "TEST_FILES=" + " ".join(impact["unit"])]
                )
            if impact["browser"]:
                commands.append(
                    prefix
                    + ["test-ui-selected", "TEST_FILES=" + " ".join(impact["browser"])]
                )
        else:
            commands.append(prefix + ["test"])
            if level in ("ui", "full"):
                commands.append(prefix + ["test-ui"])
        if level == "full":
            commands.append(prefix + ["test-production"])
        else:
            commands.append(prefix + ["build"])
    elif "contracts" in areas:
        commands.append(prefix + ["api-check", "check-app", "test", "test-production"])
    if "frontend-app" in areas and areas & {"harness", "governance"}:
        commands.append(prefix + ["app-tooling-test"])
    if "style-studio" in areas:
        commands.append(prefix + ["test-style-studio"])
    if "discovery" in areas and not parent:
        commands.append(prefix + ["discovery-check", "test-discovery"])
    elif parent and "discovery" in areas:
        commands.append(prefix + ["discovery-check", "test-discovery"])
    if "branding" in areas:
        commands.append(prefix + ["project-config-check"])
        if "frontend-app" not in areas:
            commands.append(prefix + ["test-production"])
        if parent:
            commands.append(
                [
                    "make",
                    "project-init-check",
                    "project-init-test",
                    "project-build-test",
                ]
            )
    if parent and areas & {"frontend-app", "contracts", "branding"}:
        commands.append(
            ["make", "frontend-contract-check", "frontend-package-verified"]
        )
    return commands


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "run", "light"))
    parser.add_argument("--base", default=(os.environ.get("VERIFY_BASE") or "HEAD"))
    parser.add_argument("--head", default=os.environ.get("VERIFY_HEAD") or None)
    parser.add_argument(
        "--full",
        action="store_true",
        default=os.environ.get("VERIFY_FULL") == "1" or bool(os.environ.get("CI")),
    )
    parser.add_argument(
        "--domain", choices=("all", "backend", "frontend"), default="all"
    )
    parser.add_argument("--github-output")
    parser.add_argument(
        "--json", action="store_true", help="Print full machine-readable plan"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=int(os.environ.get("VERIFY_JOBS") or "2"),
        help="Maximum concurrent command lanes (default: 2; 1 is sequential)",
    )
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    root = Path(__file__).resolve().parent.parent
    scope = plan(root, args.base, args.head, args.full)
    commands = targets(scope, (root / "src/backend").is_dir(), args.domain)
    if args.json:
        print(
            json.dumps(
                {**scope, "commands": commands, "jobs": args.jobs},
                ensure_ascii=False,
                indent=2,
            ),
            flush=True,
        )
    else:
        print(
            f"Verification: backend={scope['backend']}, frontend={scope['frontend']}, areas={','.join(scope['areas']) or 'text'}, jobs={args.jobs}, changed files={len(scope['files'])}. {scope['reason']}",
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
            execute(root, commands, jobs=args.jobs, forced=scope["forced"])


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        sys.exit(1)
