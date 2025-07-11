"""
Test suite for Pinecone vector operations.

This module contains comprehensive tests for Pinecone vector database operations
including index creation, vector upsert, query, update, and delete operations.
"""

import os
import time
import random
from typing import List, Tuple, Dict, Any
from unittest.mock import patch

import pytest
from pinecone import (
    Pinecone,
    ServerlessSpec,
    CloudProvider,
    AwsRegion,
    VectorType,
    Metric,
)


# Test configuration
TEST_INDEX_NAME = "mobius-test-index"
TEST_DIMENSION = 384  # Using a smaller dimension for testing
TEST_NAMESPACE = "test-namespace"
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")


def generate_random_vector(dimension: int) -> List[float]:
    """Generate a random vector of specified dimension."""
    return [random.random() for _ in range(dimension)]


def generate_test_vectors(
    count: int, dimension: int
) -> List[Tuple[str, List[float], Dict[str, Any]]]:
    """Generate test vectors with metadata."""
    vectors = []
    for i in range(count):
        vector_id = f"test-vec-{i}"
        values = generate_random_vector(dimension)
        metadata = {
            "test_id": i,
            "category": f"category-{i % 3}",
            "score": random.uniform(0, 100),
            "tags": [f"tag-{j}" for j in range(random.randint(1, 3))],
        }
        vectors.append((vector_id, values, metadata))
    return vectors


class TestPineconeOperations:
    """Test class for Pinecone vector operations."""

    @pytest.fixture(scope="class")
    def pinecone_client(self):
        """Initialize Pinecone client."""
        if not PINECONE_API_KEY:
            pytest.skip("PINECONE_API_KEY environment variable not set")

        return Pinecone(api_key=PINECONE_API_KEY)

    @pytest.fixture(scope="class")
    def test_index(self, pinecone_client):
        """Create a test index and clean up after tests."""
        pc = pinecone_client

        # Clean up any existing test index
        try:
            if TEST_INDEX_NAME in pc.list_indexes().names():
                pc.delete_index(TEST_INDEX_NAME)
                time.sleep(5)  # Wait for deletion to complete
        except Exception as e:
            print(f"Warning: Failed to delete existing test index: {e}")

        # Create new test index
        try:
            index_config = pc.create_index(
                name=TEST_INDEX_NAME,
                dimension=TEST_DIMENSION,
                metric=Metric.COSINE,
                spec=ServerlessSpec(
                    cloud=CloudProvider.AWS, region=AwsRegion.US_EAST_1
                ),
                vector_type=VectorType.DENSE,
            )

            # Wait for index to be ready
            time.sleep(10)

            # Get index instance
            index = pc.Index(host=index_config.host)

            yield index

        finally:
            # Cleanup: Delete test index
            try:
                pc.delete_index(TEST_INDEX_NAME)
            except Exception as e:
                print(f"Warning: Failed to delete test index during cleanup: {e}")

    def test_index_creation(self, pinecone_client):
        """Test index creation and description."""
        pc = pinecone_client

        # Verify index exists
        assert TEST_INDEX_NAME in pc.list_indexes().names()

        # Describe index
        index_desc = pc.describe_index(TEST_INDEX_NAME)
        assert index_desc.name == TEST_INDEX_NAME
        assert index_desc.dimension == TEST_DIMENSION
        assert index_desc.metric == "cosine"

    def test_upsert_operations(self, test_index):
        """Test vector upsert operations."""
        # Generate test vectors
        vectors = generate_test_vectors(10, TEST_DIMENSION)

        # Upsert vectors
        upsert_response = test_index.upsert(vectors=vectors, namespace=TEST_NAMESPACE)

        # Verify upsert response
        assert upsert_response is not None
        assert hasattr(upsert_response, "upserted_count")
        assert upsert_response.upserted_count == 10

        # Wait for vectors to be indexed
        time.sleep(2)

        # Verify vectors were upserted by checking stats
        stats = test_index.describe_index_stats()
        assert stats.total_vector_count >= 10

    def test_query_operations(self, test_index):
        """Test vector query operations."""
        # Generate and upsert test vectors if not already done
        vectors = generate_test_vectors(5, TEST_DIMENSION)
        test_index.upsert(vectors=vectors, namespace=TEST_NAMESPACE)
        time.sleep(2)

        # Query with a random vector
        query_vector = generate_random_vector(TEST_DIMENSION)

        # Basic query
        query_response = test_index.query(
            vector=query_vector, top_k=3, namespace=TEST_NAMESPACE
        )

        assert query_response is not None
        assert hasattr(query_response, "matches")
        assert len(query_response.matches) <= 3

        # Query with metadata filter
        filtered_response = test_index.query(
            vector=query_vector,
            top_k=5,
            namespace=TEST_NAMESPACE,
            include_metadata=True,
            filter={"category": {"$eq": "category-1"}},
        )

        assert filtered_response is not None
        assert all(
            match.metadata.get("category") == "category-1"
            for match in filtered_response.matches
            if match.metadata
        )

    def test_fetch_operations(self, test_index):
        """Test fetching vectors by ID."""
        # Ensure vectors exist
        vectors = generate_test_vectors(3, TEST_DIMENSION)
        test_index.upsert(vectors=vectors, namespace=TEST_NAMESPACE)
        time.sleep(2)

        # Fetch specific vectors
        ids_to_fetch = ["test-vec-0", "test-vec-1"]
        fetch_response = test_index.fetch(ids=ids_to_fetch, namespace=TEST_NAMESPACE)

        assert fetch_response is not None
        assert hasattr(fetch_response, "vectors")
        assert len(fetch_response.vectors) == 2
        assert all(id in fetch_response.vectors for id in ids_to_fetch)

    def test_update_operations(self, test_index):
        """Test vector update operations."""
        # Create a vector to update
        original_vector = (
            "update-test",
            generate_random_vector(TEST_DIMENSION),
            {"version": 1},
        )
        test_index.upsert(vectors=[original_vector], namespace=TEST_NAMESPACE)
        time.sleep(2)

        # Update the vector
        new_values = generate_random_vector(TEST_DIMENSION)
        update_response = test_index.update(
            id="update-test",
            values=new_values,
            set_metadata={"version": 2, "updated": True},
            namespace=TEST_NAMESPACE,
        )

        assert update_response is not None

        # Verify update by fetching
        time.sleep(2)
        fetch_response = test_index.fetch(ids=["update-test"], namespace=TEST_NAMESPACE)
        assert fetch_response.vectors["update-test"].metadata["version"] == 2
        assert fetch_response.vectors["update-test"].metadata["updated"] is True

    def test_delete_operations(self, test_index):
        """Test vector delete operations."""
        # Create vectors to delete
        vectors = generate_test_vectors(5, TEST_DIMENSION)
        test_index.upsert(vectors=vectors, namespace=TEST_NAMESPACE)
        time.sleep(2)

        # Delete specific vectors
        ids_to_delete = ["test-vec-0", "test-vec-1"]
        delete_response = test_index.delete(ids=ids_to_delete, namespace=TEST_NAMESPACE)

        assert delete_response is not None

        # Verify deletion
        time.sleep(2)
        fetch_response = test_index.fetch(ids=ids_to_delete, namespace=TEST_NAMESPACE)
        assert len(fetch_response.vectors) == 0

    def test_list_operations(self, test_index):
        """Test listing vector IDs."""
        # Ensure vectors exist with a specific prefix
        vectors = [
            (f"list-test-{i}", generate_random_vector(TEST_DIMENSION), {"index": i})
            for i in range(5)
        ]
        test_index.upsert(vectors=vectors, namespace=TEST_NAMESPACE)
        time.sleep(2)

        # List vectors with prefix
        vector_ids = []
        for ids in test_index.list(
            prefix="list-test", namespace=TEST_NAMESPACE, limit=3
        ):
            vector_ids.extend(ids)

        assert len(vector_ids) >= 5
        assert all(id.startswith("list-test") for id in vector_ids)

    def test_namespace_operations(self, test_index):
        """Test operations across different namespaces."""
        namespace1 = "namespace-1"
        namespace2 = "namespace-2"

        # Upsert to different namespaces
        vectors1 = generate_test_vectors(3, TEST_DIMENSION)
        vectors2 = generate_test_vectors(3, TEST_DIMENSION)

        test_index.upsert(vectors=vectors1, namespace=namespace1)
        test_index.upsert(vectors=vectors2, namespace=namespace2)
        time.sleep(2)

        # Query each namespace
        query_vector = generate_random_vector(TEST_DIMENSION)

        response1 = test_index.query(vector=query_vector, top_k=5, namespace=namespace1)
        response2 = test_index.query(vector=query_vector, top_k=5, namespace=namespace2)

        # Vectors should be isolated by namespace
        assert len(response1.matches) <= 3
        assert len(response2.matches) <= 3

    def test_batch_operations(self, test_index):
        """Test batch upsert operations."""
        # Generate large batch of vectors
        large_batch = generate_test_vectors(100, TEST_DIMENSION)

        # Upsert in batches (Pinecone handles batching internally)
        upsert_response = test_index.upsert(
            vectors=large_batch, namespace=TEST_NAMESPACE
        )

        assert upsert_response.upserted_count == 100

        # Verify with stats
        time.sleep(5)
        stats = test_index.describe_index_stats()
        assert stats.total_vector_count >= 100

    def test_error_handling(self, test_index):
        """Test error handling for invalid operations."""
        # Test with invalid vector dimension
        with pytest.raises(Exception):
            invalid_vector = ("invalid", [0.1, 0.2], {})  # Wrong dimension
            test_index.upsert(vectors=[invalid_vector], namespace=TEST_NAMESPACE)

        # Test with invalid query parameters
        with pytest.raises(Exception):
            test_index.query(
                vector=generate_random_vector(TEST_DIMENSION),
                top_k=0,  # Invalid top_k
                namespace=TEST_NAMESPACE,
            )


class TestPineconeWithoutAPIKey:
    """Test Pinecone operations when API key is not set."""

    def test_missing_api_key(self):
        """Test behavior when PINECONE_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove PINECONE_API_KEY from environment
            if "PINECONE_API_KEY" in os.environ:
                del os.environ["PINECONE_API_KEY"]

            # Should raise exception when initializing without API key
            with pytest.raises(Exception):
                Pinecone()

    def test_invalid_api_key(self):
        """Test behavior with invalid API key."""
        # Initialize with invalid key
        pc = Pinecone(api_key="invalid-key-12345")

        # Should fail when trying to list indexes
        with pytest.raises(Exception):
            pc.list_indexes()


@pytest.mark.asyncio
class TestPineconeAsyncOperations:
    """Test async operations with Pinecone (if using asyncio support)."""

    async def test_async_index_operations(self):
        """Test async index operations."""
        if not PINECONE_API_KEY:
            pytest.skip("PINECONE_API_KEY environment variable not set")

        try:
            from pinecone import PineconeAsyncio

            async with PineconeAsyncio(api_key=PINECONE_API_KEY) as pc:
                # List indexes asynchronously
                indexes = await pc.list_indexes()
                assert indexes is not None

        except ImportError:
            pytest.skip(
                "Async support not installed (install with pip install pinecone[asyncio])"
            )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
