"""Migration testing module following Task 003 specifications."""

import subprocess
import pytest
from sqlalchemy import text, inspect

from app.db.base import engine, async_session


class TestMigrations:
    """Test Alembic migration operations."""

    @pytest.fixture(autouse=True)
    async def setup_clean_db(self):
        """Ensure clean database state before each test."""
        # Drop all tables to start fresh
        async with engine.begin() as conn:
            # Get all table names
            result = await conn.execute(
                text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename NOT IN ('alembic_version')
                """)
            )
            tables = [row[0] for row in result]

            # Drop all tables except alembic_version
            for table in tables:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

        yield

        # Cleanup after test
        async with engine.begin() as conn:
            # Ensure we're at latest migration for other tests
            subprocess.run(
                ["alembic", "upgrade", "head"], check=False, capture_output=True
            )

    @pytest.mark.asyncio
    async def test_migration_up_down(self):
        """Test that migrations run successfully and are reversible."""
        # Start from clean state
        result = subprocess.run(
            ["alembic", "downgrade", "base"], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Downgrade failed: {result.stderr}"

        # Run migration up
        result = subprocess.run(
            ["alembic", "upgrade", "head"], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Upgrade failed: {result.stderr}"

        # Verify tables exist
        async with engine.begin() as conn:
            inspector = inspect(conn)
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

            expected_tables = {"projects", "documents", "embeddings", "alembic_version"}
            assert set(tables) >= expected_tables

        # Test migration down
        result = subprocess.run(
            ["alembic", "downgrade", "base"], capture_output=True, text=True
        )
        assert result.returncode == 0, f"Downgrade failed: {result.stderr}"

        # Verify tables are removed
        async with engine.begin() as conn:
            inspector = inspect(conn)
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

            # Only alembic_version should remain
            assert "projects" not in tables
            assert "documents" not in tables
            assert "embeddings" not in tables

    @pytest.mark.asyncio
    async def test_migration_history_tracking(self):
        """Test that migration history is properly tracked."""
        # Run migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)

        # Check alembic_version table
        session_factory = async_session()

        async with session_factory() as session:
            result = await session.execute(
                text("SELECT version_num FROM alembic_version")
            )
            version = result.scalar()
            assert version == "001"  # Our initial migration

    @pytest.mark.asyncio
    async def test_schema_after_migration(self):
        """Verify schema matches expected state after migrations."""
        # Run migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)

        async with engine.begin() as conn:
            # Check projects table structure
            result = await conn.execute(
                text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'projects'
                    ORDER BY ordinal_position
                """)
            )
            project_columns = {row[0]: (row[1], row[2]) for row in result}

            assert "id" in project_columns
            assert project_columns["id"][0] == "uuid"
            assert project_columns["name"][0] == "character varying"
            assert project_columns["description"][0] == "text"

            # Check documents table structure
            result = await conn.execute(
                text("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'documents'
                """)
            )
            document_columns = {row[0]: row[1] for row in result}

            assert "project_id" in document_columns
            assert "file_path" in document_columns
            assert document_columns["file_path"] == "character varying"

            # Check embeddings table structure
            result = await conn.execute(
                text("""
                    SELECT column_name, udt_name
                    FROM information_schema.columns
                    WHERE table_name = 'embeddings'
                """)
            )
            embedding_columns = {row[0]: row[1] for row in result}

            assert "embedding" in embedding_columns
            assert embedding_columns["embedding"] == "vector"

            # Check foreign key constraints
            result = await conn.execute(
                text("""
                    SELECT 
                        tc.table_name, 
                        kcu.column_name, 
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name 
                    FROM information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                """)
            )
            fk_constraints = list(result)

            # Verify foreign keys exist
            assert any(
                row[0] == "documents" and row[1] == "project_id"
                for row in fk_constraints
            )
            assert any(
                row[0] == "embeddings" and row[1] == "document_id"
                for row in fk_constraints
            )

    @pytest.mark.asyncio
    async def test_migration_idempotency(self):
        """Test running migrations multiple times is safe."""
        # Run upgrade multiple times
        for _ in range(3):
            result = subprocess.run(
                ["alembic", "upgrade", "head"], capture_output=True, text=True
            )
            assert result.returncode == 0

        # Verify only one version in alembic_version
        session_factory = async_session()

        async with session_factory() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM alembic_version"))
            count = result.scalar()
            assert count == 1

    @pytest.mark.asyncio
    async def test_vector_index_creation(self):
        """Verify vector indexes are created properly."""
        # Run migrations
        subprocess.run(["alembic", "upgrade", "head"], check=True)

        session_factory = async_session()

        async with session_factory() as session:
            # Check for ivfflat index
            result = await session.execute(
                text("""
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE tablename = 'embeddings'
                    AND indexname = 'idx_embedding_vector'
                """)
            )
            index = result.fetchone()

            assert index is not None
            assert "ivfflat" in index[1].lower()
            assert "lists = 100" in index[1]
