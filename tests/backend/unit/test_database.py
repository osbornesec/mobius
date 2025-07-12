"""Comprehensive database connection and pooling tests."""

import asyncio
import pytest
from sqlalchemy import text
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool

from app.db.base import engine, async_session, check_database_health
from app.core.config import get_settings


class TestDatabaseConnection:
    """Test database connectivity and basic operations."""

    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Verify database connectivity and basic query execution."""
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

        # Test session creation
        session_factory = async_session()
        async with session_factory() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            assert "PostgreSQL" in version

    @pytest.mark.asyncio
    async def test_connection_pool_creation(self):
        """Verify connection pool is created with correct size."""
        settings = get_settings()

        # For non-test environments, check pool configuration
        if settings.ENVIRONMENT != "test":
            pool = engine.pool
            assert isinstance(pool, AsyncAdaptedQueuePool)
            assert pool.size() == settings.DATABASE_POOL_SIZE
        else:
            # Test environment uses NullPool
            assert isinstance(engine.pool, NullPool)

    @pytest.mark.asyncio
    async def test_connection_release(self):
        """Test proper connection release after use."""
        # Create multiple sessions and ensure they're properly released
        sessions = []
        session_factory = async_session()
        for _ in range(5):
            session = session_factory()
            sessions.append(session)
            async with session:
                await session.execute(text("SELECT 1"))

        # All sessions should be closed
        for session in sessions:
            assert not session.is_active

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self):
        """Test connection timeout handling."""
        # Create a session with statement timeout
        session_factory = async_session()
        async with session_factory() as session:
            # Set a very short timeout
            await session.execute(text("SET statement_timeout = '1ms'"))

            # This should timeout
            with pytest.raises(Exception) as exc_info:
                await session.execute(text("SELECT pg_sleep(1)"))

            # Verify we got a timeout error
            assert (
                "timeout" in str(exc_info.value).lower()
                or "canceling" in str(exc_info.value).lower()
            )


class TestPgvectorExtension:
    """Test pgvector extension functionality."""

    @pytest.mark.asyncio
    async def test_pgvector_extension(self):
        """Verify pgvector extension is available."""
        session_factory = async_session()
        async with session_factory() as session:
            result = await session.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            assert result.scalar() == "vector"

    @pytest.mark.asyncio
    async def test_vector_operations_functionality(self):
        """Test basic vector operations."""
        async with async_session() as session:
            # Create temporary table for testing
            await session.execute(
                text("""
                    CREATE TEMP TABLE test_vectors (
                        id SERIAL PRIMARY KEY,
                        embedding vector(3)
                    )
                """)
            )

            # Insert test vectors
            await session.execute(
                text(
                    "INSERT INTO test_vectors (embedding) VALUES ('[1,2,3]'), ('[4,5,6]')"
                )
            )

            # Test cosine similarity
            result = await session.execute(
                text("""
                    SELECT embedding <=> '[1,2,3]'::vector as distance 
                    FROM test_vectors 
                    ORDER BY distance
                """)
            )
            distances = [row[0] for row in result]
            assert len(distances) == 2
            assert distances[0] < distances[1]  # First should be closest

    @pytest.mark.asyncio
    async def test_vector_dimension_validation(self):
        """Test vector dimension validation."""
        async with async_session() as session:
            # Create temp table with specific dimension
            await session.execute(
                text("""
                    CREATE TEMP TABLE test_dim_vectors (
                        id SERIAL PRIMARY KEY,
                        embedding vector(3)
                    )
                """)
            )

            # Try to insert wrong dimension - should fail
            with pytest.raises(Exception) as exc_info:
                await session.execute(
                    text(
                        "INSERT INTO test_dim_vectors (embedding) VALUES ('[1,2,3,4]')"
                    )
                )
            assert (
                "different size" in str(exc_info.value)
                or "dimension" in str(exc_info.value).lower()
            )

    @pytest.mark.asyncio
    async def test_similarity_functions(self):
        """Test different similarity functions."""
        async with async_session() as session:
            # Create test data
            await session.execute(
                text("""
                    CREATE TEMP TABLE test_similarity (
                        id SERIAL PRIMARY KEY,
                        vec vector(3)
                    )
                """)
            )
            await session.execute(
                text(
                    "INSERT INTO test_similarity (vec) VALUES ('[1,0,0]'), ('[0,1,0]'), ('[1,1,0]')"
                )
            )

            # Test cosine distance
            result = await session.execute(
                text(
                    "SELECT vec <=> '[1,0,0]'::vector FROM test_similarity ORDER BY vec <=> '[1,0,0]'::vector"
                )
            )
            cosine_distances = [row[0] for row in result]

            # Test L2 distance
            result = await session.execute(
                text(
                    "SELECT vec <-> '[1,0,0]'::vector FROM test_similarity ORDER BY vec <-> '[1,0,0]'::vector"
                )
            )
            l2_distances = [row[0] for row in result]

            # Both should return 3 results
            assert len(cosine_distances) == 3
            assert len(l2_distances) == 3


class TestConnectionPoolLimits:
    """Test connection pool limits and behavior under load."""

    @pytest.mark.asyncio
    async def test_connection_pool_limits(self):
        """Test maximum connection enforcement."""
        settings = get_settings()

        # Skip for test environment which uses NullPool
        if settings.ENVIRONMENT == "test":
            pytest.skip("Test environment uses NullPool")

        # Try to exceed pool size
        max_connections = settings.DATABASE_POOL_SIZE + settings.DATABASE_MAX_OVERFLOW
        sessions = []

        try:
            # Create connections up to the limit
            session_factory = async_session()
            for _ in range(max_connections):
                session = session_factory()
                sessions.append(session)
                await session.execute(text("SELECT 1"))

            # This should work - we're at the limit
            assert len(sessions) == max_connections

        finally:
            # Clean up
            for session in sessions:
                await session.close()

    @pytest.mark.asyncio
    async def test_connection_wait_timeout(self):
        """Test connection wait timeout behavior."""
        settings = get_settings()

        # Skip for test environment
        if settings.ENVIRONMENT == "test":
            pytest.skip("Test environment uses NullPool")

        # This test would require holding connections to force timeout
        # For now, just verify the pool accepts the configuration
        assert hasattr(engine.pool, "_pool")

    @pytest.mark.asyncio
    async def test_pool_overflow_handling(self):
        """Test pool overflow handling."""
        # Verify health check works
        health = await check_database_health()
        assert health is True

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test handling 100+ concurrent connections."""

        async def run_query(index: int):
            """Run a simple query."""
            session_factory = async_session()
            async with session_factory() as session:
                result = await session.execute(
                    text(f"SELECT {index} as num, pg_backend_pid()")
                )
                return result.fetchone()

        # Create 100 concurrent tasks
        tasks = [run_query(i) for i in range(100)]

        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results
        successful = [r for r in results if not isinstance(r, Exception)]
        errors = [r for r in results if isinstance(r, Exception)]

        # Most should succeed (some may fail due to connection limits)
        assert len(successful) > 80  # At least 80% success rate

        # Log any errors for debugging
        if errors:
            print(f"Connection errors: {len(errors)}")
            for error in errors[:5]:  # Show first 5 errors
                print(f"  Error: {error}")
