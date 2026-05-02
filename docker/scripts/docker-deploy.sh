#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker command not found. Install Docker Desktop/Engine first." >&2
    exit 1
fi

"${SCRIPT_DIR}/docker-build.sh"
"${SCRIPT_DIR}/docker-up.sh" --force-recreate
"${SCRIPT_DIR}/docker-export.sh"
