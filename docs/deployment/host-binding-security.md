# Host Binding Security Guide for Mobius Platform

## Overview

This guide covers security best practices for configuring host binding in the Mobius backend application. Proper host binding configuration is crucial for preventing unauthorized access and ensuring secure deployment.

## Default Configuration

As of the latest update, the Mobius platform defaults to **secure host binding**:

- **Default Host**: `127.0.0.1` (localhost only)
- **Default Port**: `8000`

This configuration ensures that by default, the application only accepts connections from the local machine, preventing unintended exposure to network interfaces.

## Environment-Specific Recommendations

### Development Environment

For local development, use the default settings:

```bash
MOBIUS_HOST=127.0.0.1
MOBIUS_PORT=8000
```

This configuration:
- ✅ Restricts access to localhost only
- ✅ Prevents accidental exposure to network
- ✅ Suitable for single-developer environments

### Docker/Container Environments

When running in Docker, you may need to bind to all interfaces:

```bash
MOBIUS_HOST=0.0.0.0
MOBIUS_PORT=8000
```

**Important**: This is safe ONLY when:
- Running inside Docker with proper network isolation
- Using Docker Compose with defined networks
- Not exposing ports directly to the internet

### Production Environment

For production deployments:

1. **Behind a Reverse Proxy** (Recommended):
   ```bash
   MOBIUS_HOST=127.0.0.1
   MOBIUS_PORT=8000
   ```
   - Let nginx/Apache/Caddy handle external connections
   - Application remains isolated from direct internet access

2. **Kubernetes/Container Orchestration**:
   ```bash
   MOBIUS_HOST=0.0.0.0
   MOBIUS_PORT=8000
   ```
   - Safe within pod network isolation
   - Service/Ingress handles external routing

3. **Direct Deployment** (Not Recommended):
   - If you must bind to `0.0.0.0`, ensure:
     - Firewall rules restrict access
     - TLS/SSL is configured
     - Rate limiting is enabled
     - Security headers are set

## Security Features

### 1. Host Validation

The application validates host binding configuration and issues warnings:

```python
# Development mode with 0.0.0.0
WARNING: Running in development mode with host=0.0.0.0 is insecure.

# Production mode with 127.0.0.1
WARNING: Running in production mode with host=127.0.0.1 will only accept local connections.
```

### 2. TrustedHostMiddleware

The application automatically configures `TrustedHostMiddleware`:

- **Development**: Allows common local hosts (localhost, 127.0.0.1)
- **Production**: Restricts to configured domain names

### 3. Environment Detection

The application adjusts security settings based on the environment:

```python
MOBIUS_ENVIRONMENT=development  # or staging, production
```

## Common Scenarios

### Scenario 1: Local Development

```bash
# Safe default configuration
MOBIUS_HOST=127.0.0.1
MOBIUS_PORT=8000
MOBIUS_ENVIRONMENT=development
```

### Scenario 2: Docker Development

```bash
# docker-compose.yml
services:
  backend:
    environment:
      - MOBIUS_HOST=0.0.0.0  # OK within container
      - MOBIUS_PORT=8000
    ports:
      - "127.0.0.1:8000:8000"  # Expose only to localhost
```

### Scenario 3: Production with Nginx

```bash
# Backend configuration
MOBIUS_HOST=127.0.0.1
MOBIUS_PORT=8000
MOBIUS_ENVIRONMENT=production

# Nginx proxy configuration
upstream mobius_backend {
    server 127.0.0.1:8000;
}
```

### Scenario 4: Kubernetes Deployment

```yaml
# deployment.yaml
env:
  - name: MOBIUS_HOST
    value: "0.0.0.0"  # OK within pod
  - name: MOBIUS_PORT
    value: "8000"
  - name: MOBIUS_ENVIRONMENT
    value: "production"
```

## Security Checklist

Before deploying to production:

- [ ] Host binding is appropriate for deployment environment
- [ ] Firewall rules are configured if using 0.0.0.0
- [ ] Reverse proxy is configured for production
- [ ] TLS/SSL certificates are installed
- [ ] Security headers are configured
- [ ] Rate limiting is enabled
- [ ] CORS origins are properly restricted
- [ ] Environment variables are securely managed

## Troubleshooting

### Application not accessible from browser

If running locally with `MOBIUS_HOST=127.0.0.1`:
- Access via `http://localhost:8000` or `http://127.0.0.1:8000`
- Not accessible via machine's IP address (this is intentional)

### Docker container not accessible

Ensure:
1. Container uses `MOBIUS_HOST=0.0.0.0`
2. Port mapping is correct: `-p 8000:8000`
3. No firewall blocking Docker networks

### Production deployment issues

Check:
1. Reverse proxy configuration
2. Security group/firewall rules
3. Health check endpoints
4. Container orchestration networking

## Additional Security Recommendations

1. **Never expose 0.0.0.0 directly to internet** without proper security layers
2. **Use environment-specific configuration** files
3. **Monitor access logs** for suspicious activity
4. **Implement rate limiting** at application and infrastructure levels
5. **Regular security audits** of network configuration
6. **Use secrets management** for sensitive configuration

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Host Header Injection](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/17-Testing_for_Host_Header_Injection)
- [Docker Networking Security](https://docs.docker.com/engine/security/)