#!/usr/bin/env bash
set -euo pipefail

ALLOWED_TYPES="feat|fix|docs|test|refactor|chore|ci|build|perf|style|revert|hotfix"
COMMIT_TITLE="${COMMIT_TITLE:-}"
COMMIT_BODY_FILE="${COMMIT_BODY_FILE:-}"
PR_TITLE="${PR_TITLE:-}"
PR_BODY_FILE="${PR_BODY_FILE:-}"
MERGE_METHOD="${MERGE_METHOD:-merge}"
ALLOW_NON_MERGE_METHOD="${ALLOW_NON_MERGE_METHOD:-false}"

usage() {
    cat <<'EOF'
Usage: scripts/validate-git-governance.sh [options]

Options:
  --commit-title TITLE   Validate a planned commit title instead of HEAD.
  --commit-body-file FILE
                         Validate required commit body sections.
  --pr-title TITLE       Validate a planned PR title.
  --pr-body-file FILE    Validate required PR description sections.
  --merge-method METHOD  Validate the planned merge method (default: merge).
  --allow-non-merge-method
                         Allow squash or rebase only for an explicit user request.

Environment aliases:
  COMMIT_TITLE, COMMIT_BODY_FILE, PR_TITLE, PR_BODY_FILE,
  MERGE_METHOD, ALLOW_NON_MERGE_METHOD
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --commit-title)
            COMMIT_TITLE="${2:-}"
            shift 2
            ;;
        --commit-body-file)
            COMMIT_BODY_FILE="${2:-}"
            shift 2
            ;;
        --pr-title)
            PR_TITLE="${2:-}"
            shift 2
            ;;
        --pr-body-file)
            PR_BODY_FILE="${2:-}"
            shift 2
            ;;
        --merge-method)
            MERGE_METHOD="${2:-}"
            shift 2
            ;;
        --allow-non-merge-method)
            ALLOW_NON_MERGE_METHOD="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

fail() {
    echo "git governance check failed: $1" >&2
    exit 1
}

case "$MERGE_METHOD" in
    merge)
        ;;
    squash|rebase)
        if [ "$ALLOW_NON_MERGE_METHOD" != "true" ]; then
            fail "merge method must be 'merge'; '$MERGE_METHOD' requires an explicit user request and ALLOW_NON_MERGE_METHOD=true"
        fi
        ;;
    *)
        fail "merge method must be one of: merge, squash, rebase"
        ;;
esac

current_branch="$(git branch --show-current)"
if [ -z "$current_branch" ]; then
    fail "could not determine current branch"
fi

if [[ ! "$current_branch" =~ ^($ALLOWED_TYPES)/[a-z0-9][a-z0-9-]*$ ]]; then
    fail "branch must match <type>/<short-kebab-title>; got '$current_branch'"
fi

if [ -z "$COMMIT_TITLE" ]; then
    COMMIT_TITLE="$(git log -1 --pretty=%s 2>/dev/null || true)"
fi

if [ -z "$COMMIT_TITLE" ]; then
    fail "commit title is empty"
fi

if [[ ! "$COMMIT_TITLE" =~ ^($ALLOWED_TYPES)(\([a-z0-9-]+\))?!?:[[:space:]][a-z0-9].{0,71}$ ]]; then
    fail "commit title must match Conventional Commits, e.g. 'feat(frontend): add pagination'"
fi

if [ -n "$COMMIT_BODY_FILE" ]; then
    [ -f "$COMMIT_BODY_FILE" ] || fail "commit body file not found: $COMMIT_BODY_FILE"
    for section in "Changes" "Affected Files" "Verification"; do
        grep -Fq "$section:" "$COMMIT_BODY_FILE" ||
            fail "commit body must include '$section:'"
    done
fi

changed_files="$(
    {
        git diff --name-only HEAD -- 2>/dev/null || true
        git ls-files --others --exclude-standard 2>/dev/null || true
    } | sort -u
)"
if [ -z "$changed_files" ]; then
    changed_files="$(git show --name-only --format= HEAD 2>/dev/null || true)"
fi

worklog_files="$(printf '%s\n' "$changed_files" | grep -E '^worklog/[0-9]{4}-[a-z0-9-]+\.md$' || true)"
if [ -z "$worklog_files" ]; then
    fail "expected a matching worklog/<number>-<short-kebab-title>.md file"
fi

for file in $worklog_files; do
    [ -f "$file" ] || continue
    grep -Eiq '^# (commit title|Commit Title)' "$file" ||
        fail "$file must include a commit title section"
    grep -Eiq '^# (changed file scope|Changed File Scope)' "$file" ||
        fail "$file must include a changed file scope section"
    grep -Eiq '^# (reason|Reason)' "$file" ||
        fail "$file must include a reason section"
    grep -Eiq '^# (impact|Impact)' "$file" ||
        fail "$file must include an impact section"
done

if [ -n "$PR_TITLE" ]; then
    if [[ ! "$PR_TITLE" =~ ^\[($ALLOWED_TYPES)\][[:space:]][A-Z0-9a-z].{0,99}$ ]]; then
        fail "PR title must match '[type] concise title', e.g. '[feat] Add API key pagination'"
    fi
fi

if [ -n "$PR_BODY_FILE" ]; then
    [ -f "$PR_BODY_FILE" ] || fail "PR body file not found: $PR_BODY_FILE"
    for section_pair in \
        "Summary|요약" \
        "Scope|범위" \
        "Reason|이유" \
        "Verification|검증" \
        "Documentation|문서" \
        "Risk / Impact|위험 / 영향"; do
        english_section="${section_pair%%|*}"
        korean_section="${section_pair##*|}"
        grep -Eq "^## (${english_section}|${korean_section})$" "$PR_BODY_FILE" ||
            fail "PR body must include '## $english_section' or '## $korean_section'"
    done
fi

echo "git governance check passed"
