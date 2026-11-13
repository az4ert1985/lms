
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /build

RUN pip install --no-cache-dir --upgrade pip

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --no-cache-dir .

# --------------------------------

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app && \
    useradd --system --gid app app

COPY --from=builder /usr/local /usr/local
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
