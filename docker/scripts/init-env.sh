#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${DOCKER_DIR}/.." && pwd)"

echo "[1/3] initialize env files"
[ -f "${ROOT_DIR}/src/backend/.env" ] || cp "${ROOT_DIR}/src/backend/.env.example" "${ROOT_DIR}/src/backend/.env"
[ -f "${ROOT_DIR}/src/frontend/.env" ] || cp "${ROOT_DIR}/src/frontend/.env.example" "${ROOT_DIR}/src/frontend/.env"
[ -f "${DOCKER_DIR}/.env" ] || cp "${DOCKER_DIR}/.env.example" "${DOCKER_DIR}/.env"

echo "[2/3] ready backend/frontend/docker env templates"
echo "  - backend: src/backend/.env"
echo "  - frontend: src/frontend/.env"
echo "  - docker: docker/.env"

echo "[3/3] done"
