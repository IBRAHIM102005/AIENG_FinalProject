# =====================================================================
# Dockerfile for the AI Engineering Software Engineering Final
# Topic 4 — Async Research Assistant (Storage + CLI layer)
# =====================================================================

# ---- Stage 1: Builder -----------------------------------------------
FROM python:3.12.9-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt


# ---- Stage 2: Runtime -----------------------------------------------
FROM python:3.12.9-slim AS runtime

LABEL org.opencontainers.image.title="Async Research Assistant"
LABEL org.opencontainers.image.description="AIENG Final Project — Topic 4 SE layer"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.authors="Fatma"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    LOG_LEVEL=INFO \
    CACHE_DIR=/app/.cache \
    CACHE_TTL_SECONDS=86400 \
    PER_SOURCE_TIMEOUT_SECONDS=10 \
    MAX_SOURCES_PER_QUERY=3 \
    PYTHONPATH="/app/topic-4-research-assistant:/app"

COPY --from=builder /opt/venv /opt/venv

RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup \
               --create-home --shell /bin/bash \
               --no-log-init appuser

WORKDIR /app

# Copy entire repo — src/storage/ and topic-4-research-assistant/ both included
COPY --chown=appuser:appgroup . .

RUN mkdir -p /app/.cache /app/logs \
    && chown -R appuser:appgroup /app

USER appuser

# Validates the storage layer is importable and SQLite is functional.
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=2 \
    CMD python -c \
        "from src.storage.cache_store import CacheStore; CacheStore(':memory:').open().close(); print('ok')" \
    || exit 1

# PYTHONPATH includes topic-4-research-assistant/ so src.cli resolves correctly
CMD ["python", "-m", "src.cli", "--help"]

# =====================================================================
# Build and run:
#   docker build -t finalproj .
#   docker run --env-file topic-4-research-assistant/.env finalproj ask "What is neural scaling?"
#
# Verify before submission:
#   docker run --env-file topic-4-research-assistant/.env finalproj python -m pytest tests/test_ai_smoke.py
# =====================================================================
