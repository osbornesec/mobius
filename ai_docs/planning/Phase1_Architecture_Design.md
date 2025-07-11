# Phase 1 Architecture Design - Mobius Context Engineering Platform

## Executive Summary

This document provides a comprehensive architectural design for Phase 1 of the Mobius Context Engineering Platform. The design focuses on establishing a robust foundation with FastAPI, PostgreSQL with pgvector, Qdrant for vector storage, and Redis for caching. This architecture prioritizes performance, scalability, and maintainability while adhering to modern Python development practices.

## Table of Contents

1. [FastAPI Application Structure](#1-fastapi-application-structure)
2. [API Design Patterns](#2-api-design-patterns)
3. [Database Architecture](#3-database-architecture)
4. [Context Processing Pipeline](#4-context-processing-pipeline)
5. [Performance Considerations](#5-performance-considerations)
6. [Security Architecture](#6-security-architecture)
7. [Development Standards](#7-development-standards)
8. [Deployment Architecture](#8-deployment-architecture)

---

## 1. FastAPI Application Structure

### 1.1 Project Layout

```
mobius/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   ├── dependencies.py        # Shared dependencies
│   │   ├── security.py            # Security utilities
│   │   └── logging.py             # Logging configuration
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── endpoints/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── projects.py   # Project management endpoints
│   │   │   │   ├── contexts.py   # Context operations
│   │   │   │   ├── search.py     # Search functionality
│   │   │   │   └── health.py     # Health checks
│   │   │   └── router.py          # API v1 router
│   │   └── deps.py                # API-specific dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain/                # Domain models
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── context.py
│   │   │   └── embedding.py
│   │   ├── schemas/               # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── request/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── project.py
│   │   │   │   └── context.py
│   │   │   └── response/
│   │   │       ├── __init__.py
│   │   │       ├── project.py
│   │   │       └── context.py
│   │   └── database/              # Database models
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── project_service.py    # Business logic for projects
│   │   ├── context_service.py    # Context processing logic
│   │   ├── embedding_service.py  # Embedding generation
│   │   └── search_service.py     # Search implementation
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py               # Base repository pattern
│   │   ├── project_repo.py       # Project data access
│   │   ├── context_repo.py       # Context data access
│   │   └── vector_repo.py        # Vector storage access
│   ├── processing/
│   │   ├── __init__.py
│   │   ├── pipeline.py           # Processing pipeline
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── python_parser.py
│   │   │   ├── javascript_parser.py
│   │   │   └── typescript_parser.py
│   │   ├── chunkers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── ast_chunker.py
│   │   └── embedders/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── openai_embedder.py
│   └── utils/
│       ├── __init__.py
│       ├── cache.py               # Caching utilities
│       ├── async_utils.py         # Async helpers
│       └── validators.py          # Custom validators
├── alembic/                       # Database migrations
│   ├── versions/
│   └── alembic.ini
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Test configuration
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/
│   ├── start.sh
│   └── test.sh
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── pyproject.toml
└── README.md
```

### 1.2 Core Application Factory Pattern

```python
# app/main.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import engine, create_db_tables
from app.services.vector_service import VectorService
from app.utils.cache import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan management for startup and shutdown events.
    """
    # Startup
    setup_logging()
    await create_db_tables()
    await redis_client.initialize()
    await VectorService.initialize()

    yield

    # Shutdown
    await redis_client.close()
    await VectorService.close()
    await engine.dispose()


def create_application() -> FastAPI:
    """
    Application factory pattern for creating FastAPI instance.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
```

### 1.3 Configuration Management

```python
# app/core/config.py
from typing import List, Optional, Union
from pydantic import AnyHttpUrl, Field, PostgresDsn, RedisDsn, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with Pydantic validation."""

    # Project Settings
    PROJECT_NAME: str = "Mobius Context Engineering Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # PostgreSQL
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour default

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "mobius_contexts"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSION: int = 1536

    # Performance
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    REDIS_POOL_SIZE: int = 10
    BATCH_SIZE: int = 100
    MAX_WORKERS: int = 4

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


settings = Settings()
```

### 1.4 Dependency Injection System

```python
# app/core/dependencies.py
from typing import AsyncGenerator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.db.database import async_session_maker
from app.core.security import verify_token
from app.utils.cache import redis_client
from app.models.domain.user import User


# Security scheme
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis() -> Redis:
    """Dependency for getting Redis client."""
    return redis_client.get_client()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """Dependency for getting current authenticated user."""
    token = credentials.credentials

    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    # Get user from database
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


# Type aliases for cleaner code
DatabaseDep = Annotated[AsyncSession, Depends(get_db)]
RedisDep = Annotated[Redis, Depends(get_redis)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
```

---

## 2. API Design Patterns

### 2.1 RESTful Endpoint Structure

```python
# app/api/v1/endpoints/projects.py
from typing import List, Optional
from fastapi import APIRouter, Query, status
from app.core.dependencies import DatabaseDep, CurrentUserDep
from app.models.schemas.request.project import ProjectCreate, ProjectUpdate
from app.models.schemas.response.project import ProjectResponse, ProjectListResponse
from app.services.project_service import ProjectService

router = APIRouter()

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    db: DatabaseDep,
    current_user: CurrentUserDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None
) -> ProjectListResponse:
    """
    List all projects for the current user with pagination and search.
    """
    service = ProjectService(db)
    projects, total = await service.list_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        search=search
    )

    return ProjectListResponse(
        items=projects,
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep
) -> ProjectResponse:
    """
    Create a new project.
    """
    service = ProjectService(db)
    project = await service.create_project(
        project_data=project_in,
        user_id=current_user.id
    )
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: DatabaseDep,
    current_user: CurrentUserDep
) -> ProjectResponse:
    """
    Get a specific project by ID.
    """
    service = ProjectService(db)
    project = await service.get_project(
        project_id=project_id,
        user_id=current_user.id
    )
    return project
```

### 2.2 Request/Response Models with Pydantic

```python
# app/models/schemas/request/project.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime


class ProjectBase(BaseModel):
    """Base project schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    repository_url: Optional[str] = None
    framework: Optional[str] = None
    language: str = Field(..., regex="^(python|javascript|typescript)$")

    @field_validator('repository_url')
    @classmethod
    def validate_repository_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith(('https://', 'git@')):
            raise ValueError('Repository URL must be a valid git URL')
        return v


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra='forbid')


# app/models/schemas/response/project.py
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class ProjectResponse(BaseModel):
    """Response schema for project data."""
    id: str
    name: str
    description: Optional[str]
    repository_url: Optional[str]
    framework: Optional[str]
    language: str
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    owner_id: str
    context_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Response schema for paginated project list."""
    items: List[ProjectResponse]
    total: int
    skip: int
    limit: int
```

### 2.3 Error Handling and Validation

```python
# app/api/error_handlers.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.core.logging import logger


class APIException(Exception):
    """Base API exception."""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


class NotFoundError(APIException):
    """Resource not found error."""
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND"
        )


class PermissionError(APIException):
    """Permission denied error."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="PERMISSION_DENIED"
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers."""

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": exc.error_code,
                "request_id": request.state.request_id
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "request_id": request.state.request_id
            }
        )
```

### 2.4 Rate Limiting Implementation

```python
# app/middleware/rate_limit.py
from typing import Callable, Tuple
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from app.utils.cache import redis_client
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        # Get client identifier (IP or user ID)
        client_id = self._get_client_id(request)

        # Check rate limits
        if not await self._check_rate_limit(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )

        response = await call_next(request)
        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request."""
        # Try to get user ID from JWT token
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0]}"
        return f"ip:{request.client.host}"

    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limits."""
        redis = redis_client.get_client()

        # Check per-minute limit
        minute_key = f"rate_limit:minute:{client_id}"
        minute_count = await redis.incr(minute_key)
        if minute_count == 1:
            await redis.expire(minute_key, 60)

        if minute_count > settings.RATE_LIMIT_PER_MINUTE:
            return False

        # Check per-hour limit
        hour_key = f"rate_limit:hour:{client_id}"
        hour_count = await redis.incr(hour_key)
        if hour_count == 1:
            await redis.expire(hour_key, 3600)

        if hour_count > settings.RATE_LIMIT_PER_HOUR:
            return False

        return True
```

### 2.5 API Versioning Strategy

```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import projects, contexts, search, health

api_router = APIRouter()

# Include endpoint routers with tags and prefixes
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    contexts.router,
    prefix="/contexts",
    tags=["contexts"]
)

api_router.include_router(
    search.router,
    prefix="/search",
    tags=["search"]
)


# app/api/v2/router.py (future)
# V2 API can coexist with V1, allowing gradual migration
```

---

## 3. Database Architecture

### 3.1 PostgreSQL Schema Design

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    framework VARCHAR(100),
    language VARCHAR(50) NOT NULL,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_project_name_per_user UNIQUE (owner_id, name)
);

-- Context entries table
CREATE TABLE context_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL, -- 'function', 'class', 'module', etc.
    content_name VARCHAR(255),
    content TEXT NOT NULL,
    language VARCHAR(50) NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    ast_metadata JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '{}', -- imports, function calls, etc.
    complexity_metrics JSONB DEFAULT '{}',
    embedding vector(1536), -- for pgvector
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
CREATE INDEX idx_context_entries_project_id ON context_entries(project_id);
CREATE INDEX idx_context_entries_content_type ON context_entries(content_type);
CREATE INDEX idx_context_entries_embedding ON context_entries USING ivfflat (embedding vector_cosine_ops);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_context_entries_updated_at BEFORE UPDATE ON context_entries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 3.2 SQLAlchemy Models with Async Support

```python
# app/models/database/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, declarative_base()):
    """Base class for all database models."""
    __abstract__ = True


# app/models/database/models.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey,
    Text, Integer, JSON, ARRAY, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.models.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint('owner_id', 'name', name='unique_project_name_per_user'),
    )

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    repository_url: Mapped[Optional[str]] = mapped_column(String(500))
    framework: Mapped[Optional[str]] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    owner_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="projects")
    context_entries: Mapped[List["ContextEntry"]] = relationship("ContextEntry", back_populates="project", cascade="all, delete-orphan")


class ContextEntry(Base):
    __tablename__ = "context_entries"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)  # function, class, module, etc.
    content_name: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    start_line: Mapped[Optional[int]] = mapped_column(Integer)
    end_line: Mapped[Optional[int]] = mapped_column(Integer)
    ast_metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    dependencies: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    complexity_metrics: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="context_entries")
```

### 3.3 Database Connection Management

```python
# app/db/database.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.models.database.base import Base


# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=False,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session maker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_db_tables():
    """Create database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 3.4 Qdrant Collection Structure

```python
# app/services/vector_service.py
from typing import List, Dict, Any, Optional
from uuid import UUID
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    SearchRequest, SearchParams
)
from app.core.config import settings
from app.core.logging import logger


class VectorService:
    """Service for managing vector storage with Qdrant."""

    _client: Optional[QdrantClient] = None

    @classmethod
    async def initialize(cls):
        """Initialize Qdrant client and create collection if needed."""
        cls._client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
            api_key=settings.QDRANT_API_KEY,
            timeout=30
        )

        # Create collection if it doesn't exist
        collections = await cls._client.get_collections()
        if settings.QDRANT_COLLECTION_NAME not in [c.name for c in collections.collections]:
            await cls._client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=settings.OPENAI_EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                ),
                on_disk_payload=True  # Store payload on disk for large contexts
            )

            # Create payload indexes for efficient filtering
            await cls._client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                field_name="project_id",
                field_schema="keyword"
            )
            await cls._client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                field_name="content_type",
                field_schema="keyword"
            )

            logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION_NAME}")

    @classmethod
    async def close(cls):
        """Close Qdrant client connection."""
        if cls._client:
            await cls._client.close()

    @classmethod
    async def upsert_embeddings(
        cls,
        embeddings: List[Dict[str, Any]]
    ) -> None:
        """
        Upsert embeddings to Qdrant.

        Args:
            embeddings: List of dicts with keys:
                - id: UUID
                - vector: List[float]
                - payload: Dict with metadata
        """
        points = [
            PointStruct(
                id=str(emb["id"]),
                vector=emb["vector"],
                payload=emb["payload"]
            )
            for emb in embeddings
        ]

        await cls._client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points
        )

    @classmethod
    async def search(
        cls,
        query_vector: List[float],
        project_id: Optional[UUID] = None,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_vector: Query embedding vector
            project_id: Filter by project ID
            content_types: Filter by content types
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of search results with scores and payloads
        """
        # Build filter conditions
        filter_conditions = []

        if project_id:
            filter_conditions.append(
                FieldCondition(
                    key="project_id",
                    match=MatchValue(value=str(project_id))
                )
            )

        if content_types:
            filter_conditions.append(
                FieldCondition(
                    key="content_type",
                    match=MatchValue(any=content_types)
                )
            )

        # Perform search
        search_result = await cls._client.search(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=Filter(must=filter_conditions) if filter_conditions else None,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=True
        )

        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in search_result
        ]
```

### 3.5 Redis Caching Patterns

```python
# app/utils/cache.py
import json
from typing import Any, Optional, Union, List
from datetime import timedelta
from redis.asyncio import Redis, ConnectionPool
from app.core.config import settings
from app.core.logging import logger


class RedisCache:
    """Redis cache manager with connection pooling."""

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None

    async def initialize(self):
        """Initialize Redis connection pool."""
        self._pool = ConnectionPool.from_url(
            str(settings.REDIS_URL),
            max_connections=settings.REDIS_POOL_SIZE,
            decode_responses=True
        )
        self._client = Redis(connection_pool=self._pool)

        # Test connection
        await self._client.ping()
        logger.info("Redis connection established")

    async def close(self):
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()

    def get_client(self) -> Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("Redis client not initialized")
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL."""
        try:
            serialized = json.dumps(value)
            if ttl:
                await self._client.setex(key, ttl, serialized)
            else:
                await self._client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def delete(self, key: Union[str, List[str]]) -> int:
        """Delete key(s) from cache."""
        try:
            if isinstance(key, list):
                return await self._client.delete(*key)
            return await self._client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    def cache_key(self, prefix: str, *args) -> str:
        """Generate cache key with prefix."""
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)


# Global cache instance
redis_client = RedisCache()


# Decorators for caching
from functools import wraps
import hashlib


def cache_result(prefix: str, ttl: int = 3600):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_data = f"{func.__name__}:{args}:{kwargs}"
            cache_hash = hashlib.md5(cache_data.encode()).hexdigest()
            cache_key = redis_client.cache_key(prefix, cache_hash)

            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached is not None:
                return cached

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_client.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

---

## 4. Context Processing Pipeline

### 4.1 File Ingestion Workflow

```mermaid
graph TD
    A[File Upload/URL] --> B{File Type?}
    B -->|Python| C[Python Parser]
    B -->|JavaScript| D[JavaScript Parser]
    B -->|TypeScript| E[TypeScript Parser]

    C --> F[AST Generation]
    D --> F
    E --> F

    F --> G[Content Extraction]
    G --> H[Chunking Strategy]
    H --> I[Embedding Generation]
    I --> J[Vector Storage]
    I --> K[Metadata Storage]

    J --> L[Qdrant]
    K --> M[PostgreSQL]
```

### 4.2 AST-based Code Parsing

```python
# app/processing/parsers/python_parser.py
import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.processing.parsers.base import BaseParser, ParsedContent


@dataclass
class PythonFunction:
    name: str
    docstring: Optional[str]
    parameters: List[Dict[str, Any]]
    returns: Optional[str]
    decorators: List[str]
    complexity: int
    start_line: int
    end_line: int
    body: str


class PythonParser(BaseParser):
    """Parser for Python source code using AST."""

    def parse(self, content: str, file_path: str) -> List[ParsedContent]:
        """Parse Python source code and extract meaningful chunks."""
        try:
            tree = ast.parse(content)
            parsed_contents = []

            # Extract module-level docstring
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                parsed_contents.append(ParsedContent(
                    content_type="module",
                    content_name=file_path,
                    content=module_docstring,
                    file_path=file_path,
                    start_line=1,
                    end_line=self._get_docstring_end_line(content, module_docstring),
                    metadata={"type": "docstring"}
                ))

            # Process all nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    parsed_contents.append(self._parse_function(node, content, file_path))
                elif isinstance(node, ast.ClassDef):
                    parsed_contents.append(self._parse_class(node, content, file_path))

            return parsed_contents

        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}")
            return []

    def _parse_function(self, node: ast.FunctionDef, source: str, file_path: str) -> ParsedContent:
        """Parse a function definition."""
        # Extract function details
        docstring = ast.get_docstring(node)
        parameters = self._extract_parameters(node)
        returns = self._extract_return_type(node)
        decorators = self._extract_decorators(node)
        complexity = self._calculate_complexity(node)

        # Get function source code
        function_source = ast.get_source_segment(source, node)

        return ParsedContent(
            content_type="function",
            content_name=node.name,
            content=function_source,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            metadata={
                "docstring": docstring,
                "parameters": parameters,
                "returns": returns,
                "decorators": decorators,
                "complexity": complexity,
                "is_async": isinstance(node, ast.AsyncFunctionDef)
            }
        )

    def _parse_class(self, node: ast.ClassDef, source: str, file_path: str) -> ParsedContent:
        """Parse a class definition."""
        docstring = ast.get_docstring(node)
        methods = []

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    "name": item.name,
                    "is_async": isinstance(item, ast.AsyncFunctionDef),
                    "decorators": self._extract_decorators(item)
                })

        class_source = ast.get_source_segment(source, node)

        return ParsedContent(
            content_type="class",
            content_name=node.name,
            content=class_source,
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno,
            metadata={
                "docstring": docstring,
                "methods": methods,
                "bases": [self._get_name(base) for base in node.bases],
                "decorators": self._extract_decorators(node)
            }
        )

    def _extract_parameters(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract function parameters with types if available."""
        params = []
        for arg in node.args.args:
            param = {"name": arg.arg}
            if arg.annotation:
                param["type"] = ast.unparse(arg.annotation)
            params.append(param)
        return params

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity
```

### 4.3 Chunking Strategies

```python
# app/processing/chunkers/ast_chunker.py
from typing import List, Dict, Any
from app.processing.chunkers.base import BaseChunker, Chunk
from app.processing.parsers.base import ParsedContent


class ASTChunker(BaseChunker):
    """Intelligent chunking based on AST analysis."""

    def __init__(
        self,
        max_chunk_size: int = 2000,
        overlap_size: int = 200,
        min_chunk_size: int = 100
    ):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size

    def chunk(self, parsed_contents: List[ParsedContent]) -> List[Chunk]:
        """Create chunks from parsed content."""
        chunks = []

        for content in parsed_contents:
            # Small content doesn't need chunking
            if len(content.content) <= self.max_chunk_size:
                chunks.append(self._create_chunk(content))
                continue

            # Large content needs intelligent chunking
            if content.content_type == "class":
                chunks.extend(self._chunk_class(content))
            elif content.content_type == "function":
                chunks.extend(self._chunk_function(content))
            else:
                chunks.extend(self._chunk_generic(content))

        return chunks

    def _chunk_class(self, content: ParsedContent) -> List[Chunk]:
        """Chunk a large class intelligently."""
        chunks = []

        # Extract class definition and docstring as first chunk
        lines = content.content.split('\n')
        class_header = []
        in_docstring = False
        docstring_complete = False

        for i, line in enumerate(lines):
            class_header.append(line)

            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                else:
                    docstring_complete = True

            if docstring_complete and line.strip() == "":
                break

        # Create header chunk
        header_content = '\n'.join(class_header)
        chunks.append(Chunk(
            content=header_content,
            content_type="class_header",
            metadata={
                **content.metadata,
                "chunk_type": "header",
                "parent_name": content.content_name
            },
            start_line=content.start_line,
            end_line=content.start_line + len(class_header)
        ))

        # Chunk methods separately
        # This would require re-parsing the class body
        # For now, chunk the remaining content
        remaining_content = '\n'.join(lines[len(class_header):])
        if remaining_content.strip():
            chunks.extend(self._chunk_by_size(
                remaining_content,
                content_type="class_body",
                base_metadata={
                    **content.metadata,
                    "chunk_type": "body",
                    "parent_name": content.content_name
                }
            ))

        return chunks

    def _chunk_by_size(
        self,
        content: str,
        content_type: str,
        base_metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """Chunk content by size with overlap."""
        chunks = []
        lines = content.split('\n')

        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > self.max_chunk_size and current_chunk:
                # Create chunk
                chunk_content = '\n'.join(current_chunk)
                chunks.append(Chunk(
                    content=chunk_content,
                    content_type=content_type,
                    metadata={
                        **base_metadata,
                        "chunk_index": len(chunks)
                    }
                ))

                # Keep overlap
                overlap_lines = []
                overlap_size = 0
                for i in range(len(current_chunk) - 1, -1, -1):
                    line_len = len(current_chunk[i]) + 1
                    if overlap_size + line_len <= self.overlap_size:
                        overlap_lines.insert(0, current_chunk[i])
                        overlap_size += line_len
                    else:
                        break

                current_chunk = overlap_lines
                current_size = overlap_size

            current_chunk.append(line)
            current_size += line_size

        # Add final chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append(Chunk(
                content=chunk_content,
                content_type=content_type,
                metadata={
                    **base_metadata,
                    "chunk_index": len(chunks)
                }
            ))

        return chunks
```

### 4.4 Embedding Generation with OpenAI

```python
# app/processing/embedders/openai_embedder.py
import asyncio
from typing import List, Dict, Any
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
from app.processing.embedders.base import BaseEmbedder
from app.core.config import settings
from app.core.logging import logger


class OpenAIEmbedder(BaseEmbedder):
    """Generate embeddings using OpenAI's API."""

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.dimension = settings.OPENAI_EMBEDDING_DIMENSION
        self.batch_size = 100  # OpenAI's limit

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching."""
        all_embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]

            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    encoding_format="float"
                )

                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

            except Exception as e:
                logger.error(f"Error generating batch embeddings: {e}")
                # Generate individually as fallback
                for text in batch:
                    try:
                        embedding = await self.generate_embedding(text)
                        all_embeddings.append(embedding)
                    except Exception as e:
                        logger.error(f"Failed to generate embedding for text: {e}")
                        # Use zero vector as fallback
                        all_embeddings.append([0.0] * self.dimension)

        return all_embeddings

    async def generate_embeddings_with_metadata(
        self,
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for items with metadata.

        Args:
            items: List of dicts with 'text' and 'metadata' keys

        Returns:
            List of dicts with 'embedding' and 'metadata' keys
        """
        texts = [item['text'] for item in items]
        embeddings = await self.generate_embeddings(texts)

        results = []
        for item, embedding in zip(items, embeddings):
            results.append({
                'embedding': embedding,
                'metadata': item['metadata']
            })

        return results
```

### 4.5 Vector Storage Optimization

```python
# app/services/context_service.py
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.context_repo import ContextRepository
from app.services.vector_service import VectorService
from app.processing.pipeline import ProcessingPipeline
from app.models.schemas.request.context import ContextCreate
from app.core.logging import logger


class ContextService:
    """Service for managing context processing and storage."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.context_repo = ContextRepository(db)
        self.pipeline = ProcessingPipeline()

    async def process_files(
        self,
        project_id: UUID,
        files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process multiple files and store contexts.

        Args:
            project_id: Project ID
            files: List of file data with 'path' and 'content'

        Returns:
            Processing summary
        """
        total_contexts = 0
        processed_files = 0
        errors = []

        # Process files concurrently with controlled parallelism
        semaphore = asyncio.Semaphore(settings.MAX_WORKERS)

        async def process_file(file_data: Dict[str, Any]):
            async with semaphore:
                try:
                    contexts = await self._process_single_file(
                        project_id,
                        file_data['path'],
                        file_data['content']
                    )
                    return len(contexts), None
                except Exception as e:
                    logger.error(f"Error processing {file_data['path']}: {e}")
                    return 0, str(e)

        # Process all files
        tasks = [process_file(f) for f in files]
        results = await asyncio.gather(*tasks)

        # Aggregate results
        for count, error in results:
            if error:
                errors.append(error)
            else:
                total_contexts += count
                processed_files += 1

        return {
            "processed_files": processed_files,
            "total_contexts": total_contexts,
            "errors": errors
        }

    async def _process_single_file(
        self,
        project_id: UUID,
        file_path: str,
        content: str
    ) -> List[UUID]:
        """Process a single file and store contexts."""
        # Parse and chunk the file
        chunks = await self.pipeline.process(content, file_path)

        if not chunks:
            return []

        # Prepare contexts for storage
        contexts_data = []
        texts_for_embedding = []

        for chunk in chunks:
            context_data = {
                "project_id": project_id,
                "file_path": file_path,
                "content_type": chunk.content_type,
                "content_name": chunk.metadata.get("name"),
                "content": chunk.content,
                "language": chunk.metadata.get("language", "unknown"),
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "ast_metadata": chunk.metadata.get("ast", {}),
                "dependencies": chunk.metadata.get("dependencies", {}),
                "complexity_metrics": chunk.metadata.get("complexity", {})
            }
            contexts_data.append(context_data)

            # Prepare text for embedding
            embedding_text = self._prepare_embedding_text(context_data)
            texts_for_embedding.append(embedding_text)

        # Generate embeddings in batch
        embeddings = await self.pipeline.embedder.generate_embeddings(texts_for_embedding)

        # Store contexts with embeddings
        context_ids = []
        vector_points = []

        for context_data, embedding in zip(contexts_data, embeddings):
            # Store in PostgreSQL
            context = await self.context_repo.create(context_data)
            context_ids.append(context.id)

            # Prepare for vector storage
            vector_points.append({
                "id": context.id,
                "vector": embedding,
                "payload": {
                    "project_id": str(project_id),
                    "file_path": file_path,
                    "content_type": context.content_type,
                    "content_name": context.content_name,
                    "language": context.language,
                    "preview": context.content[:200]  # Store preview for quick access
                }
            })

        # Store embeddings in Qdrant
        await VectorService.upsert_embeddings(vector_points)

        return context_ids

    def _prepare_embedding_text(self, context_data: Dict[str, Any]) -> str:
        """Prepare text for embedding generation."""
        parts = []

        # Add content type and name
        if context_data.get("content_name"):
            parts.append(f"{context_data['content_type']}: {context_data['content_name']}")
        else:
            parts.append(f"{context_data['content_type']}")

        # Add file path context
        parts.append(f"File: {context_data['file_path']}")

        # Add main content
        parts.append(context_data['content'])

        # Add important metadata
        if context_data.get("ast_metadata", {}).get("docstring"):
            parts.append(f"Documentation: {context_data['ast_metadata']['docstring']}")

        return "\n\n".join(parts)
```

---

## 5. Performance Considerations

### 5.1 Async/Await Patterns

```python
# app/utils/async_utils.py
import asyncio
from typing import List, Callable, TypeVar, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
import time
from app.core.logging import logger

T = TypeVar('T')


class AsyncBatcher:
    """Batch async operations for improved performance."""

    def __init__(
        self,
        batch_size: int = 100,
        timeout: float = 0.1
    ):
        self.batch_size = batch_size
        self.timeout = timeout
        self._queue: List[Any] = []
        self._results: Dict[int, Any] = {}
        self._lock = asyncio.Lock()
        self._process_task: Optional[asyncio.Task] = None

    async def add(self, item: Any) -> Any:
        """Add item to batch and get result when processed."""
        async with self._lock:
            item_id = len(self._queue)
            self._queue.append((item_id, item))

            # Start processing if not already running
            if self._process_task is None or self._process_task.done():
                self._process_task = asyncio.create_task(self._process_batch())

        # Wait for result
        while item_id not in self._results:
            await asyncio.sleep(0.01)

        return self._results.pop(item_id)

    async def _process_batch(self):
        """Process accumulated batch."""
        await asyncio.sleep(self.timeout)

        async with self._lock:
            if not self._queue:
                return

            # Extract batch
            batch = self._queue[:self.batch_size]
            self._queue = self._queue[self.batch_size:]

        # Process batch (override in subclass)
        results = await self._process_items([item for _, item in batch])

        # Store results
        for (item_id, _), result in zip(batch, results):
            self._results[item_id] = result


async def run_async_with_timeout(
    coro: Callable[..., T],
    timeout: float,
    *args,
    **kwargs
) -> Optional[T]:
    """Run async function with timeout."""
    try:
        return await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Async operation timed out after {timeout}s")
        return None


async def gather_with_concurrency(
    n: int,
    *coros: Callable[..., T]
) -> List[T]:
    """Gather results with limited concurrency."""
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator for retrying async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay

            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise

                    logger.warning(
                        f"Attempt {attempt} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1

        return wrapper
    return decorator


# Thread pool for CPU-bound operations
_thread_pool = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)


async def run_in_thread(func: Callable[..., T], *args, **kwargs) -> T:
    """Run CPU-bound function in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _thread_pool,
        partial(func, *args, **kwargs)
    )
```

### 5.2 Background Task Processing

```python
# app/services/background_service.py
from typing import Any, Dict, Optional, Callable
from uuid import UUID, uuid4
import asyncio
from datetime import datetime
from enum import Enum
from fastapi import BackgroundTasks
from app.core.logging import logger
from app.utils.cache import redis_client


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskManager:
    """Manage background tasks with status tracking."""

    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}

    async def create_task(
        self,
        func: Callable,
        *args,
        task_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create and track a background task."""
        task_id = task_id or str(uuid4())

        # Store initial status
        await self._update_status(task_id, TaskStatus.PENDING)

        # Create task
        task = asyncio.create_task(
            self._run_task(task_id, func, *args, **kwargs)
        )
        self._tasks[task_id] = task

        return task_id

    async def _run_task(
        self,
        task_id: str,
        func: Callable,
        *args,
        **kwargs
    ):
        """Run task with status updates."""
        try:
            await self._update_status(task_id, TaskStatus.RUNNING)

            # Execute function
            result = await func(*args, **kwargs)

            await self._update_status(
                task_id,
                TaskStatus.COMPLETED,
                result=result
            )

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self._update_status(
                task_id,
                TaskStatus.FAILED,
                error=str(e)
            )
            raise
        finally:
            # Clean up
            self._tasks.pop(task_id, None)

    async def _update_status(
        self,
        task_id: str,
        status: TaskStatus,
        **extra_data
    ):
        """Update task status in Redis."""
        status_data = {
            "status": status.value,
            "updated_at": datetime.utcnow().isoformat(),
            **extra_data
        }

        key = redis_client.cache_key("task", task_id)
        await redis_client.set(key, status_data, ttl=86400)  # 24 hours

    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        key = redis_client.cache_key("task", task_id)
        return await redis_client.get(key)

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self._tasks.get(task_id)
        if task and not task.done():
            task.cancel()
            await self._update_status(task_id, TaskStatus.FAILED, error="Cancelled")
            return True
        return False


# Global task manager
task_manager = TaskManager()


# FastAPI integration
def create_background_task(
    background_tasks: BackgroundTasks,
    func: Callable,
    *args,
    **kwargs
) -> str:
    """Create a tracked background task."""
    task_id = str(uuid4())

    async def wrapped_task():
        await task_manager.create_task(func, *args, task_id=task_id, **kwargs)

    background_tasks.add_task(wrapped_task)
    return task_id
```

### 5.3 Request Batching

```python
# app/services/batch_service.py
from typing import List, Dict, Any, Optional, Callable
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from app.core.logging import logger


class BatchProcessor:
    """Process requests in batches for improved performance."""

    def __init__(
        self,
        process_func: Callable[[List[Any]], List[Any]],
        batch_size: int = 100,
        batch_timeout: float = 0.1,
        max_wait_time: float = 1.0
    ):
        self.process_func = process_func
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.max_wait_time = max_wait_time

        self._queue: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._process_task: Optional[asyncio.Task] = None
        self._shutdown = False

    async def add_request(self, request_data: Any) -> Any:
        """Add request to batch and wait for result."""
        if self._shutdown:
            raise RuntimeError("Batch processor is shutting down")

        # Create future for result
        future = asyncio.Future()

        async with self._lock:
            self._queue.append({
                "data": request_data,
                "future": future,
                "timestamp": datetime.utcnow()
            })

            # Start processing if needed
            if self._process_task is None or self._process_task.done():
                self._process_task = asyncio.create_task(self._process_batch())

        # Wait for result
        return await future

    async def _process_batch(self):
        """Process accumulated batch."""
        await asyncio.sleep(self.batch_timeout)

        async with self._lock:
            if not self._queue:
                return

            # Determine batch to process
            now = datetime.utcnow()
            batch = []
            remaining = []

            for item in self._queue:
                age = (now - item["timestamp"]).total_seconds()

                if len(batch) < self.batch_size and age < self.max_wait_time:
                    batch.append(item)
                else:
                    remaining.append(item)

            self._queue = remaining

        if not batch:
            return

        # Process batch
        try:
            request_data = [item["data"] for item in batch]
            results = await self.process_func(request_data)

            # Deliver results
            for item, result in zip(batch, results):
                item["future"].set_result(result)

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # Deliver errors
            for item in batch:
                item["future"].set_exception(e)

    async def shutdown(self):
        """Shutdown batch processor."""
        self._shutdown = True

        # Process remaining items
        if self._queue:
            await self._process_batch()

        # Cancel ongoing task
        if self._process_task and not self._process_task.done():
            self._process_task.cancel()


# Example usage for embedding generation
class EmbeddingBatchProcessor(BatchProcessor):
    """Batch processor for embedding generation."""

    def __init__(self, embedder):
        async def process_batch(texts: List[str]) -> List[List[float]]:
            return await embedder.generate_embeddings(texts)

        super().__init__(
            process_func=process_batch,
            batch_size=100,  # OpenAI limit
            batch_timeout=0.05,
            max_wait_time=0.5
        )
```

### 5.4 Caching Strategies

```python
# app/decorators/cache.py
from typing import Optional, Callable, Any
from functools import wraps
import hashlib
import json
from app.utils.cache import redis_client
from app.core.logging import logger


def cache_key_builder(
    prefix: str,
    include_args: bool = True,
    include_kwargs: bool = True,
    exclude_params: Optional[List[str]] = None
) -> Callable:
    """Build cache key from function arguments."""
    exclude_params = exclude_params or []

    def key_builder(func_name: str, *args, **kwargs) -> str:
        parts = [prefix, func_name]

        if include_args:
            # Skip 'self' or 'cls' for methods
            args_to_include = args[1:] if args and hasattr(args[0], '__class__') else args
            parts.extend(str(arg) for arg in args_to_include)

        if include_kwargs:
            filtered_kwargs = {
                k: v for k, v in kwargs.items()
                if k not in exclude_params
            }
            if filtered_kwargs:
                kwargs_str = json.dumps(filtered_kwargs, sort_keys=True)
                parts.append(hashlib.md5(kwargs_str.encode()).hexdigest())

        return ":".join(parts)

    return key_builder


def cached(
    prefix: str,
    ttl: Optional[int] = 3600,
    key_builder: Optional[Callable] = None,
    condition: Optional[Callable[..., bool]] = None
):
    """
    Decorator for caching function results.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_builder: Custom key builder function
        condition: Function to determine if result should be cached
    """
    if key_builder is None:
        key_builder = cache_key_builder(prefix)

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check if caching is applicable
            if condition and not condition(*args, **kwargs):
                return await func(*args, **kwargs)

            # Build cache key
            cache_key = key_builder(func.__name__, *args, **kwargs)

            # Try to get from cache
            try:
                cached_result = await redis_client.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache get error: {e}")

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            try:
                if result is not None:
                    await redis_client.set(cache_key, result, ttl)
                    logger.debug(f"Cached result: {cache_key}")
            except Exception as e:
                logger.warning(f"Cache set error: {e}")

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async cache
            # Just execute the function
            return func(*args, **kwargs)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def invalidate_cache(pattern: str):
    """Decorator to invalidate cache entries matching pattern after function execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache
            try:
                keys = await redis_client.get_client().keys(pattern)
                if keys:
                    await redis_client.delete(keys)
                    logger.debug(f"Invalidated {len(keys)} cache entries")
            except Exception as e:
                logger.warning(f"Cache invalidation error: {e}")

            return result
        return wrapper
    return decorator


# Usage examples
class ProjectService:
    @cached(prefix="project", ttl=3600)
    async def get_project(self, project_id: UUID) -> Project:
        # This will be cached for 1 hour
        return await self.repo.get(project_id)

    @invalidate_cache("project:*")
    async def update_project(self, project_id: UUID, data: ProjectUpdate) -> Project:
        # This will invalidate all project cache entries
        return await self.repo.update(project_id, data)
```

### 5.5 Connection Pooling

```python
# app/db/connection_pool.py
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.pool import NullPool, QueuePool
from qdrant_client import QdrantClient
from redis.asyncio import Redis, ConnectionPool as RedisPool
import aiohttp
from app.core.config import settings
from app.core.logging import logger


class ConnectionManager:
    """Centralized connection pool management."""

    def __init__(self):
        self._engines: Dict[str, AsyncEngine] = {}
        self._redis_pools: Dict[str, RedisPool] = {}
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._qdrant_clients: Dict[str, QdrantClient] = {}
        self._lock = asyncio.Lock()

    async def get_db_engine(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 40
    ) -> AsyncEngine:
        """Get or create database engine with connection pooling."""
        if database_url not in self._engines:
            async with self._lock:
                if database_url not in self._engines:
                    engine = create_async_engine(
                        database_url,
                        pool_size=pool_size,
                        max_overflow=max_overflow,
                        pool_pre_ping=True,
                        pool_recycle=3600,
                        echo=False
                    )
                    self._engines[database_url] = engine
                    logger.info(f"Created database engine with pool size {pool_size}")

        return self._engines[database_url]

    async def get_redis_pool(
        self,
        redis_url: str,
        max_connections: int = 10
    ) -> Redis:
        """Get or create Redis connection pool."""
        if redis_url not in self._redis_pools:
            async with self._lock:
                if redis_url not in self._redis_pools:
                    pool = RedisPool.from_url(
                        redis_url,
                        max_connections=max_connections,
                        decode_responses=True,
                        socket_keepalive=True,
                        socket_keepalive_options={
                            1: 1,  # TCP_KEEPIDLE
                            2: 2,  # TCP_KEEPINTVL
                            3: 3,  # TCP_KEEPCNT
                        }
                    )
                    self._redis_pools[redis_url] = pool
                    logger.info(f"Created Redis pool with {max_connections} connections")

        return Redis(connection_pool=self._redis_pools[redis_url])

    async def get_http_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with connection pooling."""
        if self._http_session is None or self._http_session.closed:
            async with self._lock:
                if self._http_session is None or self._http_session.closed:
                    connector = aiohttp.TCPConnector(
                        limit=100,  # Total connection pool size
                        limit_per_host=30,  # Per-host connection limit
                        ttl_dns_cache=300,  # DNS cache timeout
                        enable_cleanup_closed=True
                    )

                    timeout = aiohttp.ClientTimeout(
                        total=30,
                        connect=5,
                        sock_read=10
                    )

                    self._http_session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout,
                        headers={
                            "User-Agent": f"Mobius/{settings.VERSION}"
                        }
                    )
                    logger.info("Created HTTP session with connection pooling")

        return self._http_session

    async def get_qdrant_client(
        self,
        host: str = settings.QDRANT_HOST,
        port: int = settings.QDRANT_PORT
    ) -> QdrantClient:
        """Get or create Qdrant client."""
        key = f"{host}:{port}"

        if key not in self._qdrant_clients:
            async with self._lock:
                if key not in self._qdrant_clients:
                    client = QdrantClient(
                        host=host,
                        port=port,
                        api_key=settings.QDRANT_API_KEY,
                        timeout=30,
                        prefer_grpc=True  # Use gRPC for better performance
                    )
                    self._qdrant_clients[key] = client
                    logger.info(f"Created Qdrant client for {key}")

        return self._qdrant_clients[key]

    async def close_all(self):
        """Close all connections."""
        # Close database engines
        for engine in self._engines.values():
            await engine.dispose()
        self._engines.clear()

        # Close Redis pools
        for pool in self._redis_pools.values():
            await pool.disconnect()
        self._redis_pools.clear()

        # Close HTTP session
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()

        # Close Qdrant clients
        for client in self._qdrant_clients.values():
            client.close()
        self._qdrant_clients.clear()

        logger.info("Closed all connection pools")


# Global connection manager
connection_manager = ConnectionManager()


# Context managers for easy usage
@asynccontextmanager
async def get_db_session():
    """Get database session from pool."""
    engine = await connection_manager.get_db_engine(str(settings.DATABASE_URL))
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_redis_client():
    """Get Redis client from pool."""
    client = await connection_manager.get_redis_pool(str(settings.REDIS_URL))
    try:
        yield client
    finally:
        # Connection is returned to pool automatically
        pass
```

---

## 6. Security Architecture

### 6.1 Authentication with OAuth2 + JWT

```python
# app/core/security.py
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise ValueError("Invalid token")


# API Key management
import secrets
import hashlib


def generate_api_key() -> tuple[str, str]:
    """Generate API key and its hash."""
    # Generate a secure random API key
    api_key = f"mbx_{secrets.token_urlsafe(32)}"

    # Hash the API key for storage
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    return api_key, api_key_hash


def verify_api_key(api_key: str, api_key_hash: str) -> bool:
    """Verify an API key against its hash."""
    return hashlib.sha256(api_key.encode()).hexdigest() == api_key_hash
```

### 6.2 Input Validation and Sanitization

```python
# app/utils/validators.py
import re
from typing import Any, Optional
from pathlib import Path
import magic
from app.api.error_handlers import APIException
from fastapi import status


class InputValidator:
    """Centralized input validation utilities."""

    # Regex patterns
    FILE_PATH_PATTERN = re.compile(r'^[\w\-./]+$')
    URL_PATTERN = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    # File validation
    ALLOWED_EXTENSIONS = {
        'python': ['.py', '.pyi'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'markdown': ['.md', '.markdown'],
        'json': ['.json'],
        'yaml': ['.yml', '.yaml']
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def validate_file_path(cls, file_path: str) -> str:
        """Validate and sanitize file path."""
        # Remove any null bytes
        file_path = file_path.replace('\x00', '')

        # Normalize path
        path = Path(file_path)
        normalized = path.as_posix()

        # Check for path traversal
        if '..' in normalized or normalized.startswith('/'):
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path",
                error_code="INVALID_FILE_PATH"
            )

        # Check pattern
        if not cls.FILE_PATH_PATTERN.match(normalized):
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File path contains invalid characters",
                error_code="INVALID_FILE_PATH"
            )

        return normalized

    @classmethod
    def validate_file_content(
        cls,
        content: bytes,
        expected_type: Optional[str] = None
    ) -> str:
        """Validate file content and detect type."""
        # Check file size
        if len(content) > cls.MAX_FILE_SIZE:
            raise APIException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum of {cls.MAX_FILE_SIZE} bytes",
                error_code="FILE_TOO_LARGE"
            )

        # Detect file type
        file_type = magic.from_buffer(content, mime=True)

        # Validate against expected type
        if expected_type:
            allowed_types = {
                'python': ['text/x-python', 'text/plain'],
                'javascript': ['application/javascript', 'text/javascript', 'text/plain'],
                'typescript': ['application/typescript', 'text/typescript', 'text/plain'],
                'json': ['application/json', 'text/plain'],
                'yaml': ['application/x-yaml', 'text/yaml', 'text/plain']
            }

            if file_type not in allowed_types.get(expected_type, []):
                raise APIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type mismatch. Expected {expected_type}, got {file_type}",
                    error_code="FILE_TYPE_MISMATCH"
                )

        return file_type

    @classmethod
    def validate_url(cls, url: str) -> str:
        """Validate and sanitize URL."""
        # Remove whitespace
        url = url.strip()

        # Check pattern
        if not cls.URL_PATTERN.match(url):
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format",
                error_code="INVALID_URL"
            )

        # Additional checks for security
        blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
        parsed = urlparse(url)

        if parsed.hostname in blocked_hosts:
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL points to blocked host",
                error_code="BLOCKED_HOST"
            )

        return url

    @classmethod
    def sanitize_user_input(cls, text: str, max_length: int = 10000) -> str:
        """Sanitize user input text."""
        # Remove null bytes
        text = text.replace('\x00', '')

        # Limit length
        if len(text) > max_length:
            text = text[:max_length]

        # Remove control characters (except newlines and tabs)
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)

        return text.strip()


# Pydantic validators
from pydantic import field_validator


class SecureProjectCreate(ProjectCreate):
    """Project creation with additional validation."""

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        # Check for SQL injection patterns
        sql_patterns = ['--', '/*', '*/', 'xp_', 'sp_', ';', 'UNION', 'SELECT']
        v_lower = v.lower()

        for pattern in sql_patterns:
            if pattern.lower() in v_lower:
                raise ValueError("Project name contains invalid characters")

        return InputValidator.sanitize_user_input(v, max_length=255)

    @field_validator('repository_url')
    @classmethod
    def validate_repository_url(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return InputValidator.validate_url(v)
        return v
```

### 6.3 API Security Middleware

```python
# app/middleware/security.py
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import logger
import uuid


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add security headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Remove server header
        response.headers.pop("Server", None)

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with security context."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client info
        client_host = request.client.host if request.client else "unknown"

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_host} "
            f"(ID: {getattr(request.state, 'request_id', 'unknown')})"
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Response: {response.status_code} "
            f"for {request.method} {request.url.path} "
            f"(ID: {getattr(request.state, 'request_id', 'unknown')})"
        )

        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist middleware for admin endpoints."""

    def __init__(self, app, whitelist: List[str]):
        super().__init__(app)
        self.whitelist = whitelist

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check admin endpoints
        if request.url.path.startswith("/admin"):
            client_host = request.client.host if request.client else None

            # Get real IP from headers if behind proxy
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                client_host = forwarded.split(',')[0].strip()

            if client_host not in self.whitelist:
                logger.warning(f"Blocked admin access from {client_host}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )

        return await call_next(request)
```

---

## 7. Development Standards

### 7.1 Code Style and Type Hints

```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  migrations
  | .git
  | .mypy_cache
  | .tox
  | venv
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

### 7.2 Testing Strategy

```python
# tests/conftest.py
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.main import app
from app.db.database import Base
from app.core.config import settings
from app.core.security import get_password_hash


# Override settings for testing
settings.DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_mobius"
settings.REDIS_URL = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user) -> AsyncClient:
    """Create authenticated test client."""
    # Login and get token
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": test_user.username, "password": "testpass123"}
    )
    token = response.json()["access_token"]

    # Set authorization header
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create test user."""
    from app.models.database.models import User

    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user
```

### 7.3 API Testing Examples

```python
# tests/api/test_projects.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database.models import Project


class TestProjectAPI:
    """Test project API endpoints."""

    async def test_create_project(
        self,
        authenticated_client: AsyncClient,
        test_user
    ):
        """Test project creation."""
        response = await authenticated_client.post(
            "/api/v1/projects/",
            json={
                "name": "Test Project",
                "description": "A test project",
                "language": "python",
                "tags": ["test", "demo"]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["owner_id"] == str(test_user.id)
        assert "id" in data

    async def test_list_projects(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user
    ):
        """Test project listing with pagination."""
        # Create test projects
        for i in range(5):
            project = Project(
                name=f"Project {i}",
                language="python",
                owner_id=test_user.id
            )
            db_session.add(project)
        await db_session.commit()

        # Test pagination
        response = await authenticated_client.get(
            "/api/v1/projects/?skip=0&limit=3"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 5
        assert data["skip"] == 0
        assert data["limit"] == 3

    async def test_get_project_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test getting non-existent project."""
        response = await authenticated_client.get(
            "/api/v1/projects/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    async def test_update_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user
    ):
        """Test project update."""
        # Create project
        project = Project(
            name="Original Name",
            language="python",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Update project
        response = await authenticated_client.patch(
            f"/api/v1/projects/{project.id}",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    async def test_delete_project(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        test_user
    ):
        """Test project deletion."""
        # Create project
        project = Project(
            name="To Delete",
            language="python",
            owner_id=test_user.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        # Delete project
        response = await authenticated_client.delete(
            f"/api/v1/projects/{project.id}"
        )

        assert response.status_code == 204

        # Verify deletion
        deleted = await db_session.get(Project, project.id)
        assert deleted is None
```

### 7.4 Performance Testing

```python
# tests/performance/test_load.py
import asyncio
import time
from typing import List
import aiohttp
import pytest
from statistics import mean, stdev


class TestPerformance:
    """Performance and load tests."""

    @pytest.mark.performance
    async def test_concurrent_requests(self, base_url: str, auth_token: str):
        """Test handling of concurrent requests."""
        async def make_request(session: aiohttp.ClientSession) -> float:
            start = time.time()
            async with session.get(
                f"{base_url}/api/v1/projects",
                headers={"Authorization": f"Bearer {auth_token}"}
            ) as response:
                await response.json()
                return time.time() - start

        # Configure test
        num_requests = 100
        max_concurrent = 10

        async with aiohttp.ClientSession() as session:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)

            async def bounded_request(session):
                async with semaphore:
                    return await make_request(session)

            # Execute requests
            tasks = [bounded_request(session) for _ in range(num_requests)]
            response_times = await asyncio.gather(*tasks)

        # Analyze results
        avg_time = mean(response_times)
        std_dev = stdev(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        print(f"\nPerformance Results:")
        print(f"  Total requests: {num_requests}")
        print(f"  Concurrent requests: {max_concurrent}")
        print(f"  Average response time: {avg_time:.3f}s")
        print(f"  Standard deviation: {std_dev:.3f}s")
        print(f"  Min response time: {min_time:.3f}s")
        print(f"  Max response time: {max_time:.3f}s")

        # Assert performance requirements
        assert avg_time < 0.2  # Average under 200ms
        assert max_time < 1.0  # No request over 1s

    @pytest.mark.performance
    async def test_vector_search_performance(
        self,
        vector_service,
        sample_embeddings: List[List[float]]
    ):
        """Test vector search performance."""
        # Insert test embeddings
        await vector_service.upsert_embeddings([
            {
                "id": str(i),
                "vector": embedding,
                "payload": {"test_id": i}
            }
            for i, embedding in enumerate(sample_embeddings[:1000])
        ])

        # Perform searches
        search_times = []
        for i in range(50):
            query_vector = sample_embeddings[i]

            start = time.time()
            results = await vector_service.search(
                query_vector=query_vector,
                limit=10
            )
            search_times.append(time.time() - start)

        # Analyze results
        avg_search_time = mean(search_times)

        print(f"\nVector Search Performance:")
        print(f"  Average search time: {avg_search_time:.3f}s")
        print(f"  Searches per second: {1/avg_search_time:.1f}")

        # Assert performance requirements
        assert avg_search_time < 0.05  # Under 50ms average
```

---

## 8. Deployment Architecture

### 8.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Development stage
FROM base as development
RUN pip install --no-cache-dir -r requirements-dev.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

# Create non-root user
RUN useradd -m -u 1000 mobius && chown -R mobius:mobius /app
USER mobius

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

### 8.2 Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: mobius
      POSTGRES_PASSWORD: mobius_dev
      POSTGRES_DB: mobius
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mobius"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__SERVICE__GRPC_PORT: 6334

  app:
    build:
      context: .
      target: development
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
    environment:
      DATABASE_URL: postgresql+asyncpg://mobius:mobius_dev@postgres/mobius
      REDIS_URL: redis://redis:6379/0
      QDRANT_HOST: qdrant
      QDRANT_PORT: 6333
      SECRET_KEY: ${SECRET_KEY:-your-secret-key-here}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    volumes:
      - ./app:/app/app
      - ./tests:/app/tests
    ports:
      - "8000:8000"
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
      "

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

### 8.3 Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mobius-api
  labels:
    app: mobius
    component: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mobius
      component: api
  template:
    metadata:
      labels:
        app: mobius
        component: api
    spec:
      containers:
      - name: api
        image: mobius/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: mobius-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: mobius-secrets
              key: redis-url
        - name: QDRANT_HOST
          value: qdrant-service
        - name: QDRANT_PORT
          value: "6333"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: mobius-secrets
              key: secret-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: mobius-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: mobius-api-service
spec:
  selector:
    app: mobius
    component: api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mobius-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mobius-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 8.4 Production Configuration

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mobius-config
data:
  # Application settings
  PROJECT_NAME: "Mobius Context Engineering Platform"
  API_V1_STR: "/api/v1"

  # Performance settings
  DATABASE_POOL_SIZE: "20"
  DATABASE_MAX_OVERFLOW: "40"
  REDIS_POOL_SIZE: "10"
  BATCH_SIZE: "100"
  MAX_WORKERS: "4"

  # Rate limiting
  RATE_LIMIT_PER_MINUTE: "60"
  RATE_LIMIT_PER_HOUR: "1000"

  # OpenAI settings
  OPENAI_MODEL: "text-embedding-3-small"
  OPENAI_EMBEDDING_DIMENSION: "1536"
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mobius-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  tls:
  - hosts:
    - api.mobius.example.com
    secretName: mobius-tls
  rules:
  - host: api.mobius.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mobius-api-service
            port:
              number: 80
```

---

## Conclusion

This architectural design provides a solid foundation for Phase 1 of the Mobius Context Engineering Platform. The design emphasizes:

1. **Performance**: Async/await patterns, connection pooling, and caching strategies ensure sub-200ms response times
2. **Scalability**: Horizontal scaling with Kubernetes, efficient batching, and distributed caching
3. **Security**: Multi-layer security with OAuth2+JWT, input validation, and secure defaults
4. **Maintainability**: Clean architecture, comprehensive testing, and clear separation of concerns
5. **Developer Experience**: Type safety, dependency injection, and comprehensive documentation

The architecture is designed to evolve smoothly into Phase 2 and beyond, with clear extension points for GraphQL, WebSocket support, and advanced features like the multi-agent system.

### Next Steps

1. Set up the development environment using Docker Compose
2. Implement the core domain models and database schema
3. Build the authentication and authorization system
4. Develop the context processing pipeline
5. Create comprehensive test suites
6. Deploy to a staging environment for integration testing

This foundation will enable the team to build a robust, scalable platform that meets the performance and reliability requirements outlined in the project plan.
