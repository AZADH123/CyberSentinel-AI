.PHONY: help install migrate seed test lint typecheck check run

help:
	@echo "install    Create/sync the Python virtual environment dependencies"
	@echo "migrate    Apply Alembic migrations"
	@echo "test       Run the pytest suite"
	@echo "lint       Run Ruff"
	@echo "typecheck  Run mypy"
	@echo "check      Run lint + typecheck + tests"
	@echo "run        Start the API with reload"

install:
	cd backend && python -m pip install -r requirements.txt

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m cybersentinel.db.seed --if-empty

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check cybersentinel tests

typecheck:
	cd backend && mypy cybersentinel

check: lint typecheck test

run:
	cd backend && uvicorn cybersentinel.api.main:app --reload --host 127.0.0.1 --port 8000
