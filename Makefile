\
# ==============================================================================
# Kavach — root Makefile
# Run `make help` to see this list. Targets are grouped by the phase that
# introduces them; later phases only ADD targets here, they don't redefine
# earlier ones. If a phase's prompt tells a model to "wire up its make target",
# it should append to this file in the matching section, not create a second
# Makefile.
# ==============================================================================

.DEFAULT_GOAL := help
.PHONY: help install install-backend install-frontend \
        db-up db-down db-reset migrate migrate-create seed \
        dev dev-backend dev-frontend \
        ml-download-data ml-augment ml-train ml-train-iforest ml-train-xgboost ml-validate \
        test test-backend test-frontend test-e2e lint lint-backend lint-frontend format \
        build build-frontend docker-build \
        docker-up docker-down deploy-staging deploy-prod \
        clean logs

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── Phase 1/2: Setup ─────────────────────────────────────────────────────────
install: install-backend install-frontend ## Install all dependencies (backend + frontend)

install-backend: ## Install Python backend dependencies
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# ── Phase 1: Database ─────────────────────────────────────────────────────────
db-up: ## Start Postgres + Redis via docker compose
	docker compose -f docker-compose.dev.yml up -d postgres redis

db-down: ## Stop Postgres + Redis
	docker compose -f docker-compose.dev.yml down

db-reset: db-down ## Drop, recreate, migrate, and seed the database — destructive, dev only
	docker compose -f docker-compose.dev.yml down -v
	$(MAKE) db-up
	sleep 3
	$(MAKE) migrate
	$(MAKE) seed

migrate: ## Apply all pending Alembic migrations
	cd backend && . .venv/bin/activate && alembic upgrade head

migrate-create: ## Create a new migration — usage: make migrate-create name="add users table"
	cd backend && . .venv/bin/activate && alembic revision --autogenerate -m "$(name)"

seed: ## Run the database seed script
	cd backend && . .venv/bin/activate && python -m app.seed

# ── Phase 2/3: Development servers ────────────────────────────────────────────
dev: ## Run backend + frontend together (requires 'concurrently' or two terminals)
	npx concurrently -n backend,frontend -c blue,green "$(MAKE) dev-backend" "$(MAKE) dev-frontend"

dev-backend: ## Run the FastAPI backend with autoreload
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run the React dev server
	cd frontend && npm run dev

# ── Phase 4: ML pipeline ───────────────────────────────────────────────────────
ml-download-data: ## Download the base PaySim dataset from Kaggle (requires kaggle.json)
	cd ml && python download_paysim.py

ml-augment: ## Run the agent-metadata augmentation pipeline
	cd ml && python augment.py

ml-train: ml-train-iforest ml-train-xgboost ## Train both ML models

ml-train-iforest: ## Train the Isolation Forest anomaly model
	cd ml && python train_isolation_forest.py

ml-train-xgboost: ## Train the XGBoost risk classifier
	cd ml && python train_xgboost.py

ml-validate: ## Run model validation and regenerate validation_report.md
	cd ml && python validate.py

# ── Phase 9: Testing & linting ─────────────────────────────────────────────────
test: test-backend test-frontend ## Run all test suites

test-backend: ## Run backend pytest suite
	cd backend && . .venv/bin/activate && pytest -v

test-frontend: ## Run frontend test suite
	cd frontend && npm run test

test-e2e: ## Run end-to-end tests against a running local stack
	cd e2e && npm run test:e2e

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend Python code (ruff)
	cd backend && . .venv/bin/activate && ruff check .

lint-frontend: ## Lint frontend JavaScript/React code
	cd frontend && npm run lint

format: ## Auto-format backend and frontend code
	cd backend && . .venv/bin/activate && ruff format .
	cd frontend && npm run format

# ── Phase 7/8: Build ───────────────────────────────────────────────────────────
build: build-frontend ## Build production frontend assets
	@echo "Frontend build output: frontend/dist"

build-frontend: ## Build the frontend production bundle
	cd frontend && npm run build

docker-build: ## Build all production Docker images
	docker compose -f docker-compose.prod.yml build

# ── Phase 8: Deployment ────────────────────────────────────────────────────────
docker-up: ## Run the full stack locally via Docker (prod-like)
	docker compose -f docker-compose.prod.yml up -d

docker-down: ## Stop the full local Docker stack
	docker compose -f docker-compose.prod.yml down

deploy-staging: ## Deploy to the staging environment (see 08_devops_deployment_prompt.md)
	./scripts/deploy.sh staging

deploy-prod: ## Deploy to production (see 08_devops_deployment_prompt.md)
	./scripts/deploy.sh production

# ── Utility ─────────────────────────────────────────────────────────────────────
clean: ## Remove build artifacts and caches
	rm -rf frontend/dist frontend/node_modules/.cache backend/.pytest_cache backend/**/__pycache__

logs: ## Tail logs from the local Docker stack
	docker compose -f docker-compose.prod.yml logs -f --tail=200
