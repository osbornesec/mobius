"""Database foundation module with async SQLAlchemy setup."""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create declarative base for models
Base = declarative_base()


def create_engine():
    """Create async engine with connection pooling configuration."""
    settings = get_settings()

    # Choose pool class based on environment
    if settings.ENVIRONMENT == "test":
        poolclass = NullPool
        pool_size = None
        max_overflow = None
    else:
        poolclass = AsyncAdaptedQueuePool
        pool_size = settings.DATABASE_POOL_SIZE
        max_overflow = settings.DATABASE_MAX_OVERFLOW

    return create_async_engine(
        settings.POSTGRES_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=pool_size,
        max_overflow=max_overflow,
        poolclass=poolclass,
        pool_pre_ping=True,  # Enable connection health checks
        pool_recycle=3600,  # Recycle connections after 1 hour
    )


# Lazy initialization to avoid settings loading at import time
class LazyEngine:
    """Lazy engine initialization wrapper."""

    _engine = None

    def __getattr__(self, name):
        if self._engine is None:
            self._engine = create_engine()
        return getattr(self._engine, name)

    async def begin(self):
        if self._engine is None:
            self._engine = create_engine()
        return self._engine.begin()

    async def dispose(self):
        if self._engine is not None:
            await self._engine.dispose()


# Create global engine instance
engine = LazyEngine()


# Create async session factory with lazy engine
def async_session():
    """Get async session factory."""
    return async_sessionmaker(
        engine._engine if engine._engine else create_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency function for FastAPI to get database sessions.

    Yields:
        AsyncSession: Database session with automatic cleanup
    """
    session_factory = async_session()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health() -> bool:
    """Check database connectivity and health.

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with engine.begin() as conn:
            # Execute simple query to verify connectivity
            result = await conn.execute(text("SELECT 1"))
            result.scalar()

            # Check pgvector extension
            result = await conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            if not result.scalar():
                logger.warning("pgvector extension not found in database")
                return False

        logger.info("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def dispose_engine():
    """Dispose of the engine and close all connections.

    Should be called during application shutdown.
    """
    await engine.dispose()
    logger.info("Database engine disposed")
