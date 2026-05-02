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

read_env() {
    local key="$1"
    awk -F= -v key="${key}" '$1==key {print substr($0, index($0, "=") + 1); exit}' "${ENV_FILE}" | sed 's/^"//; s/"$//'
}

to_lower() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

db_driver="$(read_env DB_DRIVER)"
db_host="$(read_env DB_HOST)"
redis_in_memory="$(to_lower "$(read_env REDIS_IN_MEMORY)")"
redis_host="$(read_env REDIS_HOST)"

use_local_postgres=false
if [[ "${db_driver}" == postgresql* ]] && [ "${db_host}" = "postgres" ]; then
    use_local_postgres=true
fi

use_local_redis=false
if [ "${redis_in_memory}" = "false" ] && [ "${redis_host}" = "redis" ]; then
    use_local_redis=true
fi

wait_for_container_health() {
    local container_name="$1"
    local deadline=$((SECONDS + HEALTH_TIMEOUT_SECONDS))

    while [ "${SECONDS}" -lt "${deadline}" ]; do
        local status
        status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{if .State.Running}}running{{else}}stopped{{end}}{{end}}' "${container_name}" 2>/dev/null || true)"

        if [ "${status}" = "healthy" ] || [ "${status}" = "running" ]; then
            echo "[health] ${container_name}: ${status}"
            return 0
        fi

        sleep 2
    done

    echo "[health] timeout waiting for ${container_name}" >&2
    docker logs "${container_name}" --tail 80 >&2 || true
    return 1
}

cd "${DOCKER_DIR}"

infra_services=()
[ "${use_local_postgres}" = true ] && infra_services+=("postgres")
[ "${use_local_redis}" = true ] && infra_services+=("redis")

if [ "${#infra_services[@]}" -gt 0 ]; then
    docker compose --env-file .env up -d "$@" "${infra_services[@]}"

    [ "${use_local_postgres}" = true ] && wait_for_container_health "b4fastapi-postgres"
    [ "${use_local_redis}" = true ] && wait_for_container_health "b4fastapi-redis"
fi

docker compose --env-file .env up -d "$@" app
