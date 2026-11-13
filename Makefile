
.PHONY: install run test lint format typecheck security audit check
.PHONY: db-up db-down migrate migration docker-up docker-down

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

run:
	APP_ENV=development uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	APP_ENV=test pytest -v

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check --fix app tests

typecheck:
	mypy app

security:
	bandit -r app -f screen -c pyproject.toml

security-report:
	bandit -r app -f json -o bandit-report.json -c pyproject.toml

audit:
	pip-audit -r requirements.txt

check: lint typecheck security audit test

db-up:
	docker compose up -d db

db-down:
	docker compose down

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(name)"

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down
