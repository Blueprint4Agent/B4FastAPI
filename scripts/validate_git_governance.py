#!/usr/bin/env python3
"""Validate staged snapshots or the authored commits and metadata of a PR."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

TYPES = "feat|fix|docs|test|refactor|chore|ci|build|perf|style|revert|hotfix"
TITLE = re.compile(rf"({TYPES})(\([a-z0-9-]+\))?!?: [a-z0-9].{{0,71}}")
BRANCH = re.compile(rf"({TYPES})/[a-z0-9]+(?:-[a-z0-9]+)*")
WORKLOG = re.compile(r"worklog/[0-9]{4}-[a-z0-9]+(?:-[a-z0-9]+)*\.md")
WORKLOG_SECTIONS = (
    "Commit Title",
    "Changed File Scope",
    "Reason",
    "Design",
    "Verification Plan",
    "Impact",
    "Loop Alignment",
    "Verification",
)
PR_SECTIONS = (
    ("Summary", "요약"),
    ("Scope", "범위"),
    ("Reason", "이유"),
    ("Verification", "검증"),
    ("Documentation", "문서"),
    ("Risk / Impact", "위험 / 영향"),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()


def section(text, heading, level):
    pattern = rf"^{re.escape('#' * level)} {re.escape(heading)}\s*\n(.*?)(?=^#{{1,{level}}} |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def substantive(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()
    return bool(text) and text.casefold() not in {"todo", "tbd", "pending", "-", "..."}


def check_message(message, source):
    title = message.splitlines()[0] if message else ""
    require(TITLE.fullmatch(title), f"{source}: invalid Conventional Commit title")
    body = message.partition("\n")[2]
    for heading in ("Changes", "Affected Files", "Verification"):
        match = re.search(
            rf"^{heading}:\s*\n(.*?)(?=^[A-Z][A-Za-z ]+:|\Z)", body, re.M | re.S
        )
        require(
            match and substantive(match.group(1)),
            f"{source}: missing/empty {heading} body section",
        )
    return title


def check_worklogs(paths, read_file, title, source):
    logs = [path for path in paths if WORKLOG.fullmatch(path)]
    require(
        logs,
        f"{source}: add or modify a worklog in this snapshot (untracked files do not count)",
    )
    matched = False
    for path in logs:
        content = read_file(path)
        for heading in WORKLOG_SECTIONS:
            require(
                substantive(section(content, heading, 1)),
                f"{source}: {path} missing/empty {heading}",
            )
        if section(content, "Commit Title", 1) == title:
            matched = True
    require(
        matched, f"{source}: no worklog Commit Title matches the actual commit title"
    )


def check_pr(title, body):
    require(
        re.fullmatch(rf"\[({TYPES})\] [A-Za-z0-9].{{0,99}}", title), "invalid PR title"
    )
    for english, korean in PR_SECTIONS:
        require(
            any(
                substantive(section(body, heading, 2)) for heading in (english, korean)
            ),
            f"PR missing/empty {english} section",
        )


def check_commit(sha):
    title = check_message(git("show", "-s", "--format=%B", sha), sha[:12])
    paths = git(
        "diff-tree",
        "--root",
        "--no-commit-id",
        "--no-renames",
        "--name-only",
        "--diff-filter=AM",
        "-r",
        sha,
    ).splitlines()
    check_worklogs(paths, lambda path: git("show", f"{sha}:{path}"), title, sha[:12])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit-title", default=os.getenv("COMMIT_TITLE", ""))
    parser.add_argument("--commit-body-file", default=os.getenv("COMMIT_BODY_FILE", ""))
    parser.add_argument("--pr-title", default=os.getenv("PR_TITLE", ""))
    parser.add_argument("--pr-body-file", default=os.getenv("PR_BODY_FILE", ""))
    parser.add_argument("--merge-method", default=os.getenv("MERGE_METHOD", "merge"))
    parser.add_argument(
        "--allow-non-merge-method",
        action="store_true",
        default=os.getenv("ALLOW_NON_MERGE_METHOD") == "true",
    )
    parser.add_argument(
        "--event-file",
        help="GitHub pull_request event JSON; validates its complete commit range",
    )
    args = parser.parse_args()
    require(
        args.merge_method == "merge"
        or (args.allow_non_merge_method and args.merge_method in {"squash", "rebase"}),
        "merge method must be merge unless explicitly overridden",
    )

    if args.event_file:
        event = json.loads(Path(args.event_file).read_text())
        pr = event["pull_request"]
        require(BRANCH.fullmatch(pr["head"]["ref"]), "invalid PR branch name")
        check_pr(pr["title"], pr.get("body") or "")
        base, head = pr["base"]["sha"], pr["head"]["sha"]
        require(
            re.fullmatch(r"[0-9a-f]{40}", base) and re.fullmatch(r"[0-9a-f]{40}", head),
            "invalid PR SHA",
        )
        require(git("rev-parse", "HEAD") == head, "checkout must match the PR head SHA")
        commits = git(
            "rev-list", "--reverse", "--no-merges", f"{base}..{head}"
        ).splitlines()
        require(commits, "PR has no authored commits")
        for sha in commits:
            check_commit(sha)
        print(f"git governance check passed ({len(commits)} PR commits)")
        return

    require(
        BRANCH.fullmatch(git("branch", "--show-current")),
        "use a named <type>/<kebab-description> branch",
    )
    if args.commit_title:
        require(args.commit_body_file, "planned commits require COMMIT_BODY_FILE")
        body = Path(args.commit_body_file).read_text()
        # Accept a complete git commit -F file or a body-only file.
        message = (
            body
            if body.splitlines() and body.splitlines()[0] == args.commit_title
            else args.commit_title + "\n\n" + body
        )
        title = check_message(message, "staged commit")
        paths = git(
            "diff", "--cached", "--no-renames", "--name-only", "--diff-filter=AM"
        ).splitlines()
        check_worklogs(
            paths, lambda path: git("show", f":{path}"), title, "staged commit"
        )
    else:
        check_commit(git("rev-parse", "HEAD"))
    if args.pr_title or args.pr_body_file:
        require(
            args.pr_title and args.pr_body_file,
            "provide both PR_TITLE and PR_BODY_FILE",
        )
        check_pr(args.pr_title, Path(args.pr_body_file).read_text())
    print("git governance check passed")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f"git governance check failed: {error}", file=sys.stderr)
        sys.exit(1)
