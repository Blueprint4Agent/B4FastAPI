#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Create .env files if missing..."
[ -f backend/.env ] || cp backend/.env.example backend/.env
[ -f frontend/.env ] || cp frontend/.env.example frontend/.env
[ -f docker/.env ] || cp docker/.env.example docker/.env

echo "[2/4] Optional docker services (Postgres + Redis)"
echo "  - run: (cd docker && docker compose --env-file .env up -d)"

echo "[3/4] Backend install"
echo "  - run: (cd backend && pip install -e .)"

echo "[4/4] Frontend install"
echo "  - run: (cd frontend && npm install)"

echo "Bootstrap complete."

