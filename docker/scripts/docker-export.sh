#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ARTIFACTS_DIR="${DOCKER_DIR}/artifacts"

if ! command -v docker >/dev/null 2>&1; then
    echo "docker command not found. Install Docker Desktop/Engine first." >&2
    exit 1
fi

[ -f "${DOCKER_DIR}/.env" ] || cp "${DOCKER_DIR}/.env.example" "${DOCKER_DIR}/.env"

APP_IMAGE="$(awk -F= '/^APP_IMAGE=/{print substr($0, index($0, "=")+1); exit}' "${DOCKER_DIR}/.env")"
APP_IMAGE="${APP_IMAGE%\"}"
APP_IMAGE="${APP_IMAGE#\"}"
APP_IMAGE="${APP_IMAGE:-blueprint4fastapi:local}"
mkdir -p "${ARTIFACTS_DIR}"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
SAFE_IMAGE_NAME="${APP_IMAGE//\//_}"
SAFE_IMAGE_NAME="${SAFE_IMAGE_NAME//:/_}"
OUTPUT_PATH="${ARTIFACTS_DIR}/${SAFE_IMAGE_NAME}-${TIMESTAMP}.tar"

echo "Exporting ${APP_IMAGE} -> ${OUTPUT_PATH}"
docker save -o "${OUTPUT_PATH}" "${APP_IMAGE}"
echo "Export complete: ${OUTPUT_PATH}"
