# Development Dockerfile for Mobius Backend
# This Dockerfile is optimized for development with hot reloading
# Uses multi-stage build to reduce final image size

# Builder stage - includes all build dependencies
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages
# Pinned versions for Debian 12 (Bookworm) to ensure reproducible builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc=4:12.2.0-3 \
    g++=4:12.2.0-3 \
    libpq-dev=15.13-0+deb12u1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Create virtual environment and install Python dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Final stage - minimal runtime image
FROM python:3.11-slim

# Install only runtime dependencies
# Pinned versions for Debian 12 (Bookworm) to ensure reproducible builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5=15.13-0+deb12u1 \
    curl=7.88.1-10+deb12u12 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r mobius && useradd -r -g mobius mobius

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set up environment to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application code with proper ownership
COPY --chown=mobius:mobius app/ ./app/
COPY --chown=mobius:mobius alembic/ ./alembic/
COPY --chown=mobius:mobius pyproject.toml ./

# Switch to non-root user
USER mobius

# Expose the application port
EXPOSE 8000

# Health check for development
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose.yml)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]