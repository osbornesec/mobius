# CI/CD Environment Configuration

This document describes the environment variables required for GitHub Actions
workflows.

## Required Environment Variables for Docker Compose Validation

The production docker-compose file (`docker-compose.prod.yml`) requires certain
environment variables to be set. These are validated in the CI pipeline using
dummy values.

### Required Variables:

1. **POSTGRES_USER** - PostgreSQL username
2. **POSTGRES_PASSWORD** - PostgreSQL password
3. **REDIS_PASSWORD** - Redis password for authentication
4. **QDRANT_API_KEY** - Qdrant vector database API key

## GitHub Actions Secrets Setup

For production deployments, these values should be stored as GitHub repository
secrets:

1. Go to Settings → Secrets and variables → Actions
2. Add the following repository secrets:
   - `PROD_POSTGRES_USER`
   - `PROD_POSTGRES_PASSWORD`
   - `PROD_REDIS_PASSWORD`
   - `PROD_QDRANT_API_KEY`

## CI Validation Values

During CI validation, dummy values are used. These are defined inline in the
workflow files and should NEVER be used in production.

## Example Workflow Usage

```yaml
env:
  POSTGRES_USER: ${{ secrets.PROD_POSTGRES_USER || 'ci_validation' }}
  POSTGRES_PASSWORD:
    ${{ secrets.PROD_POSTGRES_PASSWORD || 'ci_validation_password' }}
  REDIS_PASSWORD: ${{ secrets.PROD_REDIS_PASSWORD || 'ci_redis_password' }}
  QDRANT_API_KEY: ${{ secrets.PROD_QDRANT_API_KEY || 'ci_qdrant_key' }}
```

This pattern allows the workflow to use production secrets when available,
falling back to CI validation values for pull requests and forks.
