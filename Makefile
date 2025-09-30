# Project Agent - Development Makefile

.PHONY: help dev install test clean

help: ## Show this help message
	@echo "Project Agent Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing Python dependencies..."
	cd services && uv sync
	@echo "Installing Node.js dependencies..."
	cd web/portal && npm install

dev: ## Start all development services
	@echo "Starting development services..."
	@echo "API services will run on ports 8081-8084"
	@echo "Web portal will run on port 3000"
	@echo ""
	@echo "Starting services in background..."
	uv run fastapi dev services/api/chat/app.py --port 8081 &
	uv run fastapi dev services/api/inventory/app.py --port 8082 &
	uv run fastapi dev services/api/documents/app.py --port 8083 &
	uv run fastapi dev services/api/admin/app.py --port 8084 &
	uv run python services/workers/ingestion/worker.py &
	cd web/portal && npm run dev &
	@echo "All services started. Use 'make stop' to stop them."

stop: ## Stop all development services
	@echo "Stopping all services..."
	pkill -f "fastapi dev" || true
	pkill -f "python services/workers/ingestion/worker.py" || true
	pkill -f "npm run dev" || true

test: ## Run tests
	@echo "Running Python tests..."
	cd services && uv run pytest
	@echo "Running Node.js tests..."
	cd web/portal && npm test

lint: ## Run linting
	@echo "Linting Python code..."
	cd services && uv run black . && uv run isort . && uv run ruff check .
	@echo "Linting TypeScript code..."
	cd web/portal && npm run lint

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd web/portal && rm -rf .next node_modules 2>/dev/null || true

setup-env: ## Setup environment file from template
	@echo "Setting up environment file..."
	@if [ ! -f services/.env ]; then \
		cp services/env.example services/.env; \
		echo "Created services/.env from template"; \
		echo "Please edit services/.env with your GCP configuration"; \
	else \
		echo "services/.env already exists"; \
	fi

terraform-init: ## Initialize Terraform
	@echo "Initializing Terraform..."
	cd infra/terraform && terraform init

terraform-plan: ## Plan Terraform changes
	@echo "Planning Terraform changes..."
	cd infra/terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	@echo "Applying Terraform changes..."
	cd infra/terraform && terraform apply

deploy: ## Deploy to Cloud Run
	@echo "Deploying to Cloud Run..."
	gcloud builds submit --config ops/cloudbuild.yaml .
