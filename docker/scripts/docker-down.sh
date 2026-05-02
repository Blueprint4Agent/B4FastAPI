#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker command not found. Install Docker Desktop/Engine first." >&2
    exit 1
fi

cd "${DOCKER_DIR}"
docker compose --env-file .env down --remove-orphans "$@"
