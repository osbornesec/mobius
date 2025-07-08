# Mobius Context Engineering Platform - Makefile
# =============================================

# Variables
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Project directories
BACKEND_DIR := .
FRONTEND_DIR := frontend
DOCKER_DIR := docker

# Python settings
PYTHON := python3
VENV := ./venv
PIP := $(VENV)/bin/pip
PYTHON_BIN := $(VENV)/bin/python

# Node settings
NODE := node
NPM := npm
PNPM := pnpm

# Docker settings
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_FILE := docker-compose.yml

# Database settings
DB_NAME := mobius_db
DB_USER := mobius_user
DB_HOST := localhost
DB_PORT := 5432

# Service names
SERVICES := postgres redis qdrant backend frontend

.PHONY: help
help: ## Show this help message
	@echo -e "$(BLUE)Mobius Context Engineering Platform - Development Commands$(NC)"
	@echo -e "$(BLUE)=========================================================$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo -e "$(YELLOW)Usage:$(NC) make [command]"

# =============================================
# Docker Commands
# =============================================

.PHONY: up
up: ## Start all services with docker-compose
	@echo -e "$(BLUE)Starting all services...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up -d
	@echo -e "$(GREEN)✓ All services started$(NC)"

.PHONY: down
down: ## Stop all services
	@echo -e "$(BLUE)Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down
	@echo -e "$(GREEN)✓ All services stopped$(NC)"

.PHONY: restart
restart: down up ## Restart all services

.PHONY: logs
logs: ## Show logs for all services (use SERVICE=<service> for specific service)
	@if [ -z "$(SERVICE)" ]; then \
		$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f; \
	else \
		$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs -f $(SERVICE); \
	fi

.PHONY: ps
ps: ## Show running containers
	@echo -e "$(BLUE)Running containers:$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) ps

.PHONY: docker-clean
docker-clean: ## Clean up volumes and containers
	@echo -e "$(RED)Warning: This will remove all containers and volumes!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo -e "$(BLUE)Cleaning up Docker resources...$(NC)"; \
		$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) down -v --remove-orphans; \
		docker system prune -f; \
		echo -e "$(GREEN)✓ Docker cleanup complete$(NC)"; \
	fi

# =============================================
# Backend Commands
# =============================================

.PHONY: backend-venv
backend-venv: ## Create Python virtual environment
	@if [ ! -d "$(VENV)" ]; then \
		echo -e "$(BLUE)Creating Python virtual environment...$(NC)"; \
		$(PYTHON) -m venv venv; \
		echo -e "$(GREEN)✓ Virtual environment created$(NC)"; \
	else \
		echo -e "$(YELLOW)Virtual environment already exists$(NC)"; \
	fi

.PHONY: backend-install
backend-install: backend-venv ## Install Python dependencies
	@echo -e "$(BLUE)Installing backend dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@echo -e "$(GREEN)✓ Backend dependencies installed$(NC)"

.PHONY: backend-dev
backend-dev: ## Run backend in development mode
	@echo -e "$(BLUE)Starting backend development server...$(NC)"
	$(PYTHON_BIN) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: backend-test
backend-test: ## Run backend tests
	@echo -e "$(BLUE)Running backend tests...$(NC)"
	$(PYTHON_BIN) -m pytest tests/ -v

.PHONY: backend-lint
backend-lint: ## Run linting (black, ruff)
	@echo -e "$(BLUE)Running backend linters...$(NC)"
	$(PYTHON_BIN) -m black app/ tests/
	$(PYTHON_BIN) -m ruff check app/ tests/ --fix
	@echo -e "$(GREEN)✓ Backend linting complete$(NC)"

.PHONY: backend-typecheck
backend-typecheck: ## Run mypy type checking
	@echo -e "$(BLUE)Running backend type checking...$(NC)"
	$(PYTHON_BIN) -m mypy app/
	@echo -e "$(GREEN)✓ Backend type checking complete$(NC)"

.PHONY: backend-coverage
backend-coverage: ## Run tests with coverage
	@echo -e "$(BLUE)Running backend tests with coverage...$(NC)"
	$(PYTHON_BIN) -m pytest tests/ --cov=app --cov-report=html --cov-report=term

.PHONY: backend-migrate
backend-migrate: ## Run database migrations
	@echo -e "$(BLUE)Running database migrations...$(NC)"
	$(PYTHON_BIN) -m alembic upgrade head
	@echo -e "$(GREEN)✓ Database migrations complete$(NC)"

# =============================================
# Frontend Commands
# =============================================

.PHONY: frontend-install
frontend-install: ## Install Node dependencies
	@echo -e "$(BLUE)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) install
	@echo -e "$(GREEN)✓ Frontend dependencies installed$(NC)"

.PHONY: frontend-dev
frontend-dev: ## Run frontend dev server
	@echo -e "$(BLUE)Starting frontend development server...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run dev

.PHONY: frontend-build
frontend-build: ## Build frontend for production
	@echo -e "$(BLUE)Building frontend for production...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run build
	@echo -e "$(GREEN)✓ Frontend build complete$(NC)"

.PHONY: frontend-test
frontend-test: ## Run frontend tests
	@echo -e "$(BLUE)Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) test

.PHONY: frontend-lint
frontend-lint: ## Run ESLint
	@echo -e "$(BLUE)Running frontend linter...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run lint
	@echo -e "$(GREEN)✓ Frontend linting complete$(NC)"

.PHONY: frontend-typecheck
frontend-typecheck: ## Run TypeScript checking
	@echo -e "$(BLUE)Running frontend type checking...$(NC)"
	cd $(FRONTEND_DIR) && $(NPM) run type-check
	@echo -e "$(GREEN)✓ Frontend type checking complete$(NC)"

# =============================================
# Database Commands
# =============================================

.PHONY: db-create
db-create: ## Create database
	@echo -e "$(BLUE)Creating database...$(NC)"
	docker exec -it mobius-postgres psql -U $(DB_USER) -c "CREATE DATABASE $(DB_NAME);"
	@echo -e "$(GREEN)✓ Database created$(NC)"

.PHONY: db-migrate
db-migrate: backend-migrate ## Run migrations (alias for backend-migrate)

.PHONY: db-seed
db-seed: ## Seed database with test data
	@echo -e "$(BLUE)Seeding database...$(NC)"
	$(PYTHON_BIN) -m scripts.seed_database
	@echo -e "$(GREEN)✓ Database seeded$(NC)"

.PHONY: db-reset
db-reset: ## Reset database
	@echo -e "$(RED)Warning: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo -e "$(BLUE)Resetting database...$(NC)"; \
		docker exec -it mobius-postgres psql -U $(DB_USER) -c "DROP DATABASE IF EXISTS $(DB_NAME);"; \
		docker exec -it mobius-postgres psql -U $(DB_USER) -c "CREATE DATABASE $(DB_NAME);"; \
		$(MAKE) db-migrate; \
		echo -e "$(GREEN)✓ Database reset complete$(NC)"; \
	fi

# =============================================
# Utility Commands
# =============================================

.PHONY: install
install: backend-install frontend-install ## Install all dependencies
	@echo -e "$(GREEN)✓ All dependencies installed$(NC)"

.PHONY: test
test: ## Run all tests
	@echo -e "$(BLUE)Running all tests...$(NC)"
	$(MAKE) backend-test
	$(MAKE) frontend-test
	@echo -e "$(GREEN)✓ All tests complete$(NC)"

.PHONY: lint
lint: ## Run all linters
	@echo -e "$(BLUE)Running all linters...$(NC)"
	$(MAKE) backend-lint
	$(MAKE) frontend-lint
	@echo -e "$(GREEN)✓ All linting complete$(NC)"

.PHONY: format
format: ## Format all code
	@echo -e "$(BLUE)Formatting all code...$(NC)"
	$(MAKE) backend-lint
	cd $(FRONTEND_DIR) && $(NPM) run format
	@echo -e "$(GREEN)✓ Code formatting complete$(NC)"

.PHONY: typecheck
typecheck: ## Run all type checking
	@echo -e "$(BLUE)Running all type checking...$(NC)"
	$(MAKE) backend-typecheck
	$(MAKE) frontend-typecheck
	@echo -e "$(GREEN)✓ All type checking complete$(NC)"

.PHONY: clean
clean: ## Clean all artifacts
	@echo -e "$(BLUE)Cleaning all artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/dist 2>/dev/null || true
	rm -rf $(FRONTEND_DIR)/node_modules/.cache 2>/dev/null || true
	@echo -e "$(GREEN)✓ Cleanup complete$(NC)"

# =============================================
# Development Workflow Commands
# =============================================

.PHONY: onboard
onboard: ## Set up new developer environment
	@echo -e "$(BLUE)Welcome to Mobius! Setting up your development environment...$(NC)"
	@echo ""
	@if [ ! -f ".env" ]; then \
		echo -e "$(BLUE)Creating .env file from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo -e "$(GREEN)✓ .env file created$(NC)"; \
		echo -e "$(YELLOW)→ Please update your .env file with your actual configuration values$(NC)"; \
	else \
		echo -e "$(YELLOW).env file already exists - skipping creation$(NC)"; \
	fi
	@echo ""
	@echo -e "$(BLUE)Setting up Python virtual environment...$(NC)"
	$(MAKE) backend-venv
	@echo ""
	@echo -e "$(BLUE)Installing all dependencies...$(NC)"
	$(MAKE) install
	@echo ""
	@echo -e "$(GREEN)✓ Developer setup complete!$(NC)"
	@echo ""
	@echo -e "$(YELLOW)Next steps:$(NC)"
	@echo -e "  1. Review and update your .env file with your configuration"
	@echo -e "  2. Run 'make dev' to start the development environment"
	@echo -e "  3. Run 'make help' to see all available commands"
	@echo ""
	@echo -e "$(BLUE)Happy coding! 🚀$(NC)"

.PHONY: dev
dev: ## Start full development environment
	@echo -e "$(BLUE)Starting full development environment...$(NC)"
	$(MAKE) up
	@echo -e "$(YELLOW)Waiting for services to be ready...$(NC)"
	sleep 5
	$(MAKE) db-migrate
	@echo -e "$(GREEN)✓ Development environment ready$(NC)"
	@echo -e "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo -e "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo -e "$(YELLOW)Qdrant: http://localhost:6333$(NC)"

.PHONY: dev-reset
dev-reset: down docker-clean install dev ## Reset and restart development environment

.PHONY: check
check: lint typecheck test ## Run all checks (lint, typecheck, test)
	@echo -e "$(GREEN)✓ All checks passed$(NC)"

# =============================================
# CI/CD Commands
# =============================================

.PHONY: ci
ci: ## Run CI pipeline
	@echo -e "$(BLUE)Running CI pipeline...$(NC)"
	$(MAKE) install
	$(MAKE) check
	$(MAKE) frontend-build
	@echo -e "$(GREEN)✓ CI pipeline complete$(NC)"

.PHONY: build
build: ## Build all components for production
	@echo -e "$(BLUE)Building for production...$(NC)"
	$(MAKE) frontend-build
	# TODO: Uncomment when Dockerfiles are created
	# docker build -f $(DOCKER_DIR)/Dockerfile.backend -t mobius-backend:latest .
	# docker build -f $(DOCKER_DIR)/Dockerfile.frontend -t mobius-frontend:latest $(FRONTEND_DIR)
	@echo -e "$(YELLOW)Note: Docker build commands are commented out until Dockerfiles are created$(NC)"
	@echo -e "$(GREEN)✓ Frontend build complete$(NC)"

# =============================================
# Monitoring Commands
# =============================================

.PHONY: monitor
monitor: ## Show service health and logs
	@echo -e "$(BLUE)Service Status:$(NC)"
	$(MAKE) ps
	@echo ""
	@echo -e "$(BLUE)Recent Logs:$(NC)"
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) logs --tail=20

.PHONY: health
health: ## Check health of all services
	@echo -e "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8000/health || echo -e "$(RED)✗ Backend not responding$(NC)"
	@curl -s http://localhost:3000 > /dev/null && echo -e "$(GREEN)✓ Frontend responding$(NC)" || echo -e "$(RED)✗ Frontend not responding$(NC)"
	@curl -s http://localhost:6333/health || echo -e "$(RED)✗ Qdrant not responding$(NC)"
	@docker exec mobius-postgres pg_isready > /dev/null && echo -e "$(GREEN)✓ PostgreSQL ready$(NC)" || echo -e "$(RED)✗ PostgreSQL not ready$(NC)"
	@docker exec mobius-redis redis-cli ping > /dev/null && echo -e "$(GREEN)✓ Redis ready$(NC)" || echo -e "$(RED)✗ Redis not ready$(NC)"