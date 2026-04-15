#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Create .env files if missing..."
[ -f src/backend/.env ] || cp src/backend/.env.example src/backend/.env
[ -f src/frontend/.env ] || cp src/frontend/.env.example src/frontend/.env
[ -f docker/.env ] || cp docker/.env.example docker/.env

echo "[2/4] Optional docker services (Postgres + Redis)"
echo "  - run: (cd docker && docker compose --env-file .env up -d)"

echo "[3/4] Backend install"
echo "  - run: (cd src/backend && pip install -e .)"

echo "[4/4] Frontend install"
echo "  - run: (cd src/frontend && npm install)"

echo "Bootstrap complete."

