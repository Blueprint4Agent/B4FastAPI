#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${DOCKER_DIR}/.env"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-120}"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker command not found. Install Docker Desktop/Engine first." >&2
    exit 1
fi

[ -f "${ENV_FILE}" ] || cp "${DOCKER_DIR}/.env.example" "${ENV_FILE}"

# Read only the resolved app environment; never print the full Compose model.
cd "${DOCKER_DIR}"
ROOT_DIR="$(cd "${DOCKER_DIR}/.." && pwd)"
if ! command -v "${UV:-uv}" >/dev/null 2>&1; then
    echo "uv command not found. Install uv to read the resolved Compose settings." >&2
    exit 1
fi
if [[ ! "${HEALTH_TIMEOUT_SECONDS}" =~ ^[1-9][0-9]*$ ]]; then
    echo "HEALTH_TIMEOUT_SECONDS must be a positive integer." >&2
    exit 1
fi

infra_names="$(docker compose --env-file .env config --format json app |
    "${UV:-uv}" run --project "${ROOT_DIR}/src/backend" python -c '
import json
import sys
settings = json.load(sys.stdin)["services"]["app"].get("environment", {})
if settings.get("DB_DRIVER", "").startswith("postgresql") and settings.get("DB_HOST") == "postgres":
    print("postgres")
if str(settings.get("REDIS_IN_MEMORY", "true")).lower() == "false" and settings.get("REDIS_HOST") == "redis":
    print("redis")
')"

infra_services=()
while IFS= read -r service; do
    [ -z "${service}" ] || infra_services+=("${service}")
done <<< "${infra_names}"

if [ "${#infra_services[@]}" -gt 0 ]; then
    # Existing infrastructure is preserved, including its current configuration.
    docker compose --env-file .env up -d --no-deps --no-recreate \
        --wait --wait-timeout "${HEALTH_TIMEOUT_SECONDS}" "${infra_services[@]}"
fi

# Caller flags (including deploy's --force-recreate) apply to the app only.
docker compose --env-file .env up -d --no-deps "$@" \
    --wait --wait-timeout "${HEALTH_TIMEOUT_SECONDS}" app
