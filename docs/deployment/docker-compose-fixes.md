# Docker Compose Configuration Fixes

## Overview

This document describes the fixes applied to the Docker Compose configurations to resolve build and networking issues in both development and production environments.

## Issues Fixed

### 1. Production Build Failure - Missing MOBIUS_SECRET_KEY

**Problem**: The production docker-compose.prod.yml file used the `${MOBIUS_SECRET_KEY:?Missing MOBIUS_SECRET_KEY}` syntax, which causes Docker Compose to fail during the build phase if the variable is not set.

**Solution**:
- Changed to use a fallback placeholder: `${MOBIUS_SECRET_KEY:-PLACEHOLDER_SECRET_KEY_SET_IN_PRODUCTION}`
- Added a production configuration validation script (`check-production-config.sh`) that runs on container startup
- The script validates that the secret key is properly set and not using a placeholder value
- If critical variables are missing or using placeholders, the container will fail to start with clear error messages

**Security**: This approach maintains security by:
- Allowing builds to complete without exposing real secrets
- Preventing the application from starting in production with insecure placeholder values
- Providing clear feedback about missing configuration

### 2. Development Networking Issue - Frontend Cannot Reach Backend

**Problem**: The backend service was bound to `127.0.0.1:8000:8000`, making it accessible only from localhost on the host machine. The frontend's browser could not reach the backend because of this restrictive binding.

**Solution**:
- Changed the backend port binding from `127.0.0.1:8000:8000` to `8000:8000`
- This allows the backend to be accessible on all interfaces from the host machine
- The frontend configuration remains unchanged (`VITE_API_URL: http://localhost:8000`) as it runs in the browser

**Security Considerations**:
- In development, exposing the backend on all interfaces is acceptable
- The backend already has CORS configuration to restrict which origins can access it
- For production deployments, consider using a reverse proxy or API gateway for additional security

## Configuration Files Modified

1. **docker-compose.prod.yml**:
   - Modified `MOBIUS_SECRET_KEY` environment variable to use fallback syntax

2. **docker-compose.yml**:
   - Changed backend port binding to allow external access

3. **docker/backend/Dockerfile**:
   - Added production configuration check script
   - Set up ENTRYPOINT for production stage to validate configuration
   - Ensured development stage doesn't use the validation entrypoint

4. **scripts/backend/check-production-config.sh**:
   - New script that validates critical production environment variables
   - Prevents application startup if using placeholder values

## Usage

### Development
```bash
docker-compose up
```
The backend will be accessible at http://localhost:8000 from both the host and browser.

### Production
```bash
# Set required environment variables
export MOBIUS_SECRET_KEY="your-secure-secret-key"
export POSTGRES_USER="production-user"
export POSTGRES_PASSWORD="secure-password"
export REDIS_PASSWORD="redis-password"
export QDRANT_API_KEY="qdrant-api-key"
export MOBIUS_ALLOWED_ORIGINS='["https://yourdomain.com"]'

# Run with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

The configuration check script will validate all required variables before starting the application.

## Best Practices

1. **Never commit real secrets** - Always use environment variables or secret management systems
2. **Use placeholder values only for builds** - The validation script ensures they're replaced before runtime
3. **Document all required environment variables** - See `docs/deployment/production-environment-variables.md`
4. **Use proper secret management** in production (e.g., HashiCorp Vault, AWS Secrets Manager, etc.)
