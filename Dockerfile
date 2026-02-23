# --- Stage 1: Builder ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy dependency files first for layer caching
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies into a virtual environment
RUN python -m venv /build/.venv && \
    /build/.venv/bin/pip install --no-cache-dir --upgrade pip && \
    /build/.venv/bin/pip install --no-cache-dir .

# --- Stage 2: Runtime ---
FROM python:3.12-slim AS runtime

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy application code
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create data directory for SQLite database
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
