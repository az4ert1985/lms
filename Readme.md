
# LMS API

Learning Management System API built with FastAPI.

## Requirements

- Python >= 3.12
- uv
- Docker (optional)
- Git

## Installation

Clone repository:

    git clone https://github.com/az4ert1985/lms.git
    cd lms

Install dependencies:

    uv sync --all-groups

Create environment configuration:

    cp .env.example .env

## Local development

    uv run uvicorn app.main:app --reload

API documentation:

    http://localhost:8000/docs

## Docker development

    docker compose \
      -f docker-compose.yml \
      -f docker-compose.dev.yml \
      up --build

## Docker production

    docker compose up --build -d

## Testing

Unit tests:

    uv run pytest tests/unit \
      --cov=app.services \
      --cov-fail-under=80

Integration tests:

    uv run pytest tests/integration \
      --cov=app.api \
      --cov-fail-under=80

## Code quality

    uv run ruff check .
    uv run ruff format .
    uv run mypy app
    uv run bandit -r app

## Dependency audit

    uv export --locked \
      --format requirements-txt \
      --output-file requirements-audit.txt

    uv run pip-audit -r requirements-audit.txt

## Git hooks

Install hooks:

    uv run pre-commit install

Run all hooks:

    uv run pre-commit run --all-files

## Environments

- development
- production
- test

Configure environment using APP_ENV and DATABASE_URL.

## Git workflow

- main: production
- development: integration

All changes must be submitted through Pull Requests.

Direct pushes to main and development are prohibited.

All four required GitHub Actions jobs must pass before merging.
