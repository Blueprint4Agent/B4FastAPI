SHELL := /bin/bash

BACKEND_DIR ?= src/backend
FRONTEND_DIR ?= src/frontend
DOCKER_DIR ?= docker

BACKEND_HOST ?= 0.0.0.0
BACKEND_PORT ?= 8000
FRONTEND_HOST ?= 0.0.0.0
FRONTEND_PORT ?= 5173
DOCKER_SERVICE ?= app
PYTEST_ARGS ?=

UV ?= uv
NPM ?= npm
DOCKER_COMPOSE ?= docker compose

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available Make targets
	@awk 'BEGIN {FS = ":.*##"; printf "Available targets:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-28s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: init
init: ## Initialize backend, frontend, and docker env files
	bash ./docker/scripts/init-env.sh

.PHONY: install
install: backend-install frontend-install ## Install backend and frontend dependencies

.PHONY: build
build: backend-build frontend-build ## Build backend environment and frontend static artifacts

.PHONY: check
check: backend-check frontend-format-check ## Run backend lint and frontend format checks

.PHONY: git-governance-check
git-governance-check: ## Validate git governance; optionally pass COMMIT_TITLE, COMMIT_BODY_FILE, PR_TITLE, PR_BODY_FILE
	COMMIT_TITLE="$(COMMIT_TITLE)" COMMIT_BODY_FILE="$(COMMIT_BODY_FILE)" PR_TITLE="$(PR_TITLE)" PR_BODY_FILE="$(PR_BODY_FILE)" bash ./scripts/validate-git-governance.sh

.PHONY: format
format: backend-format frontend-format ## Format backend and frontend code

.PHONY: test
test: backend-test frontend-test ## Run backend and frontend tests

.PHONY: ci
ci: check test build ## Run local CI checks

.PHONY: backend-install
backend-install: ## Install backend dependencies
	cd $(BACKEND_DIR) && $(UV) sync

.PHONY: backend-build
backend-build: ## Sync backend dependencies from lockfile
	cd $(BACKEND_DIR) && $(UV) sync --frozen

.PHONY: backend-dev
backend-dev: ## Run backend development server
	cd $(BACKEND_DIR) && $(UV) run uvicorn app.main:app --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)

.PHONY: backend-check
backend-check: ## Run backend lint and format checks
	cd $(BACKEND_DIR) && $(UV) run ruff check . && $(UV) run ruff format . --check

.PHONY: backend-format
backend-format: ## Format backend code
	cd $(BACKEND_DIR) && $(UV) run ruff check . --fix && $(UV) run ruff format .

.PHONY: backend-test
backend-test: ## Run backend tests
	cd $(BACKEND_DIR) && $(UV) run python -m pytest $(PYTEST_ARGS)

.PHONY: frontend-install
frontend-install: ## Install frontend dependencies
	cd $(FRONTEND_DIR) && $(NPM) ci

.PHONY: frontend-dev
frontend-dev: ## Run frontend development server
	cd $(FRONTEND_DIR) && $(NPM) run dev -- --host $(FRONTEND_HOST) --port $(FRONTEND_PORT)

.PHONY: frontend-desktop-dev
frontend-desktop-dev: ## Run the frontend in the Tauri desktop shell
	cd $(FRONTEND_DIR) && $(NPM) run tauri:dev

.PHONY: frontend-build
frontend-build: ## Build frontend static artifacts and copy them to backend static path
	cd $(FRONTEND_DIR) && $(NPM) run build

.PHONY: frontend-desktop-build
frontend-desktop-build: ## Build the Tauri desktop application
	cd $(FRONTEND_DIR) && $(NPM) run tauri -- build

.PHONY: frontend-build-sync
frontend-build-sync: ## Generate API types optionally, then build frontend
	cd $(FRONTEND_DIR) && $(NPM) run build:sync

.PHONY: frontend-test
frontend-test: ## Run frontend tests
	cd $(FRONTEND_DIR) && $(NPM) run test

.PHONY: frontend-format
frontend-format: ## Format frontend code
	cd $(FRONTEND_DIR) && $(NPM) run format

.PHONY: frontend-format-check
frontend-format-check: ## Check frontend formatting
	cd $(FRONTEND_DIR) && $(NPM) run format:check

.PHONY: docker-build
docker-build: ## Build docker app image
	bash ./docker/scripts/docker-build.sh

.PHONY: docker-up
docker-up: ## Start docker app and required local infra
	bash ./docker/scripts/docker-up.sh

.PHONY: docker-down
docker-down: ## Stop docker services
	bash ./docker/scripts/docker-down.sh

.PHONY: docker-logs
docker-logs: ## Follow docker logs for DOCKER_SERVICE, defaults to app
	bash ./docker/scripts/docker-logs.sh $(DOCKER_SERVICE)

.PHONY: docker-export
docker-export: ## Export docker app image to docker/artifacts
	bash ./docker/scripts/docker-export.sh

.PHONY: docker-deploy
docker-deploy: ## Build, recreate, and export docker app image
	bash ./docker/scripts/docker-deploy.sh

.PHONY: docker-observability-up
docker-observability-up: ## Start local observability stack
	@[ -f "$(DOCKER_DIR)/.env" ] || cp "$(DOCKER_DIR)/.env.example" "$(DOCKER_DIR)/.env"
	cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) --env-file .env --profile observability up -d tempo otel-collector prometheus grafana

.PHONY: docker-observability-down
docker-observability-down: ## Stop local observability stack
	@[ -f "$(DOCKER_DIR)/.env" ] || cp "$(DOCKER_DIR)/.env.example" "$(DOCKER_DIR)/.env"
	cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) --env-file .env --profile observability down --remove-orphans
