# Mobius Platform Tooling Guide

This guide provides a comprehensive overview of the key configuration files and tools used in the Mobius Context Engineering Platform. Understanding these files will help developers work efficiently within the project's established conventions and workflows.

## Configuration Files Overview

### .editorconfig - Editor Settings Consistency

**Purpose:** Ensures consistent coding styles across different editors and IDEs used by team members.

**Location:** `.editorconfig` (project root)

**Key Settings:**
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space

[*.{py,pyi}]
indent_size = 4

[*.{js,jsx,ts,tsx,json,yml,yaml}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

**How Developers Interact:**
- Most modern editors (VSCode, JetBrains IDEs, Vim, etc.) automatically detect and apply these settings
- No manual action required - just ensure your editor has EditorConfig support enabled
- Settings apply automatically when you open files in the project

**Important Notes:**
- These settings override your personal editor preferences within this project
- Ensures consistent line endings (LF) across all platforms
- Python files use 4-space indentation, while JavaScript/TypeScript use 2-space indentation

---

### .prettierrc.json - Code Formatting for JavaScript/TypeScript

**Purpose:** Automatically formats JavaScript, TypeScript, JSON, and other supported file types to maintain consistent code style.

**Location:** `.prettierrc.json` (project root)

**Key Settings:**
```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

**How Developers Interact:**
- **Format on save:** Configure your editor to run Prettier automatically
- **Manual formatting:** `npm run format` in the frontend directory
- **Check formatting:** `npm run format:check` to verify without changing files
- **Pre-commit hook:** Prettier runs automatically before commits via Husky

**Important Notes:**
- Prettier is opinionated - it will override personal style preferences
- Works alongside ESLint but handles different concerns (formatting vs. code quality)
- Integrates with most editors via extensions (Prettier extension for VSCode)

---

### frontend/.eslintrc.json - JavaScript/TypeScript Linting

**Purpose:** Catches potential errors, enforces coding standards, and maintains code quality in JavaScript/TypeScript files.

**Location:** `frontend/.eslintrc.json`

**Key Sections:**
```json
{
  "extends": [
    "react-app",
    "react-app/jest",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "rules": {
    "@typescript-eslint/explicit-module-boundary-types": "warn",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

**How Developers Interact:**
- **Real-time linting:** Install ESLint extension in your editor for inline warnings
- **Manual check:** `npm run lint` in the frontend directory
- **Auto-fix issues:** `npm run lint:fix` to automatically fix fixable problems
- **Pre-commit validation:** ESLint runs automatically before commits

**Important Notes:**
- ESLint focuses on code quality and potential bugs, not formatting
- The `prettier` config ensures ESLint doesn't conflict with Prettier formatting
- Custom rules can be added to enforce project-specific standards

---

### pyproject.toml - Python Project Configuration

**Purpose:** Central configuration file for Python tooling, dependencies, and project metadata.

**Location:** `pyproject.toml` (project root)

**Key Sections:**

1. **Project Metadata:**
```toml
[tool.poetry]
name = "mobius"
version = "0.1.0"
description = "Context Engineering Platform for AI Coding Assistants"
authors = ["Your Name <email@example.com>"]
```

2. **Dependencies:**
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
pydantic = "^2.4.0"
sqlalchemy = "^2.0.0"
qdrant-client = "^1.6.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.5.0"
```

3. **Tool Configurations:**
```toml
[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "UP", "S", "B", "A", "C4", "PT"]

[tool.mypy]
python_version = "3.11"
strict = true
```

**How Developers Interact:**
- **Install dependencies:** `poetry install`
- **Add new dependencies:** `poetry add package-name`
- **Add dev dependencies:** `poetry add --group dev package-name`
- **Update dependencies:** `poetry update`
- **Run tools:** `poetry run black .`, `poetry run ruff check .`, etc.

**Important Notes:**
- Poetry manages virtual environments automatically
- Lock file (`poetry.lock`) ensures reproducible builds
- Tool configurations keep Python tooling centralized

---

### frontend/package.json - Node.js Dependencies and Scripts

**Purpose:** Manages JavaScript dependencies and defines npm scripts for the frontend application.

**Location:** `frontend/package.json`

**Key Sections:**

1. **Dependencies:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "typescript": "^5.0.0",
    "@reduxjs/toolkit": "^1.9.0",
    "axios": "^1.5.0"
  }
}
```

2. **Scripts:**
```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "lint": "eslint src --ext .ts,.tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx,json,css}\""
  }
}
```

**How Developers Interact:**
- **Install dependencies:** `npm install` or `yarn install`
- **Run development server:** `npm start`
- **Build for production:** `npm run build`
- **Run tests:** `npm test`
- **Add dependencies:** `npm install --save package-name`

**Important Notes:**
- `package-lock.json` ensures consistent dependency versions
- Scripts provide shortcuts for common development tasks
- Can be extended with custom scripts for project-specific needs

---

### docker-compose.yml - Local Development Environment

**Purpose:** Orchestrates multi-container development environment with all required services.

**Location:** `docker-compose.yml` (project root)

**Key Services:**
```yaml
services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/mobius
    depends_on:
      - postgres
      - redis
      - qdrant

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: mobius
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  redis:
    image: redis:7-alpine

  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
```

**How Developers Interact:**
- **Start all services:** `docker-compose up`
- **Start in background:** `docker-compose up -d`
- **Stop services:** `docker-compose down`
- **View logs:** `docker-compose logs -f [service-name]`
- **Rebuild containers:** `docker-compose build`

**Important Notes:**
- Provides consistent development environment across all machines
- Data volumes persist between restarts unless explicitly removed
- Environment variables can be customized via `.env` file
- Services are networked together automatically

---

### Makefile - Development Workflow Automation

**Purpose:** Provides simple commands for common development tasks and complex workflows.

**Location:** `Makefile` (project root)

**Key Targets:**
```makefile
# Development
dev:
	docker-compose up

# Testing
test:
	poetry run pytest
	cd frontend && npm test

# Linting and Formatting
lint:
	poetry run ruff check .
	poetry run mypy .
	cd frontend && npm run lint

format:
	poetry run black .
	poetry run ruff check --fix .
	cd frontend && npm run format

# Database
migrate:
	poetry run alembic upgrade head

# Clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	docker-compose down -v
```

**How Developers Interact:**
- **Run target:** `make [target-name]`
- **View available targets:** `make help` (if implemented) or read the Makefile
- **Chain targets:** `make lint test`
- **Common workflows:** `make dev` for development, `make test` for testing

**Important Notes:**
- Simplifies complex multi-step processes into single commands
- Ensures consistency in how tasks are performed
- Tab characters are required for indentation (not spaces)
- Can include dependencies between targets

---

## Best Practices

1. **Keep configurations in sync:** When updating tool versions or settings, ensure all related configs are updated
2. **Document custom settings:** Add comments in configuration files to explain non-obvious choices
3. **Version control:** All these files should be committed to version control
4. **Local overrides:** Use `.env` files or local config files (usually git-ignored) for personal settings
5. **Regular updates:** Periodically update tool versions and configurations to benefit from improvements

## Tool Integration Workflow

1. **Initial Setup:**
   ```bash
   # Install Python dependencies
   poetry install

   # Install Node dependencies
   cd frontend && npm install

   # Start development environment
   make dev
   ```

2. **Development Cycle:**
   - Code changes trigger editor formatting (EditorConfig)
   - Save triggers Prettier formatting (if configured)
   - ESLint/Ruff provide real-time feedback
   - Pre-commit hooks validate before commits

3. **Testing and Validation:**
   ```bash
   # Run all checks
   make lint test

   # Fix issues
   make format
   ```

This tooling ecosystem is designed to maintain code quality, ensure consistency, and streamline the development workflow across the entire Mobius platform.
