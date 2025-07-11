"""
Shared fixtures for backend tests.

This module provides common fixtures that can be used across all backend tests,
following pytest best practices for fixture organization and reusability.
"""

from pathlib import Path
from typing import AsyncGenerator, List
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from app.db.base import engine, async_session, Base
from app.db.models import Project, Document


@pytest.fixture(scope="session")
def project_root() -> Path:
    """
    Get the project root directory.

    This fixture is session-scoped to avoid repeated path calculations
    and provides a consistent base path for all tests.

    Returns:
        Path: The absolute path to the project root directory
    """
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def app_directory(project_root: Path) -> Path:
    """
    Get the app directory path.

    Args:
        project_root: The project root directory fixture

    Returns:
        Path: The absolute path to the app directory
    """
    return project_root / "app"


@pytest.fixture(scope="session")
def frontend_directory(project_root: Path) -> Path:
    """
    Get the frontend directory path.

    Args:
        project_root: The project root directory fixture

    Returns:
        Path: The absolute path to the frontend directory
    """
    return project_root / "frontend"


@pytest.fixture(scope="session")
def tests_directory(project_root: Path) -> Path:
    """
    Get the tests directory path.

    Args:
        project_root: The project root directory fixture

    Returns:
        Path: The absolute path to the tests directory
    """
    return project_root / "tests"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a transactional database session for tests.

    This fixture creates a new database session with a transaction
    that is rolled back after the test completes, ensuring test isolation.

    Yields:
        AsyncSession: Database session for testing
    """
    async with engine.begin() as conn:
        # Create all tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_session()

    async with session_factory() as session:
        async with session.begin():
            yield session
            # Transaction will be rolled back automatically


@pytest_asyncio.fixture
async def db_cleanup():
    """
    Clean up database between tests.

    This fixture truncates all tables to ensure a clean state
    for each test. It preserves the schema but removes all data.
    """
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

        # Truncate all tables
        for table in tables:
            await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))

    yield

    # Cleanup after test
    async with engine.begin() as conn:
        for table in tables:
            await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))


def generate_test_embedding(dimension: int = 1536) -> List[float]:
    """
    Generate a test embedding vector.

    Args:
        dimension: Vector dimension (default: 1536 for OpenAI ada-002)

    Returns:
        List[float]: Normalized random vector
    """
    vector = np.random.randn(dimension)
    # Normalize to unit length
    vector = vector / np.linalg.norm(vector)
    return vector.tolist()


@pytest.fixture
def sample_embeddings() -> List[List[float]]:
    """
    Provide sample embedding vectors for testing.

    Returns:
        List of test embeddings with different characteristics
    """
    # Base vector
    base = generate_test_embedding()

    # Similar vector (small perturbation)
    similar = np.array(base) + np.random.randn(1536) * 0.01
    similar = (similar / np.linalg.norm(similar)).tolist()

    # Orthogonal vector (dissimilar)
    orthogonal = generate_test_embedding()

    return [base, similar, orthogonal]


@pytest_asyncio.fixture
async def test_project(db_session: AsyncSession) -> Project:
    """
    Create a test project.

    Args:
        db_session: Database session fixture

    Returns:
        Project: Created test project
    """
    project = Project(name="Test Project", description="Project for testing")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest_asyncio.fixture
async def test_document(db_session: AsyncSession, test_project: Project) -> Document:
    """
    Create a test document.

    Args:
        db_session: Database session fixture
        test_project: Test project fixture

    Returns:
        Document: Created test document
    """
    document = Document(
        project_id=test_project.id,
        file_path="/test/example.py",
        content="# Test file content",
        file_type="python",
        size_bytes=1024,
        hash="abcdef123456",
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    return document


@pytest_asyncio.fixture
async def async_engine_fixture():
    """
    Provide the async engine for database tests.

    This fixture ensures the engine is properly disposed after tests.
    """
    yield engine
    # Engine disposal is handled by the application lifespan
