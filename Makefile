.DEFAULT_GOAL := help
.PHONY: help build up down restart logs logs-app logs-worker shell \
        migrate migrate-create \
        install dev worker-dev \
        test test-cov test-fast lint format check \
        clean prune

APP_SERVICE    := app
WORKER_SERVICE := worker
DC             := docker compose
DC_RUN         := $(DC) run --rm

help:
	@echo ""
	@echo "  URL Shortener"
	@echo ""
	@echo "  Setup"
	@echo "  ─────────────────────────────────────────"
	@echo "  make install             Install all dependencies (uv)"
	@echo ""
	@echo "  Infrastructure"
	@echo "  ─────────────────────────────────────────"
	@echo "  make build               Build all images"
	@echo "  make up                  Start all services"
	@echo "  make down                Stop all services"
	@echo "  make restart             Restart app + worker"
	@echo "  make logs                Follow logs (all)"
	@echo "  make logs-app            Follow app logs"
	@echo "  make logs-worker         Follow worker logs"
	@echo "  make shell               Shell inside app container"
	@echo ""
	@echo "  Database"
	@echo "  ─────────────────────────────────────────"
	@echo "  make migrate             Apply migrations"
	@echo "  make migrate-create m=   Create new migration"
	@echo ""
	@echo "  Development"
	@echo "  ─────────────────────────────────────────"
	@echo "  make dev                 Start infra + run app locally"
	@echo "  make worker-dev          Run worker locally"
	@echo ""
	@echo "  Testing & Quality"
	@echo "  ─────────────────────────────────────────"
	@echo "  make test                Run all tests"
	@echo "  make test-cov            Run tests + HTML coverage report"
	@echo "  make test-fast           Run tests, skip slow/load"
	@echo "  make lint                Ruff lint check"
	@echo "  make format              Ruff format + fix"
	@echo "  make check               Lint + format check (CI)"
	@echo ""
	@echo "  Cleanup"
	@echo "  ─────────────────────────────────────────"
	@echo "  make clean               Remove .pyc / __pycache__ / htmlcov"
	@echo "  make prune               Remove containers + volumes"
	@echo ""

install:
	uv sync --dev

build:
	$(DC) build

up:
	$(DC) up -d

down:
	$(DC) down

restart:
	$(DC) restart $(APP_SERVICE) $(WORKER_SERVICE)

logs:
	$(DC) logs -f

logs-app:
	$(DC) logs -f $(APP_SERVICE)

logs-worker:
	$(DC) logs -f $(WORKER_SERVICE)

shell:
	$(DC) exec $(APP_SERVICE) /bin/bash

migrate:
	$(DC_RUN) migrate alembic upgrade head

migrate-create:
	@test -n "$(m)" || (echo "  Usage: make migrate-create m=migration_name" && exit 1)
	$(DC_RUN) $(APP_SERVICE) alembic revision --autogenerate -m "$(m)"

dev:
	$(DC) up -d db redis
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

worker-dev:
	$(DC) up -d db redis
	uv run python -m src.worker.worker

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "  Coverage report → htmlcov/index.html"
	@echo ""

test-fast:
	uv run pytest -m "not slow and not load"

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

check:
	uv run ruff format --check src tests
	uv run ruff check src tests

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -name ".coverage" -delete
	@echo "  Cleaned."

prune:
	$(DC) down -v --remove-orphans
	docker system prune -f
	@echo "  Pruned."