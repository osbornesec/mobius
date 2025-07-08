# Docker Linting Guide for Mobius Project

This guide covers Docker linting tools and their integration into the Mobius
development workflow, ensuring consistent and secure Docker configurations
across the platform.

## Table of Contents

1. [Hadolint - Dockerfile Linter](#hadolint---dockerfile-linter)
2. [Docker Compose Validation](#docker-compose-validation)
3. [Additional Docker Analysis Tools](#additional-docker-analysis-tools)
4. [Integration Strategies](#integration-strategies)
5. [Mobius-Specific Configuration](#mobius-specific-configuration)

## Hadolint - Dockerfile Linter

Hadolint is the most popular Dockerfile linter that helps you build best
practice Docker images. It parses Dockerfiles into an AST and performs
rules-based checks.

### Installation

#### Local Installation (Linux/WSL)

```bash
# Download the latest version
wget -O /tmp/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64

# Make it executable and move to PATH
chmod +x /tmp/hadolint
sudo mv /tmp/hadolint /usr/local/bin/hadolint

# Verify installation
hadolint --version
```

#### Using Docker (No installation required)

```bash
# Run hadolint using Docker
docker run --rm -i hadolint/hadolint < Dockerfile
```

#### macOS Installation

```bash
brew install hadolint
```

### Basic Usage

```bash
# Lint a single Dockerfile
hadolint docker/backend/Dockerfile

# Lint multiple Dockerfiles
hadolint docker/*/Dockerfile*

# Output in different formats
hadolint -f json docker/backend/Dockerfile
hadolint -f checkstyle docker/backend/Dockerfile
```

### Configuration

Create a `.hadolint.yaml` file in the project root:

```yaml
# .hadolint.yaml
ignored:
  - DL3008 # Pin versions in apt-get install
  - DL3009 # Delete the apt-get lists after installing

trustedRegistries:
  - docker.io
  - gcr.io
  - quay.io

label-schema:
  # Enforce Mobius-specific labels
  maintainer: required
  version: required
  description: required

strict-labels: true

# Override severity levels
overrides:
  - id: DL3001
    severity: error # Avoid using sudo
  - id: DL3002
    severity: error # Last user should not be root
  - id: DL3018
    severity: warning # Pin versions in apk add
  - id: DL3059
    severity: info # Multiple consecutive RUN instructions
```

## Docker Compose Validation

### Docker Compose Config Validation

```bash
# Validate docker-compose.yml syntax
docker-compose -f docker-compose.yml config --quiet

# Validate production compose file
docker-compose -f docker-compose.prod.yml config --quiet

# Check for unused environment variables
docker-compose config --services
```

## Additional Docker Analysis Tools

### 1. dockerfile-utils

Provides utilities for parsing and analyzing Dockerfiles.

```bash
# Installation
pip install dockerfile

# Usage example
python -c "from dockerfile import parse_file; print(parse_file('docker/backend/Dockerfile'))"
```

### 2. dockerfilelint (Alternative to Hadolint)

```bash
# Installation
npm install -g dockerfilelint

# Usage
dockerfilelint docker/backend/Dockerfile
```

### 3. Dive - Docker Image Layer Analysis

Dive helps analyze Docker images for wasted space and optimize layer caching.

#### Installation

```bash
# Linux/WSL
wget https://github.com/wagoodman/dive/releases/download/v0.11.0/dive_0.11.0_linux_amd64.tar.gz
tar -xzf dive_0.11.0_linux_amd64.tar.gz
sudo mv dive /usr/local/bin/

# macOS
brew install dive
```

#### Usage

```bash
# Analyze an image
dive mobius-backend:latest

# Build and analyze in one step
dive build -t mobius-backend:latest -f docker/backend/Dockerfile .

# CI mode (non-interactive)
CI=true dive mobius-backend:latest
```

### 4. Docker Bench Security

Checks for common security issues in Docker deployments.

```bash
# Run security benchmark
docker run --rm -it \
  --net host \
  --pid host \
  --userns host \
  --cap-add audit_control \
  -v /etc:/etc:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro \
  -v /usr/lib/systemd:/usr/lib/systemd:ro \
  -v /var/lib:/var/lib:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  docker/docker-bench-security
```

## Integration Strategies

### 1. Git Hooks (Manual Setup)

For teams that want to enforce linting on commit, you can set up Git hooks
manually:

```bash
# Create a pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Run Docker linting before commit

echo "Running Docker linting..."

# Check if hadolint is installed
if command -v hadolint >/dev/null 2>&1; then
    hadolint --config .hadolint.yaml docker/backend/Dockerfile
    hadolint --config .hadolint.yaml docker/frontend/Dockerfile.dev
else
    echo "Warning: hadolint not installed. Skipping Dockerfile linting."
fi

# Validate Docker Compose files
docker-compose -f docker-compose.yml config > /dev/null || exit 1
docker-compose -f docker-compose.prod.yml config > /dev/null || exit 1

echo "Docker linting passed!"
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit
```

### 2. VSCode Extensions

Add to `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "exiasr.hadolint",
    "ms-azuretools.vscode-docker",
    "redhat.vscode-yaml",
    "timonwong.shellcheck"
  ]
}
```

VSCode settings (`.vscode/settings.json`):

```json
{
  "hadolint.hadolintPath": "/usr/local/bin/hadolint",
  "hadolint.customRules": ".hadolint.yaml",
  "docker.images.label": "Tag",
  "docker.images.sortBy": "CreatedTime",
  "yaml.schemas": {
    "https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json": "docker-compose*.yml"
  }
}
```

### 3. CI/CD Integration

#### GitHub Actions

Create `.github/workflows/docker-lint.yml`:

```yaml
name: Docker Linting

on:
  pull_request:
    paths:
      - 'docker/**'
      - 'docker-compose*.yml'
      - '.dockerignore'

jobs:
  hadolint:
    name: Hadolint Dockerfile Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Hadolint
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: docker/backend/Dockerfile
          config: .hadolint.yaml

      - name: Run Hadolint on Frontend Dockerfile
        uses: hadolint/hadolint-action@v3.1.0
        with:
          dockerfile: docker/frontend/Dockerfile.dev
          config: .hadolint.yaml

  docker-compose-lint:
    name: Docker Compose Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate Docker Compose files
        run: |
          docker-compose -f docker-compose.yml config > /dev/null
          docker-compose -f docker-compose.prod.yml config > /dev/null

  dive-analysis:
    name: Dive Image Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Backend Image
        run: docker build -f docker/backend/Dockerfile -t mobius-backend:ci .

      - name: Run Dive
        uses: yuichielectric/dive-action@0.0.4
        with:
          image: 'mobius-backend:ci'
          config: '.dive-ci.yaml'
```

#### Dive CI Configuration

Create `.dive-ci.yaml`:

```yaml
# .dive-ci.yaml
rules:
  # Fail if efficiency is below threshold
  lowestEfficiency: 0.90

  # Fail if waste exceeds threshold
  highestWasteBytes: 20MB
  highestUserWastedPercent: 0.10

  # Image size limits
  imageSizeLimit: 500MB
```

### 4. Make Targets

Add to existing `Makefile`:

```makefile
# Docker Linting Targets
.PHONY: lint-docker lint-compose lint-images install-lint-tools

# Install linting tools
install-lint-tools:
	@echo "Installing Docker linting tools..."
	@wget -O /tmp/hadolint https://github.com/hadolint/hadolint/releases/download/v2.12.0/hadolint-Linux-x86_64
	@chmod +x /tmp/hadolint
	@sudo mv /tmp/hadolint /usr/local/bin/hadolint || mv /tmp/hadolint ~/.local/bin/hadolint
	@echo "Docker linting tools installed successfully"

# Lint Dockerfiles
lint-docker:
	@echo "Linting Dockerfiles..."
	@hadolint docker/backend/Dockerfile
	@hadolint docker/frontend/Dockerfile.dev
	@echo "Dockerfile linting passed"

# Validate Docker Compose files
lint-compose:
	@echo "Validating Docker Compose files..."
	@docker-compose -f docker-compose.yml config > /dev/null
	@docker-compose -f docker-compose.prod.yml config > /dev/null
	@echo "Docker Compose validation passed"

# Analyze Docker images
lint-images: build
	@echo "Analyzing Docker images with dive..."
	@dive mobius-backend:latest --ci --config .dive-ci.yaml
	@dive mobius-frontend:latest --ci --config .dive-ci.yaml

# Run all Docker lints
lint-all-docker: lint-docker lint-compose
	@echo "All Docker linting passed"

# Add to existing lint target
lint: lint-python lint-all-docker
```

## Mobius-Specific Configuration

### Hadolint Rules for Mobius

Based on the Mobius architecture, here are recommended Hadolint rules:

```yaml
# .hadolint.yaml - Mobius specific
ignored:
  # Allow apt-get without version pinning during development
  - DL3008

# Enforce security best practices
overrides:
  - id: DL3002
    severity: error # Last user should not be root
  - id: DL3003
    severity: error # Use WORKDIR instead of cd
  - id: DL3004
    severity: error # Do not use sudo
  - id: DL3025
    severity: error # Use --no-cache-dir with pip
  - id: DL3013
    severity: warning # Pin versions in pip
  - id: DL3018
    severity: warning # Pin versions in apk add
  - id: DL3047
    severity: warning # Use COPY instead of ADD for files

# Mobius-specific labels
label-schema:
  maintainer: required
  version: required
  description: required
  mobius.component: required # backend, frontend, etc.
  mobius.tier: required # api, web, worker, etc.
```

### Docker Compose Best Practices for Mobius

1. **Service Naming Convention**:

   ```yaml
   services:
     mobius-backend: # Use mobius- prefix
     mobius-frontend:
     mobius-redis:
     mobius-postgres:
   ```

2. **Network Segmentation**:

   ```yaml
   networks:
     mobius-frontend: # Frontend network
     mobius-backend: # Backend network
     mobius-data: # Database network
   ```

3. **Resource Limits** (for production):
   ```yaml
   services:
     mobius-backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
           reservations:
             cpus: '1'
             memory: 2G
   ```

### Security Scanning Integration

Add to `Makefile`:

```makefile
# Security scanning
security-scan-docker:
	@echo "Running Docker security scan..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image mobius-backend:latest
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image mobius-frontend:latest
```

## Quick Start Commands

```bash
# Install all linting tools
make install-lint-tools

# Run all Docker lints
make lint-all-docker

# Run specific lints
make lint-docker      # Lint Dockerfiles only
make lint-compose     # Lint docker-compose files only
make lint-images      # Analyze image layers

# Run security scan
make security-scan-docker

# Auto-fix some issues
hadolint --fix docker/backend/Dockerfile
```

## Troubleshooting

### Common Hadolint Issues

1. **DL3008 - Pin versions in apt-get**

   ```dockerfile
   # Bad
   RUN apt-get update && apt-get install -y python3

   # Good
   RUN apt-get update && apt-get install -y python3=3.11.* \
       && rm -rf /var/lib/apt/lists/*
   ```

2. **DL3003 - Use WORKDIR**

   ```dockerfile
   # Bad
   RUN cd /app && pip install -r requirements.txt

   # Good
   WORKDIR /app
   RUN pip install -r requirements.txt
   ```

3. **DL3025 - Use --no-cache-dir with pip**

   ```dockerfile
   # Bad
   RUN pip install -r requirements.txt

   # Good
   RUN pip install --no-cache-dir -r requirements.txt
   ```

### Docker Compose Validation Errors

1. **Invalid service name**:
   - Ensure service names match pattern: `[a-zA-Z0-9._-]+`

2. **Duplicate mount points**:
   - Check for conflicting volume mounts

3. **Missing environment variables**:
   - Ensure all referenced env vars are defined

## Next Steps

1. Install the linting tools: `make install-lint-tools`
2. Run initial lint check: `make lint-all-docker`
3. Fix any issues found
4. Configure your IDE with recommended extensions
5. Set up CI/CD workflows for automated checks

This guide ensures consistent, secure, and optimized Docker configurations
across the Mobius platform, aligning with the project's high standards for code
quality and security.
