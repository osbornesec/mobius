# Mobius Context Engineering Platform - Makefile

.PHONY: help install dev test build clean docker-build docker-up docker-down

help:
	@echo "Mobius Context Engineering Platform - Available commands:"
	@echo "  make install        Install all dependencies (backend & frontend)"
	@echo "  make dev           Run development servers"
	@echo "  make test          Run all tests"
	@echo "  make build         Build production assets"
	@echo "  make clean         Clean build artifacts"
	@echo "  make docker-build  Build Docker images"
	@echo "  make docker-up     Start Docker containers"
	@echo "  make docker-down   Stop Docker containers"

# Installation
install: install-backend install-frontend

install-backend:
	@echo "Installing backend dependencies..."
	pip install -r requirements.txt
	pip install -e .

install-frontend:
	@echo "Installing frontend dependencies..."
	npm install

# Development
dev:
	@echo "Starting development servers..."
	@make -j 2 dev-backend dev-frontend

dev-backend:
	@echo "Starting FastAPI backend..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	@echo "Starting React frontend..."
	npm start

# Testing
test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	pytest tests/backend/ -v --cov=app --cov-report=term-missing

test-frontend:
	@echo "Running frontend tests..."
	npm test

test-e2e:
	@echo "Running end-to-end tests..."
	npm run test:e2e

# Building
build: build-backend build-frontend

build-backend:
	@echo "Building backend..."
	python -m build

build-frontend:
	@echo "Building frontend..."
	npm run build

# Docker
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

# Database
db-migrate:
	@echo "Running database migrations..."
	alembic upgrade head

db-rollback:
	@echo "Rolling back database migration..."
	alembic downgrade -1

# Linting and Formatting
lint:
	@echo "Running linters..."
	@make -j 2 lint-backend lint-frontend

lint-backend:
	@echo "Linting backend..."
	flake8 app/
	black --check app/
	mypy app/

lint-frontend:
	@echo "Linting frontend..."
	npm run lint

format:
	@echo "Formatting code..."
	@make -j 2 format-backend format-frontend

format-backend:
	@echo "Formatting backend..."
	black app/
	isort app/

format-frontend:
	@echo "Formatting frontend..."
	npm run format

# Cleaning
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete