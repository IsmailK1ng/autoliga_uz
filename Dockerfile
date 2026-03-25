# ─────────────────────────────────────────────────────────────────────────────
# Multi-stage Dockerfile for autoliga_uz
# Stage 1  — build deps (keeps final image smaller)
# Stage 2  — production image
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed only during build (compiling psycopg2, Pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: production image ────────────────────────────────────────────────
FROM python:3.11-slim AS production

# Runtime system libs only (no compiler)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy pre-built wheels from builder
COPY --from=builder /install /usr/local

# Copy project source
COPY --chown=appuser:appuser . .

# Create dirs Django expects
RUN mkdir -p /app/media /app/static /app/logs \
    && chown -R appuser:appuser /app

USER appuser

# Collect static during image build (requires SECRET_KEY at build time —
# set via build-arg or supply a dummy value)
ARG SECRET_KEY=build-dummy-secret-key-not-used-at-runtime
ARG DJANGO_SETTINGS_MODULE=myproject.settings
ENV DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# ── Health check (TCP — works without a /health/ URL in Django) ───────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('localhost',8000),5); s.close()" || exit 1

# ── Default command: gunicorn (production) ───────────────────────────────────
# Bot runs as a separate service (see docker-compose.yml).
CMD ["gunicorn", "myproject.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
