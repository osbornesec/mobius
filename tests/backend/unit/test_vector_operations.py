"""Vector operations testing module following Task 003 specifications."""

import time
import asyncio
from typing import List
import numpy as np
import pytest

from sqlalchemy import select, text
from app.db.base import async_session
from app.db.models import Project, Document, Embedding
from app.db.vector_ops import (
    insert_embeddings,
    similarity_search,
    vector_search_with_filters,
)


def generate_random_vector(dimension: int = 1536) -> List[float]:
    """Generate a random normalized vector."""
    vector = np.random.randn(dimension)
    # Normalize to unit length for consistent similarity scores
    vector = vector / np.linalg.norm(vector)
    return vector.tolist()


class TestVectorOperations:
    """Test vector insert and retrieve operations."""

    @pytest.fixture
    async def test_project_and_document(self):
        """Create test project and document."""
        session_factory = async_session()

        async with session_factory() as session:
            project = Project(
                name="Test Project", description="Test project for vector ops"
            )
            session.add(project)
            await session.flush()

            document = Document(
                project_id=project.id,
                file_path="/test/document.py",
                content="Test content",
                file_type="python",
                size_bytes=1024,
            )
            session.add(document)
            await session.commit()

            return project.id, document.id

    @pytest.mark.asyncio
    async def test_vector_insert_retrieve(self, test_project_and_document):
        """Test inserting and retrieving vectors."""
        _, document_id = test_project_and_document

        # Prepare test embeddings
        embeddings_data = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": f"Test chunk {i}",
                "embedding": generate_random_vector(),
                "metadata": {"test": True, "index": i},
            }
            for i in range(5)
        ]

        # Insert embeddings
        session_factory = async_session()

        async with session_factory() as session:
            created_ids = await insert_embeddings(session, embeddings_data)
            assert len(created_ids) == 5

            # Retrieve and verify
            for i, embedding_id in enumerate(created_ids):
                result = await session.execute(
                    select(Embedding).where(Embedding.id == embedding_id)
                )
                embedding = result.scalar_one()

                assert embedding.chunk_index == i
                assert embedding.chunk_text == f"Test chunk {i}"
                assert len(embedding.embedding) == 1536
                assert embedding.embedding_metadata["test"] is True

    @pytest.mark.asyncio
    async def test_batch_vector_operations(self, test_project_and_document):
        """Test batch insertion of vectors."""
        _, document_id = test_project_and_document

        # Create large batch
        batch_size = 500
        embeddings_data = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": f"Batch chunk {i}",
                "embedding": generate_random_vector(),
                "metadata": {"batch": True},
            }
            for i in range(batch_size)
        ]

        # Insert in batches
        start_time = time.time()
        session_factory = async_session()

        async with session_factory() as session:
            created_ids = await insert_embeddings(
                session, embeddings_data, batch_size=100
            )
            elapsed = time.time() - start_time

            assert len(created_ids) == batch_size
            assert elapsed < 5.0  # Should complete within 5 seconds

            # Verify count
            result = await session.execute(
                select(Embedding).where(Embedding.document_id == document_id)
            )
            embeddings = result.scalars().all()
            assert len(embeddings) == batch_size

    @pytest.mark.asyncio
    async def test_vector_dimension_validation(self, test_project_and_document):
        """Test vector dimension validation."""
        _, document_id = test_project_and_document

        # Try to insert wrong dimension
        wrong_dim_data = [
            {
                "document_id": document_id,
                "chunk_index": 0,
                "chunk_text": "Wrong dimension",
                "embedding": [0.1] * 100,  # Wrong dimension
                "metadata": {},
            }
        ]

        session_factory = async_session()

        async with session_factory() as session:
            with pytest.raises(ValueError) as exc_info:
                await insert_embeddings(session, wrong_dim_data)
            assert "Invalid vector dimension" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_vector_metadata_storage(self, test_project_and_document):
        """Test storing and retrieving vector metadata."""
        _, document_id = test_project_and_document

        # Complex metadata
        metadata = {
            "source": "test",
            "language": "python",
            "tokens": 150,
            "nested": {"key": "value", "array": [1, 2, 3]},
        }

        embeddings_data = [
            {
                "document_id": document_id,
                "chunk_index": 0,
                "chunk_text": "Metadata test",
                "embedding": generate_random_vector(),
                "metadata": metadata,
            }
        ]

        session_factory = async_session()

        async with session_factory() as session:
            created_ids = await insert_embeddings(session, embeddings_data)

            # Retrieve and verify metadata
            result = await session.execute(
                select(Embedding).where(Embedding.id == created_ids[0])
            )
            embedding = result.scalar_one()

            assert embedding.embedding_metadata["source"] == "test"
            assert embedding.embedding_metadata["nested"]["key"] == "value"
            assert embedding.embedding_metadata["nested"]["array"] == [1, 2, 3]


class TestVectorSimilaritySearch:
    """Test vector similarity search operations."""

    @pytest.fixture
    async def seeded_vectors(self, test_project_and_document):
        """Seed database with test vectors."""
        _, document_id = test_project_and_document

        # Create known vectors for testing
        base_vector = generate_random_vector()

        # Create similar and dissimilar vectors
        embeddings_data = []

        # Very similar vector (small perturbation)
        similar_vector = np.array(base_vector) + np.random.randn(1536) * 0.01
        similar_vector = (similar_vector / np.linalg.norm(similar_vector)).tolist()
        embeddings_data.append(
            {
                "document_id": document_id,
                "chunk_index": 0,
                "chunk_text": "Very similar",
                "embedding": similar_vector,
                "metadata": {"similarity": "high"},
            }
        )

        # Somewhat similar vector
        medium_vector = np.array(base_vector) + np.random.randn(1536) * 0.1
        medium_vector = (medium_vector / np.linalg.norm(medium_vector)).tolist()
        embeddings_data.append(
            {
                "document_id": document_id,
                "chunk_index": 1,
                "chunk_text": "Medium similar",
                "embedding": medium_vector,
                "metadata": {"similarity": "medium"},
            }
        )

        # Dissimilar vector (orthogonal)
        dissimilar_vector = generate_random_vector()
        embeddings_data.append(
            {
                "document_id": document_id,
                "chunk_index": 2,
                "chunk_text": "Not similar",
                "embedding": dissimilar_vector,
                "metadata": {"similarity": "low"},
            }
        )

        session_factory = async_session()

        async with session_factory() as session:
            await insert_embeddings(session, embeddings_data)

        return base_vector, document_id

    @pytest.mark.asyncio
    async def test_cosine_similarity_search(self, seeded_vectors):
        """Test cosine similarity search."""
        query_vector, _ = seeded_vectors

        session_factory = async_session()

        async with session_factory() as session:
            results = await similarity_search(
                session, query_vector, limit=3, metric="cosine"
            )

            assert len(results) == 3

            # Results should be ordered by similarity
            assert results[0]["chunk_text"] == "Very similar"
            assert results[1]["chunk_text"] == "Medium similar"
            assert results[2]["chunk_text"] == "Not similar"

            # Check similarity scores
            assert results[0]["similarity"] > 0.95  # Very high similarity
            assert results[1]["similarity"] > 0.8  # Good similarity
            assert results[2]["similarity"] < 0.5  # Low similarity

    @pytest.mark.asyncio
    async def test_l2_distance_search(self, seeded_vectors):
        """Test L2 distance search."""
        query_vector, _ = seeded_vectors

        session_factory = async_session()

        async with session_factory() as session:
            results = await similarity_search(
                session, query_vector, limit=3, metric="l2"
            )

            assert len(results) == 3

            # Results should be ordered by distance (ascending)
            assert results[0]["distance"] < results[1]["distance"]
            assert results[1]["distance"] < results[2]["distance"]

    @pytest.mark.asyncio
    async def test_search_with_filters(self, seeded_vectors):
        """Test similarity search with metadata filters."""
        query_vector, document_id = seeded_vectors

        # Add more vectors with different metadata
        embeddings_data = [
            {
                "document_id": document_id,
                "chunk_index": i + 10,
                "chunk_text": f"Python code {i}",
                "embedding": generate_random_vector(),
                "metadata": {"language": "python", "type": "code"},
            }
            for i in range(5)
        ]

        session_factory = async_session()

        async with session_factory() as session:
            await insert_embeddings(session, embeddings_data)

            # Search with filters
            results = await vector_search_with_filters(
                session, query_vector, metadata_filters={"language": "python"}, limit=10
            )

            # Should only return Python code chunks
            assert all(r["metadata"].get("language") == "python" for r in results)
            assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_performance_10k_vectors(self, test_project_and_document):
        """Test search performance with 10k vectors."""
        _, document_id = test_project_and_document

        # Insert 10k vectors in batches
        total_vectors = 10000
        batch_size = 1000

        print(f"\nInserting {total_vectors} vectors...")
        start_insert = time.time()

        for batch_start in range(0, total_vectors, batch_size):
            embeddings_data = [
                {
                    "document_id": document_id,
                    "chunk_index": batch_start + i,
                    "chunk_text": f"Performance test chunk {batch_start + i}",
                    "embedding": generate_random_vector(),
                    "metadata": {"batch": batch_start // batch_size},
                }
                for i in range(min(batch_size, total_vectors - batch_start))
            ]

            session_factory = async_session()

            async with session_factory() as session:
                await insert_embeddings(session, embeddings_data, batch_size=500)

        insert_time = time.time() - start_insert
        print(f"Inserted {total_vectors} vectors in {insert_time:.2f}s")

        # Test search performance
        query_vector = generate_random_vector()

        # Warm up the index
        session_factory = async_session()

        async with session_factory() as session:
            await similarity_search(session, query_vector, limit=1)

        # Measure search times
        search_times = []
        for _ in range(10):
            start_time = time.time()
            session_factory = async_session()

            async with session_factory() as session:
                results = await similarity_search(
                    session, query_vector, limit=10, metric="cosine"
                )
            elapsed_ms = (time.time() - start_time) * 1000
            search_times.append(elapsed_ms)

            assert len(results) == 10

        avg_search_time = np.mean(search_times)
        p95_search_time = np.percentile(search_times, 95)

        print(f"\nSearch performance with {total_vectors} vectors:")
        print(f"  Average: {avg_search_time:.1f}ms")
        print(f"  P95: {p95_search_time:.1f}ms")

        # Must meet <100ms requirement
        assert (
            avg_search_time < 100
        ), f"Average search time {avg_search_time:.1f}ms exceeds 100ms requirement"
        assert (
            p95_search_time < 150
        ), f"P95 search time {p95_search_time:.1f}ms is too high"


class TestVectorIndexing:
    """Test vector indexing functionality."""

    @pytest.mark.asyncio
    async def test_vector_indexing(self):
        """Test that vector indexes are properly used."""
        # This is tested implicitly by performance tests
        # The index creation is verified in test_migrations.py
        # Here we just verify we can query index information

        session_factory = async_session()

        async with session_factory() as session:
            result = await session.execute(
                text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'embeddings' 
                    AND indexname LIKE '%vector%'
                """)
            )
            indexes = [row[0] for row in result]
            assert "idx_embedding_vector" in indexes

    @pytest.mark.asyncio
    async def test_concurrent_index_usage(self, test_project_and_document):
        """Test concurrent queries using the vector index."""
        _, document_id = test_project_and_document

        # Insert test vectors
        embeddings_data = [
            {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": f"Concurrent test {i}",
                "embedding": generate_random_vector(),
                "metadata": {},
            }
            for i in range(100)
        ]

        session_factory = async_session()

        async with session_factory() as session:
            await insert_embeddings(session, embeddings_data)

        # Run concurrent searches
        async def search_task(index: int):
            query_vector = generate_random_vector()
            session_factory = async_session()

            async with session_factory() as session:
                return await similarity_search(session, query_vector, limit=5)

        # Execute 20 concurrent searches
        tasks = [search_task(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # All searches should succeed
        assert all(len(r) == 5 for r in results)
