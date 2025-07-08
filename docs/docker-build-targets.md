# Docker Build Targets

The Mobius backend Dockerfile uses a multi-stage build to properly separate
production and development dependencies.

## Build Stages

### 1. `prod-builder`

- Installs only production dependencies from `requirements.txt`
- Creates a virtual environment at `/opt/venv`
- Used as the base for the production image

### 2. `dev-builder`

- Extends `prod-builder`
- Adds development dependencies from `requirements-dev.txt`
- Used for the development image

### 3. `production` (default)

- Minimal runtime image
- Contains only production dependencies
- Runs as non-root user `mobius`
- No hot-reloading, optimized for production

### 4. `development`

- Extends `production`
- Includes all development dependencies
- Enables hot-reloading with uvicorn
- Used by default in `docker-compose.yml`

## Usage

### Development (default)

```bash
# Uses development target automatically via docker-compose.yml
docker-compose up backend
```

### Production Build

```bash
# Build production image
docker build -f docker/backend/Dockerfile --target production -t mobius-backend:prod .

# Or use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up backend
```

### Building Specific Targets

```bash
# Build only production dependencies
docker build -f docker/backend/Dockerfile --target prod-builder -t mobius-builder:prod .

# Build with dev dependencies
docker build -f docker/backend/Dockerfile --target dev-builder -t mobius-builder:dev .
```

## Benefits

1. **Smaller Production Images**: Production images don't include test
   frameworks, linters, or other dev tools
2. **Security**: Fewer dependencies in production means smaller attack surface
3. **Clear Separation**: Development tools are explicitly separated from
   production code
4. **Flexibility**: Can build for different environments from the same
   Dockerfile
