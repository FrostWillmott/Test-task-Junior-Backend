# --- Stage 1: Build ---
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# --- Stage 2: Final ---
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

RUN addgroup --system django && \
    adduser --system --group django && \
    mkdir -p /app/staticfiles && \
    chown -R django:django /app

USER django

# Collect static files (dummy DATABASE_URL to avoid env.db() failure at build time)
RUN DATABASE_URL=sqlite:///dummy SECRET_KEY=build-only DEBUG=True python manage.py collectstatic --noinput

HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
