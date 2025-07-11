# Multi-stage Dockerfile for Mobius Backend
# Properly separates production and development dependencies
# Uses multi-stage build to reduce final image size

# Production builder stage - only production dependencies
FROM python:3.11-slim as prod-builder

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages
# Pinned versions for Debian 12 (Bookworm) to ensure reproducible builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc=4:12.2.0-3 \
    g++=4:12.2.0-3 \
    libpq-dev=15.13-0+deb12u1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only production requirements
COPY requirements.txt ./

# Create virtual environment and install ONLY production dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip==24.0 && \
    pip install --no-cache-dir -r requirements.txt

# Development builder stage - includes dev dependencies
FROM prod-builder as dev-builder

# Copy dev requirements
COPY requirements-dev.txt ./

# Install development dependencies on top of production ones
RUN pip install --no-cache-dir -r requirements-dev.txt

# Final production stage - minimal runtime image
FROM python:3.11-slim as production

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

# Copy virtual environment from production builder (no dev dependencies)
COPY --from=prod-builder /opt/venv /opt/venv

# Set up environment to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy application code with proper ownership
COPY --chown=mobius:mobius app/ ./
COPY --chown=mobius:mobius alembic/ ./alembic/
COPY --chown=mobius:mobius pyproject.toml ./

# Copy production config check script
COPY --chown=mobius:mobius scripts/backend/check-production-config.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/check-production-config.sh

# Switch to non-root user
USER mobius

# Expose the application port
EXPOSE 8000

# Health check for development
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use the config check script as entrypoint in production
ENTRYPOINT ["/usr/local/bin/check-production-config.sh"]

# Default command for production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage - includes dev dependencies for local development
FROM production as development

# Switch back to root to install dev dependencies
USER root

# Copy virtual environment with dev dependencies from dev-builder
COPY --from=dev-builder /opt/venv /opt/venv

# Switch back to non-root user
USER mobius

# Override the production entrypoint for development
ENTRYPOINT []

# Development command with hot reloading
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]