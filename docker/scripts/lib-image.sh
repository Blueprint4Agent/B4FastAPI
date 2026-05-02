#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${DOCKER_DIR}/.." && pwd)"

ensure_docker_command() {
    if ! command -v docker >/dev/null 2>&1; then
        echo "docker command not found. Install Docker Desktop/Engine first." >&2
        exit 1
    fi
}

ensure_docker_env_file() {
    [ -f "${DOCKER_DIR}/.env" ] || cp "${DOCKER_DIR}/.env.example" "${DOCKER_DIR}/.env"
}

load_docker_env() {
    set -a
    # shellcheck disable=SC1091
    source "${DOCKER_DIR}/.env"
    set +a
}

resolve_project_version_from_file() {
    local version_file="${APP_VERSION_FILE:-src/backend/pyproject.toml}"
    local full_path="${ROOT_DIR}/${version_file}"

    if [ -f "${full_path}" ]; then
        awk '
            $0 ~ /^\[project\]/ { in_project = 1; next }
            in_project && $0 ~ /^\[/ { in_project = 0 }
            in_project && $0 ~ /^version[[:space:]]*=/ {
                gsub(/"/, "", $3)
                print $3
                exit
            }
        ' "${full_path}"
    fi
}

resolve_version() {
    local configured="${APP_VERSION:-auto}"

    if [ "${configured}" != "auto" ] && [ -n "${configured}" ]; then
        echo "${configured}"
        return 0
    fi

    local file_version
    file_version="$(resolve_project_version_from_file || true)"
    if [ -n "${file_version}" ]; then
        echo "${file_version}"
        return 0
    fi

    if command -v git >/dev/null 2>&1 && git -C "${ROOT_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        local short_sha
        short_sha="$(git -C "${ROOT_DIR}" rev-parse --short HEAD 2>/dev/null || true)"
        if [ -n "${short_sha}" ]; then
            echo "git-${short_sha}"
            return 0
        fi
    fi

    echo "local"
}

resolve_app_image() {
    local explicit_image="${APP_IMAGE:-}"
    if [ -n "${explicit_image}" ]; then
        echo "${explicit_image}"
        return 0
    fi

    local image_repo="${APP_IMAGE_REPO:-blueprint4fastapi}"
    local image_version
    image_version="$(resolve_version)"
    echo "${image_repo}:${image_version}"
}
