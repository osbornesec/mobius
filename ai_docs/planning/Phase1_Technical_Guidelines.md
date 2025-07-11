# Phase 1 Technical Guidelines - Mobius Context Engineering Platform

## Document Version: 1.0
## Date: 2025-01-07
## Purpose: Definitive technical reference for all Phase 1 development

---

## Executive Summary

This document outlines the core technical standards and architectural principles for Phase 1 of the Mobius Context Engineering Platform. Adherence to these guidelines is essential for building a scalable, maintainable, and secure system. This summary serves as a quick reference; please consult the full document for detailed specifications.

### Guiding Philosophy & Core Principles

Our approach is centered on **velocity, stability, and developer autonomy**. We achieve this through a loosely coupled microservices architecture where teams can build, test, and deploy their services independently.

- **API-First Design:** Services communicate exclusively through well-defined, versioned RESTful APIs. The OpenAPI specification is the source of truth for all inter-service communication.
- **Stateless Services:** Services must be stateless. All persistent state is delegated to dedicated data stores (PostgreSQL, Qdrant) and caches (Redis).
- **Clear Ownership & Boundaries:** Each microservice has a single, unambiguous purpose and is owned by a specific team.
- **Automate Everything:** We rely on robust CI/CD pipelines for automated testing, security scanning, and deployment to ensure reliability and speed.
- **Secure by Design:** Security is a foundational, non-negotiable requirement integrated into every stage of the development lifecycle.

### Technology Stack At-a-Glance

| Component | Technology/Standard | Key Usage |
|-----------|-------------------|-----------|
| **Backend** | Python 3.11+ / FastAPI | Core service logic, API implementation |
| **Frontend** | TypeScript | Type-safe user interface development |
| **API Specification** | OpenAPI 3.x | Contract for all APIs |
| **Primary Datastore** | PostgreSQL 15+ (with pgvector) | Relational data, transactional workloads |
| **Vector Datastore** | Qdrant | High-performance semantic search |
| **Caching & Queues** | Redis | Caching, rate limiting, simple message queuing |
| **VCS & Workflow** | Git / GitFlow | Source control and branching strategy |
| **Observability** | Structured Logging (JSON) | Centralized, queryable logs |

### Critical Mandates: The Non-Negotiables

While the full guidelines are extensive, the following are the most critical for project success. Non-compliance with these points will block deployment.

1. **Structured JSON Logging:** All log output **must** be in a structured JSON format. This is vital for effective monitoring and debugging in our distributed environment.
2. **Centralized Error Handling:** Use the provided FastAPI middleware for handling exceptions. This ensures all services return consistent, predictable error responses.
3. **Configuration via Environment:** All configuration, especially secrets and environment-specific settings, **must** be loaded from environment variables. No hardcoding is permitted.
4. **Comprehensive Testing:** A minimum of **80% unit test coverage** is required. Critical user flows must also be covered by integration and/or end-to-end tests.
5. **Asynchronous I/O:** All network and database I/O operations **must** be implemented using `async`/`await` to ensure non-blocking performance.

### Development Team Checklist

Use this checklist to validate your service before submitting a merge request for review.

**Service Design & Setup**
- [ ] Service responsibilities are clearly defined and documented in the `README.md`
- [ ] API contract is defined in an `openapi.json` file (leverage FastAPI's auto-generation)
- [ ] All dependencies are declared in `pyproject.toml` with pinned versions

**Code Implementation**
- [ ] Code is formatted with `black` and passes `ruff` checks
- [ ] All configuration and secrets are loaded from the environment (12-Factor compliant)
- [ ] Structured JSON logging is implemented for all operations
- [ ] `async/await` is used for all I/O-bound calls
- [ ] Standard error handling middleware is correctly implemented

**Testing & Validation**
- [ ] Unit tests achieve >80% code coverage on new code
- [ ] Integration tests exist for database interactions and external API calls
- [ ] The full test suite passes in the CI pipeline

**Pre-Deployment**
- [ ] The `README.md` is updated with setup instructions and API usage examples
- [ ] API documentation is generated, accurate, and accessible
- [ ] Security best practices (e.g., input validation, auth checks) are implemented
- [ ] Monitoring hooks (e.g., Prometheus endpoints) are exposed

---

## Table of Contents

1. [Development Standards](#1-development-standards)
2. [Architecture Guidelines](#2-architecture-guidelines)
3. [Technology Stack Details](#3-technology-stack-details)
4. [API Specifications](#4-api-specifications)
5. [Database Design Guidelines](#5-database-design-guidelines)
6. [Security Implementation](#6-security-implementation)
7. [Testing Requirements](#7-testing-requirements)
8. [Performance Standards](#8-performance-standards)
9. [Documentation Standards](#9-documentation-standards)
10. [Development Workflow](#10-development-workflow)
11. [Monitoring and Observability](#11-monitoring-and-observability)
12. [Best Practices](#12-best-practices)

---

## 1. Development Standards

### 1.1 Python Coding Standards

#### General Code Style (PEP 8 & Black)
We adhere to PEP 8 as the baseline for all Python code. To ensure consistency and eliminate debates over formatting, we use `black` as our auto-formatter.

- **Line Length:** 88 characters (Black default)
- **Indentation:** 4 spaces
- **Tooling:** Use `ruff` for linting and `black` for formatting
- **Naming Conventions:**
  - `snake_case` for variables, functions, and modules
  - `PascalCase` for classes (including Pydantic models)
  - `UPPER_SNAKE_CASE` for constants

#### Type Hinting Best Practices (Python 3.11+)
Modern type hints are essential for clarity and for leveraging FastAPI's validation and serialization capabilities.

- **Prefer Built-in Generics:** Use `list[str]` and `dict[str, int]` instead of `typing.List` and `typing.Dict`
- **Use the `|` Union Operator:** Prefer `str | None` over `typing.Union[str, None]` or `typing.Optional[str]`
- **Use `Annotated` for Metadata:** For path/query/body parameters, use `typing.Annotated` to separate the type hint from the validation logic

```python
from typing import Annotated
from fastapi import FastAPI, Path, Query

app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(
    item_id: Annotated[int, Path(title="The ID of the item to get", ge=1)],
    q: Annotated[str | None, Query(max_length=50)] = None,
):
    results = {"item_id": item_id}
    if q:
        results.update({"q": q})
    return results
```

#### Async/Await Patterns
Correctly using `async`/`await` is critical for performance.

- **Use `async def` for I/O-bound operations:** Database calls, external API requests, file I/O
- **Use standard `def` for CPU-bound operations:** Pure computation without waiting
- **Integrating Synchronous Code:** Run blocking I/O in FastAPI's thread pool

```python
from fastapi.concurrency import run_in_threadpool
import some_blocking_io_library

async def my_async_endpoint():
    # Run blocking I/O in a separate thread
    result = await run_in_threadpool(some_blocking_io_library.call, arg1, kwarg="value")
    return {"result": result}
```

#### Pydantic Model Best Practices
Pydantic models are the data interface layer of the application.

- **Separate Models for Input and Output:** Never reuse the same model for requests and responses
- **Clear Naming Convention:**
  - `ModelNameBase`: Common fields shared across all models
  - `ModelNameCreate`: For creation (request body)
  - `ModelNameUpdate`: For updates (all fields optional)
  - `ModelNameRead`: For responses (includes generated fields)
- **Enable `from_attributes` for ORM Mapping**

```python
from pydantic import BaseModel, ConfigDict, Field

# Base model with shared fields
class ItemBase(BaseModel):
    name: str = Field(min_length=3)
    description: str | None = None

# Model for creating an item (input)
class ItemCreate(ItemBase):
    pass

# Model for reading an item (output)
class ItemRead(ItemBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
```

#### Dependency Injection Patterns
FastAPI's DI system should be used for managing resources and cross-cutting concerns.

- **Centralize Dependencies:** Place common dependencies in `app/dependencies.py`
- **Use `yield` for Setup and Teardown:** For resources that need cleanup

```python
from typing import Generator
from .database import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Error Handling Standards
Standardized error handling makes the API predictable and robust.

- **Decouple Business Logic from HTTP:** Service layer should raise domain-specific exceptions
- **Use Custom Exception Handlers:** Translate business exceptions to HTTP responses

```python
# Custom exception (app/exceptions.py)
class ItemNotFoundError(Exception):
    def __init__(self, item_id: int):
        self.item_id = item_id

# Service layer raises it
def get_item_by_id(db: Session, item_id: int) -> models.Item:
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise exceptions.ItemNotFoundError(item_id=item_id)
    return item

# Application handles it (app/main.py)
@app.exception_handler(exceptions.ItemNotFoundError)
async def item_not_found_exception_handler(request: Request, exc: exceptions.ItemNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"message": f"Item with ID {exc.item_id} not found"},
    )
```

#### Import Organization
Consistent import order improves readability. Use `isort` or `ruff` to enforce this automatically.

1. Standard Library (e.g., `os`, `sys`, `typing`)
2. Third-Party Libraries (e.g., `fastapi`, `pydantic`, `sqlalchemy`)
3. First-Party/Local Application Imports (e.g., `from . import models`)

```python
# Standard Library
from typing import List

# Third-Party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Local Application
from .. import dependencies, schemas, services
from ..exceptions import ItemNotFoundError
```

### 1.2 TypeScript/JavaScript Standards

#### TypeScript Configuration
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "lib": ["ES2022"],
    "outDir": "./out",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

#### Coding Standards
- Use 2 spaces for indentation
- Use camelCase for functions and variables
- Use PascalCase for classes and types
- Use UPPER_CASE for constants
- Always use explicit types (avoid `any`)
- Prefer `const` over `let`
- Use async/await over promises

### 1.3 API Design Principles

#### RESTful Conventions
- Use nouns for resources: `/api/v1/projects`
- Use HTTP verbs appropriately:
  - GET: Read operations
  - POST: Create operations
  - PUT: Full updates
  - PATCH: Partial updates
  - DELETE: Remove operations

#### Async Patterns
- All endpoints should be async
- Use background tasks for long-running operations
- Implement proper timeout handling
- Return 202 Accepted for async operations

### 1.4 Database Conventions

#### Naming Conventions
- Tables: plural snake_case (e.g., `projects`, `context_chunks`)
- Columns: snake_case (e.g., `created_at`, `is_active`)
- Indexes: `idx_<table>_<columns>` (e.g., `idx_projects_user_id`)
- Foreign keys: `fk_<table>_<referenced_table>` (e.g., `fk_contexts_projects`)

#### Best Practices
- Always use UUID for primary keys
- Include `created_at` and `updated_at` timestamps
- Use soft deletes with `deleted_at` field
- Add database-level constraints

### 1.5 Git Workflow and Branching Strategy

#### Branch Naming
- Feature branches: `feature/<ticket-id>-<description>`
- Bug fixes: `fix/<ticket-id>-<description>`
- Hotfixes: `hotfix/<ticket-id>-<description>`
- Release branches: `release/<version>`

#### Commit Messages
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

#### Git Flow
1. Create feature branch from `develop`
2. Make atomic commits
3. Push branch and create PR
4. Code review required (min 1 approval)
5. Merge to `develop` after CI passes
6. Deploy to staging from `develop`
7. Create release branch for production

---

## 2. Architecture Guidelines

### 2.1 Microservices Boundaries

#### Service Separation
- **Context Service**: Handles all context operations
- **Project Service**: Manages projects and workspaces
- **Search Service**: Dedicated search functionality
- **Auth Service**: Authentication and authorization
- **Gateway Service**: API gateway and routing

#### Service Communication
- Internal: gRPC for service-to-service
- External: REST APIs through gateway
- Async: Redis pub/sub for events
- Message Queue: Redis Streams for job processing

### 2.2 Data Flow Architecture

#### Request Flow
```
Client → API Gateway → Load Balancer → Service → Database
                                    ↓
                              Background Jobs → Redis Queue
```

#### Context Processing Flow
```
File Upload → Parser → Chunker → Embedder → Vector Store
                                          ↓
                                    Metadata Store
```

### 2.3 Error Handling Strategies

#### Error Categories
1. **Client Errors (4xx)**
   - 400: Bad Request - Invalid input
   - 401: Unauthorized - Missing/invalid auth
   - 403: Forbidden - Insufficient permissions
   - 404: Not Found - Resource doesn't exist
   - 422: Unprocessable Entity - Validation errors

2. **Server Errors (5xx)**
   - 500: Internal Server Error - Unexpected errors
   - 502: Bad Gateway - Service unavailable
   - 503: Service Unavailable - Maintenance/overload
   - 504: Gateway Timeout - Request timeout

#### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "request_id": "uuid-v4",
    "timestamp": "2025-01-07T10:00:00Z"
  }
}
```

### 2.4 Logging and Monitoring Standards

#### Log Levels
- DEBUG: Detailed debugging information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical issues requiring immediate attention

#### Structured Logging
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "context_processed",
    project_id=project_id,
    context_id=context_id,
    processing_time=processing_time,
    chunk_count=chunk_count
)
```

---

## 3. Technology Stack Details

### 3.1 Version Requirements

#### Core Dependencies
- Python: 3.11.x (minimum 3.11.5)
- Node.js: 20.x LTS
- PostgreSQL: 15.x
- Redis: 7.2.x
- Docker: 24.x
- Docker Compose: 2.23.x

#### Python Libraries
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
pydantic = "^2.5.0"
sqlalchemy = "^2.0.23"
asyncpg = "^0.29.0"
redis = "^5.0.1"
qdrant-client = "^1.7.0"
openai = "^1.6.0"
structlog = "^23.2.0"
httpx = "^0.25.2"
```

#### TypeScript/VSCode Extension
```json
{
  "devDependencies": {
    "@types/vscode": "^1.85.0",
    "@typescript-eslint/eslint-plugin": "^6.15.0",
    "@typescript-eslint/parser": "^6.15.0",
    "eslint": "^8.56.0",
    "typescript": "^5.3.3"
  }
}
```

### 3.2 Configuration Management

#### Environment Variables
```bash
# Application
APP_NAME=mobius
APP_ENV=development|staging|production
APP_VERSION=1.0.0
LOG_LEVEL=INFO

# API
MOBIUS_HOST=0.0.0.0
MOBIUS_PORT=8000
API_PREFIX=/api/v1

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mobius
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=10

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key

# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=text-embedding-3-small

# Security
SECRET_KEY=your-secret-key
API_KEY_HEADER=X-API-Key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400
```

### 3.3 Docker Container Specifications

#### Base Dockerfile
```dockerfile
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.0

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application
COPY . .

# Production stage
FROM base as production

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.4 Development Tool Requirements

#### Required Tools
- Poetry: Python dependency management
- Black: Python code formatter
- Ruff: Python linter
- mypy: Static type checker
- pytest: Testing framework
- pre-commit: Git hooks
- ESLint: TypeScript linter
- Prettier: TypeScript formatter

#### Pre-commit Configuration
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

---

## 4. API Specifications

### 4.1 Endpoint Naming Conventions

#### Resource Naming
- Use plural nouns: `/projects`, `/contexts`, `/embeddings`
- Use kebab-case for multi-word resources: `/context-chunks`
- Nested resources: `/projects/{project_id}/contexts`
- Actions as sub-resources: `/contexts/{id}/process`

### 4.2 Request/Response Formats

#### Standard Request Headers
```http
Content-Type: application/json
Accept: application/json
X-API-Key: <api-key>
X-Request-ID: <uuid>
```

#### Pagination Parameters
```
GET /api/v1/contexts?page=1&limit=20&sort=created_at&order=desc
```

#### Standard Response Structure
```json
{
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "limit": 20
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2025-01-07T10:00:00Z",
    "version": "1.0.0"
  }
}
```

### 4.3 Error Response Standards

#### Error Response Structure
```json
{
  "error": {
    "type": "ValidationError",
    "code": "INVALID_INPUT",
    "message": "The provided input is invalid",
    "details": {
      "fields": {
        "email": ["Invalid email format"],
        "name": ["Required field"]
      }
    },
    "trace_id": "uuid",
    "documentation_url": "https://docs.mobius.ai/errors/INVALID_INPUT"
  }
}
```

### 4.4 Versioning Strategy

#### URL Versioning
- Version in URL path: `/api/v1/`, `/api/v2/`
- Maintain backward compatibility for 2 versions
- Deprecation notices in headers:
  ```http
  X-API-Deprecation: true
  X-API-Deprecation-Date: 2025-06-01
  X-API-Deprecation-Info: https://docs.mobius.ai/deprecation/v1
  ```

### 4.5 Authentication/Authorization Patterns

#### API Key Authentication
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not await validate_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key
```

#### JWT Token Pattern
```python
@router.post("/auth/login")
async def login(credentials: LoginCredentials):
    user = await authenticate_user(credentials)
    access_token = create_access_token(user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 86400
    }
```

---

## 5. Database Design Guidelines

### 5.1 PostgreSQL Schema Conventions

#### Schema Organization
```sql
-- Core schemas
CREATE SCHEMA IF NOT EXISTS core;      -- Core business entities
CREATE SCHEMA IF NOT EXISTS auth;      -- Authentication/authorization
CREATE SCHEMA IF NOT EXISTS audit;     -- Audit logs

-- Grant permissions
GRANT USAGE ON SCHEMA core TO mobius_app;
GRANT CREATE ON SCHEMA core TO mobius_app;
```

#### Table Structure Template
```sql
CREATE TABLE core.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id UUID NOT NULL,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ,

    CONSTRAINT fk_projects_users
        FOREIGN KEY (user_id)
        REFERENCES auth.users(id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_projects_user_id ON core.projects(user_id);
CREATE INDEX idx_projects_created_at ON core.projects(created_at DESC);
CREATE INDEX idx_projects_deleted_at ON core.projects(deleted_at) WHERE deleted_at IS NULL;

-- Triggers
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON core.projects
    FOR EACH ROW
    EXECUTE FUNCTION core.update_updated_at_column();
```

#### PostgreSQL with pgvector Best Practices

##### Vector Storage Schema
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Document storage with vectors
CREATE TABLE core.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES core.projects(id),
    content TEXT NOT NULL,
    metadata JSONB,                    -- Flexible metadata storage
    embedding vector(1536),            -- OpenAI ada-002 dimensions
    tenant_id UUID NOT NULL,           -- For multi-tenancy
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Structured columns for frequent filters
    is_active BOOLEAN DEFAULT true,
    document_type VARCHAR(50),

    CONSTRAINT fk_documents_projects
        FOREIGN KEY (project_id)
        REFERENCES core.projects(id)
        ON DELETE CASCADE
);
```

##### Indexing Strategy for Hybrid Search
```sql
-- HNSW index for vector similarity (recommended for pgvector 0.6.0+)
-- Better performance than IVFFlat for most use cases
CREATE INDEX idx_documents_embedding_hnsw
ON core.documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Alternative: IVFFlat index (for faster build times)
-- Lists should be ~sqrt(n) for up to 1M rows
-- CREATE INDEX idx_documents_embedding_ivfflat
-- ON core.documents
-- USING ivfflat (embedding vector_cosine_ops)
-- WITH (lists = 100);

-- GIN index for JSONB metadata queries
CREATE INDEX idx_documents_metadata
ON core.documents
USING gin (metadata);

-- B-tree indexes for structured filters
CREATE INDEX idx_documents_tenant_id ON core.documents(tenant_id);
CREATE INDEX idx_documents_project_id ON core.documents(project_id);
CREATE INDEX idx_documents_type ON core.documents(document_type);
```

##### Performance Tuning
```sql
-- PostgreSQL configuration for vector operations
-- Add to postgresql.conf or set at session level

-- Increase work memory for vector operations
ALTER SYSTEM SET work_mem = '256MB';

-- For index creation
ALTER SYSTEM SET maintenance_work_mem = '2GB';

-- Shared buffers (25% of system RAM)
ALTER SYSTEM SET shared_buffers = '8GB';

-- Reload configuration
SELECT pg_reload_conf();
```

##### Partitioning for Scale
```sql
-- Partition by tenant for multi-tenant applications
CREATE TABLE core.documents_partitioned (
    id UUID DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    tenant_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, tenant_id)
) PARTITION BY LIST (tenant_id);

-- Create partitions per tenant
CREATE TABLE core.documents_tenant_a
PARTITION OF core.documents_partitioned
FOR VALUES IN ('11111111-1111-1111-1111-111111111111');

-- Remember to create indexes on each partition
```

### 5.2 Qdrant Collection Structure

#### Production Collection Configuration
```python
from qdrant_client import QdrantClient, models

client = QdrantClient(host="localhost", port=6333)

# Production-optimized collection
client.recreate_collection(
    collection_name="production_contexts",
    vectors_config=models.VectorParams(
        size=1536,  # OpenAI text-embedding-3-small
        distance=models.Distance.COSINE
    ),
    # HNSW configuration for optimal search performance
    hnsw_config=models.HnswConfigDiff(
        m=16,                # Connections per layer (16-32 recommended)
        ef_construct=100,    # Build quality (higher = better quality, slower build)
        full_scan_threshold=10000
    ),
    # Enable quantization for memory optimization
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            quantile=0.99,
            always_ram=True  # Keep quantized vectors in RAM
        ),
    ),
    # Storage optimization
    on_disk_payload=True,  # Store payload on disk to save RAM
    optimizers_config=models.OptimizersConfigDiff(
        deleted_threshold=0.2,
        vacuum_min_vector_number=1000,
        default_segment_number=4,
        memmap_threshold=20000,
        indexing_threshold=20000
    )
)
```

#### Payload Indexing for Fast Filtering
```python
# Create indexes for frequently filtered fields
client.create_payload_index(
    collection_name="production_contexts",
    field_name="project_id",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="production_contexts",
    field_name="tenant_id",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="production_contexts",
    field_name="metadata.language",
    field_schema=models.PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="production_contexts",
    field_name="metadata.document_type",
    field_schema=models.PayloadSchemaType.KEYWORD
)
```

#### Optimized Point Structure
```python
from typing import List, Dict, Any
import uuid

def create_point_batch(
    documents: List[Dict[str, Any]],
    embeddings: List[List[float]]
) -> List[models.PointStruct]:
    """Create batch of points for efficient upsert"""
    return [
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "project_id": doc["project_id"],
                "tenant_id": doc["tenant_id"],
                "context_id": doc["context_id"],
                "chunk_id": doc["chunk_id"],
                "content": doc["content"],
                "metadata": {
                    "file_path": doc["file_path"],
                    "language": doc["language"],
                    "document_type": doc["document_type"],
                    "chunk_index": doc["chunk_index"],
                    "total_chunks": doc["total_chunks"],
                    "tokens": doc["token_count"]
                },
                "timestamps": {
                    "created_at": doc["created_at"],
                    "indexed_at": datetime.utcnow().isoformat()
                }
            }
        )
        for doc, embedding in zip(documents, embeddings)
    ]

# Batch upsert for performance
points = create_point_batch(documents, embeddings)
client.upsert(
    collection_name="production_contexts",
    points=points,
    wait=False  # Async insertion for better throughput
)
```

#### Hybrid Search Implementation
```python
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

async def hybrid_search(
    query_vector: List[float],
    tenant_id: str,
    filters: Dict[str, Any],
    limit: int = 10,
    score_threshold: float = 0.7
) -> List[models.ScoredPoint]:
    """Perform hybrid vector + metadata search"""

    # Build filter conditions
    must_conditions = [
        FieldCondition(
            key="tenant_id",
            match=MatchValue(value=tenant_id)
        )
    ]

    # Add dynamic filters
    if "language" in filters:
        must_conditions.append(
            FieldCondition(
                key="metadata.language",
                match=MatchValue(value=filters["language"])
            )
        )

    if "min_tokens" in filters:
        must_conditions.append(
            FieldCondition(
                key="metadata.tokens",
                range=Range(gte=filters["min_tokens"])
            )
        )

    # Execute search
    results = await client.search(
        collection_name="production_contexts",
        query_vector=query_vector,
        query_filter=Filter(must=must_conditions),
        limit=limit,
        score_threshold=score_threshold,
        with_payload=True
    )

    return results
```

### 5.3 Redis Key Patterns

#### Key Naming Convention
```
<prefix>:<entity>:<identifier>:<field>
```

Examples:
```
mobius:project:123e4567-e89b-12d3-a456-426614174000:settings
mobius:cache:embeddings:hash(content):vector
mobius:session:user:123:contexts
mobius:ratelimit:api:192.168.1.1:count
```

#### TTL Strategy
```python
# Cache TTLs
EMBEDDING_CACHE_TTL = 86400  # 24 hours
SESSION_TTL = 3600  # 1 hour
RATE_LIMIT_TTL = 60  # 1 minute

# Set with TTL
await redis.setex(
    f"mobius:cache:embeddings:{content_hash}",
    EMBEDDING_CACHE_TTL,
    json.dumps(embedding)
)
```

### 5.4 Data Synchronization Patterns

#### PostgreSQL and Qdrant Sync Strategy
Maintaining consistency between PostgreSQL (source of truth) and Qdrant (vector index) using asynchronous patterns.

##### Message Queue Architecture
```python
# app/core/messaging.py
from typing import Dict, Any
import asyncio
import json
from redis import asyncio as aioredis
from structlog import get_logger

logger = get_logger()

class EmbeddingQueue:
    """Queue for async embedding tasks"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.queue_name = "mobius:embedding:queue"
        self.processing_queue = "mobius:embedding:processing"

    async def connect(self):
        self.redis = await aioredis.from_url(self.redis_url)

    async def enqueue_document(self, document_id: str, priority: int = 0):
        """Add document to embedding queue"""
        task = {
            "document_id": document_id,
            "timestamp": datetime.utcnow().isoformat(),
            "attempts": 0
        }

        # Use sorted set for priority queue
        await self.redis.zadd(
            self.queue_name,
            {json.dumps(task): priority}
        )

        logger.info("document_queued", document_id=document_id)

    async def dequeue_batch(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Get batch of documents to process"""
        # Move items to processing queue atomically
        async with self.redis.pipeline() as pipe:
            # Get highest priority items
            items = await self.redis.zrange(
                self.queue_name, 0, batch_size - 1
            )

            if items:
                # Move to processing queue
                pipe.multi()
                for item in items:
                    pipe.zrem(self.queue_name, item)
                    pipe.sadd(self.processing_queue, item)
                await pipe.execute()

        return [json.loads(item) for item in items]
```

##### Embedding Worker Service
```python
# app/workers/embedding_worker.py
from app.services import EmbeddingService, DocumentService
from app.core.messaging import EmbeddingQueue
from app.db.session import get_async_session
from qdrant_client import AsyncQdrantClient
import asyncio

class EmbeddingWorker:
    """Worker for processing embedding queue"""

    def __init__(
        self,
        queue: EmbeddingQueue,
        embedding_service: EmbeddingService,
        qdrant_client: AsyncQdrantClient
    ):
        self.queue = queue
        self.embedding_service = embedding_service
        self.qdrant = qdrant_client
        self.running = False

    async def process_document(self, document_id: str):
        """Process single document"""
        async with get_async_session() as db:
            # 1. Fetch document from PostgreSQL
            doc_service = DocumentService(db)
            document = await doc_service.get_by_id(document_id)

            if not document:
                logger.warning("document_not_found", document_id=document_id)
                return

            # 2. Generate embedding
            embedding = await self.embedding_service.generate_embedding(
                document.content
            )

            # 3. Update PostgreSQL with embedding
            await doc_service.update_embedding(document_id, embedding)

            # 4. Upsert to Qdrant
            await self.qdrant.upsert(
                collection_name="production_contexts",
                points=[
                    models.PointStruct(
                        id=document_id,
                        vector=embedding,
                        payload={
                            "project_id": str(document.project_id),
                            "tenant_id": str(document.tenant_id),
                            "content": document.content,
                            "metadata": document.metadata
                        }
                    )
                ]
            )

            logger.info("document_embedded", document_id=document_id)

    async def run(self):
        """Main worker loop"""
        self.running = True

        while self.running:
            try:
                # Get batch of documents
                batch = await self.queue.dequeue_batch(batch_size=10)

                if not batch:
                    # No work, sleep briefly
                    await asyncio.sleep(1)
                    continue

                # Process batch concurrently
                tasks = [
                    self.process_document(task["document_id"])
                    for task in batch
                ]

                await asyncio.gather(*tasks, return_exceptions=True)

            except Exception as e:
                logger.error("worker_error", error=str(e))
                await asyncio.sleep(5)  # Back off on error
```

##### Reconciliation Service
```python
# app/services/reconciliation.py
from datetime import datetime, timedelta
from typing import Set

class ReconciliationService:
    """Ensure PostgreSQL and Qdrant stay in sync"""

    def __init__(self, db_session, qdrant_client, queue):
        self.db = db_session
        self.qdrant = qdrant_client
        self.queue = queue

    async def find_missing_embeddings(
        self,
        lookback_hours: int = 24
    ) -> Set[str]:
        """Find documents without embeddings"""
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)

        # Get document IDs from PostgreSQL
        postgres_query = """
            SELECT id FROM core.documents
            WHERE created_at > :cutoff
            AND embedding IS NULL
        """

        result = await self.db.execute(
            postgres_query,
            {"cutoff": cutoff}
        )
        postgres_ids = {str(row.id) for row in result}

        # Get IDs from Qdrant
        qdrant_ids = set()
        offset = None

        while True:
            result = await self.qdrant.scroll(
                collection_name="production_contexts",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="timestamps.created_at",
                            range=models.Range(
                                gte=cutoff.isoformat()
                            )
                        )
                    ]
                ),
                offset=offset,
                limit=1000
            )

            qdrant_ids.update(point.id for point in result.points)

            if not result.next_page_offset:
                break
            offset = result.next_page_offset

        # Find missing
        missing = postgres_ids - qdrant_ids

        logger.info(
            "reconciliation_complete",
            postgres_count=len(postgres_ids),
            qdrant_count=len(qdrant_ids),
            missing_count=len(missing)
        )

        return missing

    async def sync_missing(self):
        """Queue missing documents for embedding"""
        missing = await self.find_missing_embeddings()

        for doc_id in missing:
            await self.queue.enqueue_document(
                doc_id,
                priority=10  # Higher priority for reconciliation
            )
```

##### Transaction Patterns
```python
# app/api/endpoints/documents.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/documents")
async def create_document(
    request: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    queue: EmbeddingQueue = Depends(get_queue)
):
    """Create document with async embedding"""

    # 1. Create in PostgreSQL (transactional)
    async with db.begin():  # Auto commit/rollback
        doc_service = DocumentService(db)
        document = await doc_service.create(request)

    # 2. Queue for embedding (after commit)
    background_tasks.add_task(
        queue.enqueue_document,
        str(document.id)
    )

    return DocumentResponse.from_orm(document)
```

### 5.5 Query Optimization Patterns

#### Embedding Cache Strategy
```python
# app/services/cache.py
import hashlib
from typing import Optional, List

class EmbeddingCache:
    """Cache for expensive embedding operations"""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 86400  # 24 hours
        self.prefix = "mobius:embedding:cache"

    def _get_key(self, text: str) -> str:
        """Generate cache key from text"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"{self.prefix}:{text_hash}"

    async def get(self, text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        key = self._get_key(text)
        cached = await self.redis.get(key)

        if cached:
            return json.loads(cached)
        return None

    async def set(self, text: str, embedding: List[float]):
        """Cache embedding"""
        key = self._get_key(text)
        await self.redis.setex(
            key,
            self.ttl,
            json.dumps(embedding)
        )

    async def get_or_generate(
        self,
        text: str,
        generator_func
    ) -> List[float]:
        """Get from cache or generate"""
        # Check cache
        cached = await self.get(text)
        if cached:
            return cached

        # Generate and cache
        embedding = await generator_func(text)
        await self.set(text, embedding)

        return embedding
```

#### Hybrid Search Performance
```python
# app/services/search.py
class HybridSearchService:
    """Optimized hybrid search across PostgreSQL and Qdrant"""

    def __init__(self, db_session, qdrant_client, cache):
        self.db = db_session
        self.qdrant = qdrant_client
        self.cache = cache

    async def search(
        self,
        query: str,
        tenant_id: str,
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[SearchResult]:
        """Perform optimized hybrid search"""

        # 1. Get query embedding (with cache)
        embedding = await self.cache.get_or_generate(
            query,
            self.embedding_service.generate_embedding
        )

        # 2. Vector search in Qdrant
        vector_results = await self.qdrant.search(
            collection_name="production_contexts",
            query_vector=embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="tenant_id",
                        match=MatchValue(value=tenant_id)
                    )
                ]
            ),
            limit=limit * 2,  # Over-fetch for filtering
            with_payload=True
        )

        # 3. Get document IDs
        doc_ids = [result.id for result in vector_results]

        # 4. Fetch metadata from PostgreSQL
        if doc_ids:
            metadata_query = """
                SELECT id, name, created_at, metadata
                FROM core.documents
                WHERE id = ANY(:ids)
                AND deleted_at IS NULL
            """

            rows = await self.db.execute(
                metadata_query,
                {"ids": doc_ids}
            )

            # 5. Combine results
            metadata_map = {
                str(row.id): row for row in rows
            }

            results = []
            for vector_result in vector_results[:limit]:
                if str(vector_result.id) in metadata_map:
                    row = metadata_map[str(vector_result.id)]
                    results.append(
                        SearchResult(
                            id=vector_result.id,
                            score=vector_result.score,
                            content=vector_result.payload.get("content"),
                            metadata=row.metadata,
                            created_at=row.created_at
                        )
                    )

            return results

        return []
```

### 5.6 Migration Strategies

#### Alembic Configuration
```python
# alembic.ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://user:pass@localhost/mobius

# Migration naming
# YYYYMMDD_HHMMSS_description.py
# Example: 20250107_120000_create_projects_table.py
```

#### Migration Template
```python
"""Create projects table

Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

def upgrade():
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('projects')
```

### 5.5 Backup Procedures

#### Automated Backup Script
```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="mobius"

# PostgreSQL backup
pg_dump -h localhost -U postgres -d $DB_NAME \
    --format=custom \
    --verbose \
    --file="${BACKUP_DIR}/postgres_${DB_NAME}_${DATE}.dump"

# Qdrant backup
curl -X POST "http://localhost:6333/collections/contexts/snapshots" \
    -H "api-key: ${QDRANT_API_KEY}" \
    -H "content-type: application/json"

# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb "${BACKUP_DIR}/redis_${DATE}.rdb"

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -type f -mtime +7 -delete
```

---

## 6. Security Implementation

### 6.1 Authentication Flow

#### API Key Authentication
```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import hashlib
import secrets

class APIKeyAuth:
    def __init__(self):
        self.scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

    async def __call__(self, api_key: str = Security(scheme)) -> str:
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )

        # Hash the API key for comparison
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Verify against database
        valid_key = await verify_api_key_hash(key_hash)
        if not valid_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        return valid_key.user_id
```

#### JWT Implementation
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel

class TokenData(BaseModel):
    user_id: str
    scopes: List[str] = []

def create_access_token(user_id: str, scopes: List[str] = None):
    expires = datetime.utcnow() + timedelta(seconds=settings.JWT_EXPIRATION)
    to_encode = {
        "sub": user_id,
        "exp": expires,
        "scopes": scopes or [],
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

async def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return TokenData(
            user_id=payload.get("sub"),
            scopes=payload.get("scopes", [])
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

### 6.2 API Key Management

#### Key Generation
```python
def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash"""
    # Generate a secure random key
    raw_key = secrets.token_urlsafe(32)

    # Create a prefixed key for easy identification
    api_key = f"mobius_{raw_key}"

    # Hash for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return api_key, key_hash

# Usage
api_key, key_hash = generate_api_key()
# Store key_hash in database
# Return api_key to user ONCE
```

### 6.3 Encryption Standards

#### Data at Rest
```python
from cryptography.fernet import Fernet
import base64

class EncryptionService:
    def __init__(self, key: str):
        self.cipher = Fernet(base64.urlsafe_b64encode(key.encode()[:32]))

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Environment variable: ENCRYPTION_KEY
encryption = EncryptionService(settings.ENCRYPTION_KEY)
```

### 6.4 Input Validation Rules

#### Pydantic Validators
```python
from pydantic import BaseModel, Field, validator
import re

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(None, max_length=1000)

    @validator('name')
    def validate_name(cls, v):
        # Allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[\w\s-]+$', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()

    @validator('description')
    def sanitize_description(cls, v):
        if v:
            # Remove any potential XSS
            v = re.sub(r'<[^>]*>', '', v)
        return v

class FileUpload(BaseModel):
    filename: str = Field(..., max_length=255)
    content_type: str
    size: int = Field(..., gt=0, le=10_485_760)  # Max 10MB

    @validator('filename')
    def validate_filename(cls, v):
        # Prevent directory traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')

        # Check extension
        allowed_extensions = {'.py', '.js', '.ts', '.md', '.json'}
        if not any(v.endswith(ext) for ext in allowed_extensions):
            raise ValueError('File type not allowed')

        return v
```

### 6.5 Security Headers

#### FastAPI Middleware
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

# Application setup
app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    max_age=3600
)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)
```

---

## 7. Testing Requirements

### 7.1 Unit Test Patterns

#### Test Structure
```python
import pytest
from unittest.mock import Mock, patch
from app.services.context_service import ContextService

class TestContextService:
    """Test cases for ContextService"""

    @pytest.fixture
    def mock_repo(self):
        """Mock repository fixture"""
        return Mock()

    @pytest.fixture
    def service(self, mock_repo):
        """Service fixture with mocked dependencies"""
        return ContextService(repository=mock_repo)

    @pytest.mark.asyncio
    async def test_create_context_success(self, service, mock_repo):
        """Test successful context creation"""
        # Arrange
        project_id = "123e4567-e89b-12d3-a456-426614174000"
        content = "def hello_world(): pass"
        expected_context = Mock(id="context-123")

        mock_repo.create.return_value = expected_context

        # Act
        result = await service.create_context(project_id, content)

        # Assert
        assert result == expected_context
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_context_invalid_project(self, service, mock_repo):
        """Test context creation with invalid project"""
        # Arrange
        mock_repo.get_project.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Project not found"):
            await service.create_context("invalid-id", "content")
```

### 7.2 Integration Test Setup

#### Database Testing
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
async def postgres_container():
    """PostgreSQL test container"""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture
async def db_session(postgres_container):
    """Database session for testing"""
    engine = create_async_engine(postgres_container.get_connection_url())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.mark.integration
async def test_project_repository_create(db_session):
    """Test project creation in database"""
    repo = ProjectRepository(db_session)

    project = await repo.create(
        name="Test Project",
        user_id="user-123"
    )

    assert project.id is not None
    assert project.name == "Test Project"
```

### 7.3 Performance Test Benchmarks

#### Load Testing with Locust
```python
from locust import HttpUser, task, between
import json

class MobiusUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Get API key on start"""
        self.headers = {
            "X-API-Key": "test-api-key",
            "Content-Type": "application/json"
        }

    @task(3)
    def create_context(self):
        """Test context creation endpoint"""
        payload = {
            "project_id": "test-project",
            "content": "def test_function(): return 42",
            "metadata": {"language": "python"}
        }

        with self.client.post(
            "/api/v1/contexts",
            json=payload,
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure("Request took too long")

    @task(5)
    def search_contexts(self):
        """Test context search endpoint"""
        params = {
            "q": "test function",
            "limit": 10
        }

        self.client.get(
            "/api/v1/contexts/search",
            params=params,
            headers=self.headers
        )
```

### 7.4 Test Data Management

#### Fixtures and Factories
```python
import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

fake = Faker()

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.LazyAttribute(lambda _: fake.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    created_at = factory.LazyFunction(datetime.utcnow)

class ProjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Project

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f"Project {n}")
    user = factory.SubFactory(UserFactory)
    settings = factory.LazyFunction(dict)

# Usage in tests
@pytest.fixture
def sample_project():
    return ProjectFactory.create(
        name="Test Project",
        settings={"max_contexts": 1000}
    )
```

### 7.5 CI/CD Pipeline Configuration

#### GitHub Actions Workflow
```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Poetry
      run: |
        curl -sSL https://install.python-poetry.org | python3 -
        echo "$HOME/.local/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: poetry install

    - name: Run linters
      run: |
        poetry run black --check .
        poetry run ruff check .
        poetry run mypy .

    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
        REDIS_URL: redis://localhost:6379/0
      run: |
        poetry run pytest \
          --cov=app \
          --cov-report=xml \
          --cov-report=term-missing \
          -v

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

## 8. Performance Standards

### 8.1 Latency Requirements

#### API Response Times
| Endpoint Type | Target | Maximum |
|--------------|--------|---------|
| Health Check | < 50ms | 100ms |
| Simple GET | < 100ms | 200ms |
| Complex Query | < 200ms | 500ms |
| File Upload | < 500ms | 1000ms |
| Batch Operations | < 1000ms | 2000ms |

#### Database Query Performance
```python
# Use query analysis
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    if total > 0.1:  # Log slow queries
        logger.warning(
            f"Slow query detected",
            extra={
                "duration": total,
                "statement": statement,
                "parameters": parameters
            }
        )
```

### 8.2 Throughput Targets

#### System Capacity
- Concurrent users: 10,000+
- Requests per second: 1,000 RPS
- Context processing: 100 documents/minute
- Search queries: 500 QPS

#### Rate Limiting
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time

class RateLimiter:
    def __init__(self, requests: int, window: int):
        self.requests = requests
        self.window = window
        self.cache = {}

    async def __call__(self, request: Request):
        client_id = request.client.host
        now = time.time()

        # Clean old entries
        self.cache = {
            k: v for k, v in self.cache.items()
            if now - v['first'] < self.window
        }

        if client_id in self.cache:
            if self.cache[client_id]['count'] >= self.requests:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            self.cache[client_id]['count'] += 1
        else:
            self.cache[client_id] = {'count': 1, 'first': now}

# Usage
rate_limiter = RateLimiter(requests=100, window=60)  # 100 req/min
app.add_middleware(rate_limiter)
```

### 8.3 Resource Utilization Limits

#### Container Resources
```yaml
# docker-compose.yml
services:
  api:
    image: mobius-api:latest
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 8.4 Optimization Guidelines

#### Query Optimization
```python
# Bad: N+1 query problem
projects = await db.query(Project).all()
for project in projects:
    contexts = await db.query(Context).filter_by(project_id=project.id).all()

# Good: Use eager loading
from sqlalchemy.orm import selectinload

projects = await db.query(Project).options(
    selectinload(Project.contexts)
).all()

# Better: Use specific fields
from sqlalchemy import select

stmt = select(
    Project.id,
    Project.name,
    func.count(Context.id).label('context_count')
).join(Context).group_by(Project.id)

results = await db.execute(stmt)
```

#### Caching Strategy
```python
from functools import lru_cache
from typing import Optional
import hashlib

class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 3600

    async def get_or_set(
        self,
        key: str,
        func,
        ttl: Optional[int] = None
    ):
        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        # Compute and cache
        result = await func()
        await self.redis.setex(
            key,
            ttl or self.default_ttl,
            json.dumps(result)
        )
        return result

    def cache_key(self, prefix: str, **kwargs) -> str:
        """Generate consistent cache key"""
        parts = [prefix]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")

        key_string = ":".join(parts)
        return f"mobius:cache:{hashlib.md5(key_string.encode()).hexdigest()}"
```

### 8.5 Profiling Procedures

#### Python Profiling
```python
import cProfile
import pstats
from functools import wraps

def profile(func):
    """Decorator for profiling functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()

        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.sort_stats('cumulative')
            stats.print_stats(10)  # Top 10 functions

    return wrapper

# Usage
@profile
async def process_context(context_data):
    # Function implementation
    pass
```

#### Memory Profiling
```python
from memory_profiler import profile
import tracemalloc

# Start tracing
tracemalloc.start()

# Your code here

# Get memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 10**6:.1f} MB")
print(f"Peak memory: {peak / 10**6:.1f} MB")

# Get top memory allocations
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

---

## 9. Documentation Standards

### 9.1 Code Documentation

#### Python Docstrings
```python
from typing import List, Optional, Dict, Any

class ContextService:
    """
    Service for managing context operations.

    This service handles all context-related business logic including
    creation, retrieval, processing, and search operations.

    Attributes:
        repository: The context repository for data access
        embedder: The embedding service for vector generation
        cache: The caching service for performance optimization
    """

    async def create_context(
        self,
        project_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Context:
        """
        Create a new context for a project.

        This method processes the content, generates embeddings, and stores
        the context in both the database and vector store.

        Args:
            project_id: The UUID of the project
            content: The raw content to be processed
            metadata: Optional metadata dict containing:
                - language: Programming language (python, javascript, etc)
                - file_path: Original file path
                - version: Content version number

        Returns:
            Context: The created context object with generated ID

        Raises:
            ValueError: If project_id is invalid or content is empty
            ProcessingError: If content processing fails
            StorageError: If database or vector storage fails

        Example:
            >>> service = ContextService()
            >>> context = await service.create_context(
            ...     project_id="123e4567-e89b-12d3-a456-426614174000",
            ...     content="def hello(): return 'world'",
            ...     metadata={"language": "python"}
            ... )
            >>> print(context.id)
            "context-123"
        """
        # Implementation
        pass
```

#### TypeScript Documentation
```typescript
/**
 * Context provider for VSCode extension
 *
 * Manages the context state and provides methods for context operations
 * within the VSCode environment.
 */
export class ContextProvider implements vscode.TreeDataProvider<ContextItem> {
    /**
     * Event emitter for tree data changes
     */
    private _onDidChangeTreeData: vscode.EventEmitter<ContextItem | undefined | null | void> =
        new vscode.EventEmitter<ContextItem | undefined | null | void>();

    /**
     * Event that fires when tree data changes
     */
    readonly onDidChangeTreeData: vscode.Event<ContextItem | undefined | null | void> =
        this._onDidChangeTreeData.event;

    /**
     * Creates a new context item in the current project
     *
     * @param {string} content - The content to create context from
     * @param {ContextMetadata} metadata - Additional metadata for the context
     * @returns {Promise<ContextItem>} The created context item
     * @throws {Error} If the API request fails
     *
     * @example
     * const context = await provider.createContext(
     *     "function calculate() { return 42; }",
     *     { language: "javascript", fileName: "calc.js" }
     * );
     */
    async createContext(
        content: string,
        metadata?: ContextMetadata
    ): Promise<ContextItem> {
        // Implementation
    }
}
```

### 9.2 API Documentation

#### OpenAPI/Swagger Setup
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Mobius Context Engineering Platform",
    description="AI-powered context management for coding assistants",
    version="1.0.0",
    terms_of_service="https://mobius.ai/terms",
    contact={
        "name": "Mobius Support",
        "url": "https://mobius.ai/support",
        "email": "support@mobius.ai"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://mobius.ai/license"
    }
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add custom schemas
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
```

#### Endpoint Documentation
```python
from fastapi import APIRouter, HTTPException, Depends
from typing import List

router = APIRouter(prefix="/api/v1/contexts", tags=["contexts"])

@router.post(
    "/",
    response_model=ContextResponse,
    status_code=201,
    summary="Create a new context",
    description="Creates a new context by processing the provided content and generating embeddings",
    response_description="The created context with generated ID and metadata",
    responses={
        201: {
            "description": "Context created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "context-123",
                        "project_id": "proj-456",
                        "content": "def hello(): pass",
                        "chunks": 1,
                        "created_at": "2025-01-07T10:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid input data"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"}
    }
)
async def create_context(
    request: ContextCreateRequest,
    current_user: User = Depends(get_current_user)
) -> ContextResponse:
    """
    Create a new context.

    - **project_id**: UUID of the project
    - **content**: The raw content to process
    - **metadata**: Optional metadata (language, file_path, etc)
    """
    # Implementation
    pass
```

### 9.3 Architecture Decision Records

#### ADR Template
```markdown
# ADR-001: Use Qdrant for Vector Storage

## Status
Accepted

## Context
We need a vector database to store and search embeddings generated from code contexts. The solution must support:
- High-dimensional vectors (1536d from OpenAI)
- Semantic search with filtering
- Horizontal scalability
- Low latency (<100ms p95)

## Decision
We will use Qdrant Cloud as our vector storage solution.

## Consequences

### Positive
- Native support for high-dimensional vectors
- Built-in filtering capabilities
- Managed cloud service reduces operational overhead
- Good Python SDK with async support
- Proven scalability

### Negative
- Additional service dependency
- Potential vendor lock-in
- Monthly costs for managed service

## Alternatives Considered
1. **Pinecone**: More expensive, less flexible filtering
2. **Weaviate**: More complex setup, less mature
3. **PostgreSQL + pgvector**: Limited scalability for large datasets
```

### 9.4 README Templates

#### Service README
```markdown
# Context Service

## Overview
The Context Service manages all context-related operations for the Mobius platform.

## Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Qdrant instance

## Installation

### Local Development
```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start service
uvicorn app.main:app --reload
```

### Docker
```bash
docker-compose up -d
```

## Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | - |
| REDIS_URL | Redis connection string | - |
| QDRANT_URL | Qdrant API endpoint | - |
| OPENAI_API_KEY | OpenAI API key | - |

## API Documentation
Once running, visit http://localhost:8000/docs for interactive API documentation.

## Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_context_service.py
```

## Deployment
See [deployment guide](./docs/deployment.md) for production deployment instructions.
```

### 9.5 Deployment Guides

#### Production Deployment
```markdown
# Production Deployment Guide

## Prerequisites
- Kubernetes cluster (1.28+)
- kubectl configured
- Helm 3.x installed
- Container registry access

## Step 1: Build and Push Images
```bash
# Build production image
docker build -t mobius-api:v1.0.0 -f Dockerfile.prod .

# Tag for registry
docker tag mobius-api:v1.0.0 registry.mobius.ai/api:v1.0.0

# Push to registry
docker push registry.mobius.ai/api:v1.0.0
```

## Step 2: Configure Secrets
```bash
# Create namespace
kubectl create namespace mobius

# Create secrets
kubectl create secret generic mobius-secrets \
  --from-literal=database-url=$DATABASE_URL \
  --from-literal=redis-url=$REDIS_URL \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  -n mobius
```

## Step 3: Deploy with Helm
```bash
# Add Helm repository
helm repo add mobius https://charts.mobius.ai
helm repo update

# Install
helm install mobius mobius/platform \
  --namespace mobius \
  --values production-values.yaml
```

## Step 4: Verify Deployment
```bash
# Check pods
kubectl get pods -n mobius

# Check services
kubectl get svc -n mobius

# View logs
kubectl logs -f deployment/mobius-api -n mobius
```

## Monitoring
Access monitoring dashboards:
- Grafana: https://grafana.mobius.ai
- Prometheus: https://prometheus.mobius.ai

## Rollback Procedure
```bash
# List releases
helm list -n mobius

# Rollback to previous version
helm rollback mobius -n mobius
```
```

---

## 10. Development Workflow

### 10.1 Local Development Setup

#### Environment Setup Script
```bash
#!/bin/bash
# setup-dev.sh

echo "Setting up Mobius development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
required_version="3.11"
if [[ ! "$python_version" == "$required_version"* ]]; then
    echo "Error: Python $required_version required"
    exit 1
fi

# Install Poetry
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Create virtual environment
poetry install

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file - please update with your configuration"
fi

# Start services
docker-compose up -d postgres redis

# Wait for services
echo "Waiting for services to start..."
sleep 5

# Run migrations
poetry run alembic upgrade head

# Install pre-commit hooks
poetry run pre-commit install

echo "Setup complete! Run 'poetry run uvicorn app.main:app --reload' to start the server"
```

#### VSCode Configuration
```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", "88"],
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true
  }
}
```

### 10.2 Debugging Procedures

#### Debug Configuration
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "ENV": "development"
      }
    },
    {
      "name": "Pytest Debug",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "-s",
        "${file}"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

#### Debugging Tools
```python
# Debug middleware
import time
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

async def debug_middleware(request: Request, call_next):
    start_time = time.time()

    # Log request
    logger.debug(f"Request: {request.method} {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")

    # Process request
    response = await call_next(request)

    # Log response
    process_time = time.time() - start_time
    logger.debug(f"Response: {response.status_code} in {process_time:.3f}s")

    # Add debug headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request.state.request_id

    return response

# Enable in development
if settings.DEBUG:
    app.middleware("http")(debug_middleware)
```

### 10.3 Code Review Checklist

#### Python Code Review
- [ ] Code follows PEP 8 standards
- [ ] All functions have type hints
- [ ] Docstrings are complete and accurate
- [ ] No hardcoded secrets or credentials
- [ ] Proper error handling with specific exceptions
- [ ] Async functions used appropriately
- [ ] Database queries are optimized
- [ ] Unit tests cover new functionality
- [ ] No circular imports
- [ ] Dependencies are justified

#### API Review
- [ ] Endpoints follow RESTful conventions
- [ ] Request/response schemas are validated
- [ ] Error responses are consistent
- [ ] Authentication/authorization implemented
- [ ] Rate limiting considered
- [ ] API documentation updated
- [ ] Backward compatibility maintained
- [ ] Performance impact assessed

### 10.4 Deployment Procedures

#### Staging Deployment
```bash
#!/bin/bash
# deploy-staging.sh

set -e

echo "Deploying to staging..."

# Run tests
poetry run pytest

# Build image
docker build -t mobius-api:staging .

# Tag with commit hash
COMMIT_HASH=$(git rev-parse --short HEAD)
docker tag mobius-api:staging registry.mobius.ai/api:staging-$COMMIT_HASH

# Push to registry
docker push registry.mobius.ai/api:staging-$COMMIT_HASH

# Update staging
kubectl set image deployment/mobius-api \
  api=registry.mobius.ai/api:staging-$COMMIT_HASH \
  -n mobius-staging

# Wait for rollout
kubectl rollout status deployment/mobius-api -n mobius-staging

# Run smoke tests
poetry run pytest tests/smoke/ --staging

echo "Staging deployment complete!"
```

### 10.5 Rollback Strategies

#### Kubernetes Rollback
```bash
#!/bin/bash
# rollback.sh

# Get current revision
CURRENT=$(kubectl get deployment mobius-api -n mobius -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')

echo "Current revision: $CURRENT"

# Show rollout history
kubectl rollout history deployment/mobius-api -n mobius

# Rollback to previous version
read -p "Rollback to previous version? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl rollout undo deployment/mobius-api -n mobius
    kubectl rollout status deployment/mobius-api -n mobius
    echo "Rollback complete"
fi
```

#### Database Rollback
```python
# Alembic rollback
import subprocess
import sys

def rollback_database(steps=1):
    """Rollback database migrations"""
    try:
        # Show current version
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True
        )
        print(f"Current version: {result.stdout}")

        # Confirm rollback
        confirm = input(f"Rollback {steps} migration(s)? (y/n): ")
        if confirm.lower() != 'y':
            print("Rollback cancelled")
            return

        # Execute rollback
        subprocess.run(
            ["alembic", "downgrade", f"-{steps}"],
            check=True
        )
        print("Rollback complete")

    except subprocess.CalledProcessError as e:
        print(f"Rollback failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    rollback_database()
```

---

## 11. Monitoring and Observability

### 11.1 Logging Standards

#### Structured Logging Configuration
```python
import structlog
from pythonjsonlogger import jsonlogger

def configure_logging():
    """Configure structured logging"""

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter()
    logHandler.setFormatter(formatter)

    logging.basicConfig(
        handlers=[logHandler],
        level=getattr(logging, settings.LOG_LEVEL),
    )
```

#### Logging Context
```python
import structlog
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")

class LoggingMiddleware:
    async def __call__(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        # Add to structlog context
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path
        )

        response = await call_next(request)

        # Clear context
        structlog.contextvars.clear_contextvars()

        return response

# Usage in code
logger = structlog.get_logger()
logger.info("processing_context",
    project_id=project_id,
    chunk_count=len(chunks)
)
```

### 11.2 Metrics Collection

#### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from prometheus_client import make_asgi_app

# Create registry
registry = CollectorRegistry()

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    registry=registry
)

active_connections = Gauge(
    'active_connections',
    'Active WebSocket connections',
    registry=registry
)

context_processing_time = Histogram(
    'context_processing_seconds',
    'Time to process context',
    ['operation'],
    registry=registry
)

# Metrics middleware
class MetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        # Skip metrics endpoint
        if path == "/metrics":
            return await call_next(request)

        # Track request
        with request_duration.labels(
            method=method,
            endpoint=path
        ).time():
            response = await call_next(request)

        # Count request
        request_count.labels(
            method=method,
            endpoint=path,
            status=response.status_code
        ).inc()

        return response

# Add metrics endpoint
metrics_app = make_asgi_app(registry=registry)
app.mount("/metrics", metrics_app)
```

### 11.3 Distributed Tracing

#### OpenTelemetry Setup
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def configure_tracing():
    """Configure OpenTelemetry tracing"""

    # Set up the tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()

    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTLP_ENDPOINT,
        insecure=True
    )

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Instrument libraries
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    RedisInstrumentor().instrument()

# Custom span example
tracer = trace.get_tracer(__name__)

async def process_context(context_data: dict):
    with tracer.start_as_current_span("process_context") as span:
        span.set_attribute("context.size", len(context_data))

        # Processing logic
        with tracer.start_as_current_span("parse_content"):
            parsed = await parse_content(context_data)

        with tracer.start_as_current_span("generate_embeddings"):
            embeddings = await generate_embeddings(parsed)

        span.set_attribute("embeddings.count", len(embeddings))
        return embeddings
```

### 11.4 Alert Configurations

#### Alerting Rules (Prometheus)
```yaml
# alerts.yml
groups:
  - name: mobius_api
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is above 500ms"

      - alert: DatabaseConnectionPoolExhausted
        expr: |
          db_connection_pool_size - db_connection_pool_available < 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
          description: "Less than 5 connections available in pool"
```

### 11.5 Dashboard Requirements

#### Grafana Dashboard JSON
```json
{
  "dashboard": {
    "title": "Mobius API Dashboard",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Response Time (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Connections",
        "targets": [
          {
            "expr": "active_connections",
            "legendFormat": "Connections"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
```

---

## 12. Best Practices

### 12.1 Async Programming Patterns

#### Concurrent Processing
```python
import asyncio
from typing import List, TypeVar, Callable, Any
from asyncio import Semaphore

T = TypeVar('T')

class AsyncBatcher:
    """Batch async operations with concurrency control"""

    def __init__(self, batch_size: int = 100, max_concurrent: int = 10):
        self.batch_size = batch_size
        self.semaphore = Semaphore(max_concurrent)

    async def process_batch(
        self,
        items: List[T],
        process_func: Callable[[T], Any]
    ) -> List[Any]:
        """Process items in batches with concurrency limit"""
        results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await asyncio.gather(
                *[self._process_with_semaphore(process_func, item)
                  for item in batch]
            )
            results.extend(batch_results)

        return results

    async def _process_with_semaphore(
        self,
        process_func: Callable[[T], Any],
        item: T
    ) -> Any:
        async with self.semaphore:
            return await process_func(item)

# Usage
batcher = AsyncBatcher(batch_size=50, max_concurrent=5)
embeddings = await batcher.process_batch(
    chunks,
    generate_embedding
)
```

#### Background Tasks
```python
from fastapi import BackgroundTasks
import asyncio

class TaskQueue:
    """Async task queue for background processing"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.workers = []

    async def start_workers(self, num_workers: int = 5):
        """Start background workers"""
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

    async def _worker(self, name: str):
        """Worker process"""
        logger = structlog.get_logger().bind(worker=name)

        while True:
            try:
                task = await self.queue.get()
                logger.info("processing_task", task_id=task.id)

                await task.process()

                logger.info("task_completed", task_id=task.id)
            except Exception as e:
                logger.error("task_failed", task_id=task.id, error=str(e))
            finally:
                self.queue.task_done()

    async def add_task(self, task):
        """Add task to queue"""
        await self.queue.put(task)

# Initialize on startup
task_queue = TaskQueue()

@app.on_event("startup")
async def startup_event():
    await task_queue.start_workers()
```

### 12.2 Dependency Injection

#### Service Layer Pattern
```python
from typing import Protocol
from fastapi import Depends

class RepositoryProtocol(Protocol):
    """Repository interface"""
    async def get(self, id: str) -> Any: ...
    async def create(self, data: dict) -> Any: ...
    async def update(self, id: str, data: dict) -> Any: ...
    async def delete(self, id: str) -> None: ...

class ProjectService:
    """Service with injected dependencies"""

    def __init__(
        self,
        repository: RepositoryProtocol,
        cache: CacheService,
        embedder: EmbeddingService
    ):
        self.repository = repository
        self.cache = cache
        self.embedder = embedder

    async def create_project(self, data: ProjectCreate) -> Project:
        # Business logic here
        project = await self.repository.create(data.dict())
        await self.cache.set(f"project:{project.id}", project)
        return project

# Dependency providers
async def get_db_session():
    async with AsyncSession(engine) as session:
        yield session

def get_project_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ProjectRepository:
    return ProjectRepository(session)

def get_project_service(
    repository: ProjectRepository = Depends(get_project_repository),
    cache: CacheService = Depends(get_cache_service),
    embedder: EmbeddingService = Depends(get_embedding_service)
) -> ProjectService:
    return ProjectService(repository, cache, embedder)

# Usage in endpoint
@router.post("/projects")
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service)
):
    return await service.create_project(data)
```

### 12.3 Configuration Management

#### Settings with Pydantic
```python
from pydantic import BaseSettings, Field, validator
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    """Application settings with validation"""

    # Application
    app_name: str = "Mobius API"
    app_version: str = "1.0.0"
    environment: str = Field(..., env="APP_ENV")
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api/v1"
    allowed_origins: List[str] = ["http://localhost:3000"]

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 40

    # Redis
    redis_url: str
    redis_pool_size: int = 10

    # Security
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    api_key_header: str = "X-API-Key"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 86400  # 24 hours

    # External Services
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: Optional[str] = None

    @validator("environment")
    def validate_environment(cls, v):
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith("postgresql"):
            raise ValueError("Only PostgreSQL is supported")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton instance
settings = Settings()

# Environment-specific overrides
if settings.environment == "production":
    settings.debug = False
    settings.database_pool_size = 50
elif settings.environment == "development":
    settings.debug = True
```

### 12.4 Secret Handling

#### Secrets Manager Integration
```python
import boto3
from functools import lru_cache
import json

class SecretsManager:
    """AWS Secrets Manager integration"""

    def __init__(self):
        self.client = boto3.client('secretsmanager')
        self._cache = {}

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {e}")
            raise

    def get_database_credentials(self) -> dict:
        """Get database credentials"""
        secret = self.get_secret("mobius/database/credentials")
        return {
            "host": secret["host"],
            "port": secret["port"],
            "username": secret["username"],
            "password": secret["password"],
            "database": secret["database"]
        }

    def get_api_keys(self) -> dict:
        """Get external API keys"""
        return self.get_secret("mobius/api/keys")

# Usage
secrets_manager = SecretsManager()

# Build database URL from secrets
db_creds = secrets_manager.get_database_credentials()
DATABASE_URL = (
    f"postgresql+asyncpg://{db_creds['username']}:{db_creds['password']}"
    f"@{db_creds['host']}:{db_creds['port']}/{db_creds['database']}"
)
```

### 12.5 Resource Cleanup

#### Context Managers
```python
from contextlib import asynccontextmanager
import asyncio

class ResourcePool:
    """Generic resource pool with cleanup"""

    def __init__(self, factory, max_size: int = 10):
        self.factory = factory
        self.max_size = max_size
        self.pool = asyncio.Queue(maxsize=max_size)
        self.active = set()

    @asynccontextmanager
    async def acquire(self):
        """Acquire resource from pool"""
        resource = None
        try:
            # Try to get from pool
            try:
                resource = self.pool.get_nowait()
            except asyncio.QueueEmpty:
                # Create new if under limit
                if len(self.active) < self.max_size:
                    resource = await self.factory()
                else:
                    # Wait for available resource
                    resource = await self.pool.get()

            self.active.add(resource)
            yield resource

        finally:
            # Return to pool
            if resource:
                self.active.discard(resource)
                try:
                    self.pool.put_nowait(resource)
                except asyncio.QueueFull:
                    # Pool full, cleanup resource
                    await self._cleanup_resource(resource)

    async def _cleanup_resource(self, resource):
        """Cleanup resource"""
        if hasattr(resource, 'close'):
            await resource.close()

# Usage
connection_pool = ResourcePool(create_connection, max_size=20)

async def process_data(data):
    async with connection_pool.acquire() as conn:
        result = await conn.execute(query, data)
        return result
```

#### Shutdown Handlers
```python
import signal
import asyncio

class GracefulShutdown:
    """Handle graceful shutdown"""

    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.tasks = set()

    def setup_handlers(self):
        """Setup signal handlers"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signal"""
        logger.info("Shutdown signal received", signal=signum)
        self.shutdown_event.set()

    async def create_task(self, coro):
        """Create tracked task"""
        task = asyncio.create_task(coro)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Starting graceful shutdown")

        # Signal all tasks to stop
        self.shutdown_event.set()

        # Wait for tasks with timeout
        if self.tasks:
            logger.info(f"Waiting for {len(self.tasks)} tasks")
            done, pending = await asyncio.wait(
                self.tasks,
                timeout=30.0
            )

            # Cancel remaining tasks
            for task in pending:
                task.cancel()

            # Wait for cancellation
            await asyncio.gather(*pending, return_exceptions=True)

        logger.info("Graceful shutdown complete")

# Application lifecycle
shutdown_handler = GracefulShutdown()

@app.on_event("startup")
async def startup():
    shutdown_handler.setup_handlers()

@app.on_event("shutdown")
async def shutdown():
    await shutdown_handler.shutdown()
```

---

## Appendix A: Quick Reference

### Command Reference
```bash
# Development
poetry install                      # Install dependencies
poetry run dev                      # Start development server
poetry run test                     # Run tests
poetry run lint                     # Run linters
poetry run format                   # Format code

# Database
poetry run alembic upgrade head     # Run migrations
poetry run alembic revision -m ""   # Create migration
poetry run alembic downgrade -1     # Rollback migration

# Docker
docker-compose up -d               # Start services
docker-compose logs -f api         # View logs
docker-compose down -v             # Stop and cleanup

# Production
kubectl apply -f k8s/              # Deploy to Kubernetes
kubectl rollout status deploy/api  # Check deployment
helm upgrade --install mobius .    # Deploy with Helm
```

### Environment Variables Reference
```bash
# Required
APP_ENV=development|staging|production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
QDRANT_URL=http://localhost:6333

# Optional
LOG_LEVEL=INFO
MOBIUS_PORT=8000
SECRET_KEY=your-secret-key
SENTRY_DSN=https://...
```

---

## Document Maintenance

This document should be reviewed and updated:
- Weekly during active development
- Before each major release
- When introducing new technologies
- When changing architectural patterns

Last Updated: 2025-01-07
Next Review: 2025-01-14
