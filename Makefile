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
MERGE_METHOD ?= merge
ALLOW_NON_MERGE_METHOD ?= false

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available Make targets
	@awk 'BEGIN {FS = ":.*##"; printf "Available targets:\n"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "  %-28s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: init
init: frontend-init ## Initialize backend, frontend, and docker env files
	bash ./docker/scripts/init-env.sh

.PHONY: env-sync env-check docker-env-sync docker-env-check env-contract-check
env-contract-check: ## Check shared development/deployment example keys without local env files
	$(UV) run --project $(BACKEND_DIR) python scripts/env.py contract-check

env-sync: ## Sync development env keys and template layout with backups
	$(UV) run --project $(BACKEND_DIR) python scripts/env.py sync --scope dev

env-check: ## Check development env keys, layout, and template consistency
	$(UV) run --project $(BACKEND_DIR) python scripts/env.py check --scope dev

docker-env-sync: ## Sync deployment env keys and template layout with backups
	$(UV) run --project $(BACKEND_DIR) python scripts/env.py sync --scope docker

docker-env-check: ## Check deployment env keys, layout, and template consistency
	$(UV) run --project $(BACKEND_DIR) python scripts/env.py check --scope docker

.PHONY: install
install: backend-install frontend-install ## Install backend and frontend dependencies

.PHONY: build
build: backend-build frontend-package ## Build backend environment and frontend static artifacts

.PHONY: check
check: project-init-check architecture-check env-contract-check backend-check frontend-format-check frontend-typecheck contract-check frontend-api-check ## Check code, env keys, types, and pinned API contracts

.PHONY: git-governance-check
git-governance-check: ## Validate git governance; optionally pass commit, PR, and merge metadata
	bash ./scripts/validate-git-governance.sh

.PHONY: format
format: project-init-format backend-format frontend-format ## Format backend and frontend code

.PHONY: test
test: project-init-test backend-test frontend-test ## Run backend and frontend tests

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
frontend-install: frontend-init ## Install frontend dependencies
	cd $(FRONTEND_DIR) && $(NPM) ci

.PHONY: frontend-dev
frontend-dev: ## Run frontend development server
	cd $(FRONTEND_DIR) && $(NPM) run dev -- --host $(FRONTEND_HOST) --port $(FRONTEND_PORT)

.PHONY: frontend-desktop-dev
frontend-desktop-dev: ## Run the frontend in the Tauri desktop shell
	cd $(FRONTEND_DIR) && $(NPM) run tauri:dev

.PHONY: frontend-build
frontend-build: project-brand ## Build only B4React dist artifacts
	cd $(FRONTEND_DIR) && $(NPM) run build

.PHONY: frontend-desktop-build
frontend-desktop-build: ## Build the Tauri desktop application
	cd $(FRONTEND_DIR) && $(NPM) run tauri -- build

.PHONY: frontend-build-sync
frontend-build-sync: ## Regenerate local pinned types, then build B4React dist
	cd $(FRONTEND_DIR) && $(NPM) run build:sync

.PHONY: contract-export contract-check frontend-api-generate frontend-typecheck
contract-export: ## Export the OpenAPI baseline without running a server
	cd $(BACKEND_DIR) && $(UV) run python -m app.export_openapi ../../contracts/openapi.json

contract-check: frontend-contract-check ## Check backend export and pinned frontend baseline
	cd $(BACKEND_DIR) && $(UV) run python -m app.export_openapi ../../contracts/openapi.json --check

frontend-api-generate: ## Generate types from B4React own pinned baseline
	cd $(FRONTEND_DIR) && $(NPM) run generate:api:contract

frontend-typecheck: ## Check frontend TypeScript without building static artifacts
	cd $(FRONTEND_DIR) && $(NPM) exec tsc -- --noEmit

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
docker-up: ## Start required infra and wait for app readiness
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
docker-deploy: ## Build, recreate app only, wait for readiness, and export image
	bash ./docker/scripts/docker-deploy.sh

.PHONY: docker-observability-up
docker-observability-up: ## Start local observability stack
	@[ -f "$(DOCKER_DIR)/.env" ] || cp "$(DOCKER_DIR)/.env.example" "$(DOCKER_DIR)/.env"
	cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) --env-file .env --profile observability up -d tempo loki otel-collector prometheus grafana

.PHONY: docker-observability-down
docker-observability-down: ## Stop only local observability services
	@[ -f "$(DOCKER_DIR)/.env" ] || cp "$(DOCKER_DIR)/.env.example" "$(DOCKER_DIR)/.env"
	cd $(DOCKER_DIR) && $(DOCKER_COMPOSE) --env-file .env --profile observability stop grafana prometheus otel-collector tempo loki

.PHONY: frontend-init frontend-package frontend-contract-check frontend-api-check
frontend-init: ## Initialize submodules at their committed versions
	git submodule update --init --recursive

frontend-package: frontend-build ## Build and package frontend into backend static dist
	node scripts/package-frontend.mjs "$(FRONTEND_DIR)/dist" "$(BACKEND_DIR)/app/static/dist"

frontend-contract-check: ## Compare provider and pinned consumer OpenAPI contracts
	node scripts/check-frontend-contract.mjs "$(FRONTEND_DIR)"

frontend-api-check: ## Detect generated frontend type drift
	cd $(FRONTEND_DIR) && $(NPM) run api:check

export COMMIT_TITLE COMMIT_BODY_FILE PR_TITLE PR_BODY_FILE MERGE_METHOD ALLOW_NON_MERGE_METHOD

.PHONY: git-governance-pr-check
git-governance-pr-check: ## Validate actual PR metadata and every authored commit
	bash ./scripts/validate-git-governance.sh --event-file "$(GITHUB_EVENT_PATH)"

.PHONY: architecture-check backend-architecture-check frontend-architecture-check
architecture-check: backend-architecture-check frontend-architecture-check ## Check backend/frontend dependency boundaries
backend-architecture-check: ## Check router/DB and lower-layer import boundaries
	$(UV) run --project $(BACKEND_DIR) python scripts/check_backend_architecture.py
frontend-architecture-check: ## Check pinned frontend dependency boundaries
	$(MAKE) -C $(FRONTEND_DIR) architecture-check

export EMAIL ROLE
.PHONY: user-role
user-role: ## Set an existing account role: EMAIL=address ROLE=admin|user
	cd $(BACKEND_DIR) && $(UV) run python -m app.manage_user_role

.PHONY: frontend-react-performance-check frontend-test-routes
frontend-react-performance-check: ## Validate frontend state and memo optimization safeguards
	$(MAKE) -C $(FRONTEND_DIR) react-performance-check
frontend-test-routes: project-brand ## Build and verify production frontend lazy routes in Chromium
	$(MAKE) -C $(FRONTEND_DIR) test-routes

PROJECT_CONFIG ?= project.json
export PROJECT_CONFIG
.PHONY: project-plan project-init project-check project-init-check project-init-test
project-plan: ## Preview project initialization from PROJECT_CONFIG without writing files
	$(UV) run --project $(BACKEND_DIR) python scripts/project_init.py plan
project-init: ## Apply identity/features from PROJECT_CONFIG, preserving unrelated env values
	$(UV) run --project $(BACKEND_DIR) python scripts/project_init.py apply
project-check: ## Check generated identity/features against PROJECT_CONFIG
	$(UV) run --project $(BACKEND_DIR) python scripts/project_init.py check
project-init-check: ## Check project initializer code and public manifest example
	$(UV) run --project $(BACKEND_DIR) ruff check scripts/project_init.py scripts/project_identity.py scripts/test_project_init.py scripts/test_project_build.py
	$(UV) run --project $(BACKEND_DIR) ruff format --check scripts/project_init.py scripts/project_identity.py scripts/test_project_init.py scripts/test_project_build.py
project-init-test: ## Verify isolated project initialization scenarios
	$(UV) run --project $(BACKEND_DIR) python -m unittest discover -s scripts -p 'test_project_init.py'

.PHONY: project-brand
project-brand: ## Generate public frontend identity from optional root project.json
	python3 scripts/project_identity.py

.PHONY: project-init-format
project-init-format: ## Format project initializer tooling
	$(UV) run --project $(BACKEND_DIR) ruff check --fix scripts/project_init.py scripts/project_identity.py scripts/test_project_init.py scripts/test_project_build.py
	$(UV) run --project $(BACKEND_DIR) ruff format scripts/project_init.py scripts/project_identity.py scripts/test_project_init.py scripts/test_project_build.py

.PHONY: project-build-test
project-build-test: ## Verify custom branding in an isolated production frontend build
	python3 scripts/test_project_build.py
