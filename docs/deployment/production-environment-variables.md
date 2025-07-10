# Production Environment Variables Guide

This document describes the critical environment variables required for
production deployment using `docker-compose.prod.yml`.

## Required Production Variables

### Redis Authentication

**Variable:** `REDIS_PASSWORD`  
**Required:** Yes (in production)  
**Purpose:** Secures Redis cache instance with password authentication  
**Example Generation:** `openssl rand -base64 32`  
**Docker Compose Reference:** Line 37 in `docker-compose.prod.yml`

```bash
# Generate a secure password
openssl rand -base64 32

# Example (DO NOT USE IN PRODUCTION):
REDIS_PASSWORD=change_me_use_strong_password_in_production
```

**Security Notes:**

- Never commit actual passwords to version control
- Use CI/CD secrets management for production deployments
- Rotate passwords regularly
- Monitor Redis logs for unauthorized access attempts

### Qdrant API Authentication

**Variable:** `QDRANT_API_KEY`  
**Required:** Yes (in production)  
**Purpose:** Secures Qdrant vector database API access  
**Example Generation:** `openssl rand -hex 32`  
**Docker Compose Reference:** Line 46 in `docker-compose.prod.yml`

```bash
# Generate a secure API key
openssl rand -hex 32

# Example (DO NOT USE IN PRODUCTION):
QDRANT_API_KEY=your_qdrant_api_key_replace_with_secure_value
```

**Security Notes:**

- Use a strong, randomly generated API key
- Store in secure secrets management system
- Limit API key permissions to required operations only
- Monitor Qdrant access logs for suspicious activity

## Production Deployment Checklist

Before deploying to production with `docker-compose.prod.yml`:

1. **Set all required environment variables:**
   - [ ] `REDIS_PASSWORD` - Generated and stored securely
   - [ ] `QDRANT_API_KEY` - Generated and stored securely
   - [ ] `POSTGRES_PASSWORD` - Already documented in .env.example

2. **Verify security settings:**
   - [ ] All passwords are strong and randomly generated
   - [ ] No default or example values are used
   - [ ] Secrets are managed through CI/CD pipeline
   - [ ] Environment variables are not logged or exposed

3. **Test configuration:**

   ```bash
   # Validate environment variables are set
   docker-compose -f docker-compose.prod.yml config

   # Check for missing required variables
   docker-compose -f docker-compose.prod.yml config | grep -E "(REDIS_PASSWORD|QDRANT_API_KEY)"
   ```

## Environment Variable Injection

For production deployments, inject these variables through your CI/CD pipeline:

### GitHub Actions Example

```yaml
- name: Deploy to Production
  env:
    REDIS_PASSWORD: ${{ secrets.REDIS_PASSWORD }}
    QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
  run: |
    docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Secrets Example

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mobius-secrets
type: Opaque
data:
  redis-password: <base64-encoded-password>
  qdrant-api-key: <base64-encoded-key>
```

## Troubleshooting

### Missing Variable Errors

If you see errors like:

```
ERROR: Missing required environment variable: REDIS_PASSWORD
```

Ensure:

1. The variable is set in your environment
2. The variable name matches exactly (case-sensitive)
3. The value is not empty

### Connection Failures

If services fail to connect in production:

1. Verify the passwords/keys match between services
2. Check service logs for authentication errors
3. Ensure network connectivity between containers

## Additional Resources

- [Docker Compose Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [Redis Security Best Practices](https://redis.io/docs/manual/security/)
- [Qdrant Authentication](https://qdrant.tech/documentation/guides/security/)
