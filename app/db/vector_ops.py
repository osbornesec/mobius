"""Vector operations module for efficient vector database operations."""

import time
from typing import List, Dict, Any, Optional, Literal
from uuid import UUID

from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.models import Embedding, Document
from app.core.logging import get_logger

logger = get_logger(__name__)

# Type aliases
SimilarityMetric = Literal["cosine", "l2"]


async def insert_embeddings(
    session: AsyncSession, embeddings_data: List[Dict[str, Any]], batch_size: int = 100
) -> List[UUID]:
    """Batch insert embeddings with proper error handling.

    Args:
        session: Async database session
        embeddings_data: List of embedding data dictionaries containing:
            - document_id: UUID of the document
            - chunk_index: Index of the chunk
            - chunk_text: Text content of the chunk
            - embedding: Vector embedding (list of floats)
            - metadata: Optional metadata dictionary
        batch_size: Number of embeddings to insert per batch

    Returns:
        List of created embedding IDs

    Raises:
        IntegrityError: If constraints are violated
        ValueError: If vector dimensions don't match
    """
    start_time = time.time()
    created_ids = []

    try:
        # Process in batches for efficiency
        for i in range(0, len(embeddings_data), batch_size):
            batch = embeddings_data[i : i + batch_size]

            # Create embedding objects
            embeddings = []
            for data in batch:
                # Validate vector dimension
                if len(data["embedding"]) != 1536:
                    raise ValueError(
                        f"Invalid vector dimension: expected 1536, got {len(data['embedding'])}"
                    )

                embedding = Embedding(
                    document_id=data["document_id"],
                    chunk_index=data["chunk_index"],
                    chunk_text=data["chunk_text"],
                    embedding=data["embedding"],
                    embedding_metadata=data.get("metadata"),
                )
                embeddings.append(embedding)

            # Bulk insert
            session.add_all(embeddings)
            await session.flush()

            # Collect IDs
            created_ids.extend([e.id for e in embeddings])

        await session.commit()

        elapsed = time.time() - start_time
        logger.info(
            f"Inserted {len(embeddings_data)} embeddings in {elapsed:.2f}s "
            f"({len(embeddings_data)/elapsed:.0f} embeddings/s)"
        )

        return created_ids

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Integrity error during embedding insertion: {e}")
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error inserting embeddings: {e}")
        raise


async def similarity_search(
    session: AsyncSession,
    query_vector: List[float],
    limit: int = 10,
    metric: SimilarityMetric = "cosine",
    similarity_threshold: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Perform similarity search using pgvector operators.

    Args:
        session: Async database session
        query_vector: Query vector for similarity search
        limit: Maximum number of results to return
        metric: Similarity metric to use ("cosine" or "l2")
        similarity_threshold: Optional minimum similarity score

    Returns:
        List of search results with embedding data and similarity scores
    """
    start_time = time.time()

    # Validate vector dimension
    if len(query_vector) != 1536:
        raise ValueError(
            f"Invalid query vector dimension: expected 1536, got {len(query_vector)}"
        )

    # Choose operator based on metric
    if metric == "cosine":
        # <-> operator for cosine distance (1 - cosine similarity)
        distance_op = "<=>"
        order = "ASC"  # Lower distance = higher similarity
    else:  # l2
        # <#> operator for L2 distance
        distance_op = "<->"
        order = "ASC"  # Lower distance = higher similarity

    # Build query
    query = f"""
        SELECT 
            e.id,
            e.document_id,
            e.chunk_index,
            e.chunk_text,
            e.embedding_metadata,
            e.embedding {distance_op} :query_vector AS distance,
            d.file_path,
            d.project_id
        FROM embeddings e
        JOIN documents d ON e.document_id = d.id
        {"WHERE e.embedding " + distance_op + " :query_vector < :threshold" if similarity_threshold else ""}
        ORDER BY distance {order}
        LIMIT :limit
    """

    # Execute query
    params = {"query_vector": str(query_vector), "limit": limit}
    if similarity_threshold:
        params["threshold"] = similarity_threshold

    result = await session.execute(text(query), params)
    rows = result.fetchall()

    # Format results
    results = []
    for row in rows:
        # Convert distance to similarity score for cosine
        if metric == "cosine":
            similarity = 1 - row.distance
        else:
            similarity = 1 / (1 + row.distance)  # Convert L2 distance to similarity

        results.append(
            {
                "id": row.id,
                "document_id": row.document_id,
                "project_id": row.project_id,
                "file_path": row.file_path,
                "chunk_index": row.chunk_index,
                "chunk_text": row.chunk_text,
                "metadata": row.embedding_metadata,
                "similarity": similarity,
                "distance": row.distance,
            }
        )

    elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds
    logger.info(
        f"Similarity search completed in {elapsed:.1f}ms, "
        f"returned {len(results)} results"
    )

    # Ensure we meet performance requirements (<100ms for 10k vectors)
    if elapsed > 100:
        logger.warning(
            f"Similarity search took {elapsed:.1f}ms, "
            f"exceeding 100ms performance target"
        )

    return results


async def vector_search_with_filters(
    session: AsyncSession,
    query_vector: List[float],
    project_id: Optional[UUID] = None,
    file_types: Optional[List[str]] = None,
    metadata_filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    metric: SimilarityMetric = "cosine",
) -> List[Dict[str, Any]]:
    """Perform filtered similarity search with metadata constraints.

    Args:
        session: Async database session
        query_vector: Query vector for similarity search
        project_id: Optional project ID filter
        file_types: Optional list of file types to filter
        metadata_filters: Optional JSONB metadata filters
        limit: Maximum number of results
        metric: Similarity metric to use

    Returns:
        Filtered search results
    """
    start_time = time.time()

    # Build base query
    query = select(
        Embedding,
        Document,
        # Add similarity calculation
        text(f"embedding {'<=>' if metric == 'cosine' else '<->'} :query_vector").label(
            "distance"
        ),
    ).join(Document, Embedding.document_id == Document.id)

    # Apply filters
    filters = []
    if project_id:
        filters.append(Document.project_id == project_id)
    if file_types:
        filters.append(Document.file_type.in_(file_types))
    if metadata_filters:
        for key, value in metadata_filters.items():
            filters.append(Embedding.embedding_metadata[key].astext == str(value))

    if filters:
        query = query.filter(and_(*filters))

    # Order by similarity and limit
    query = query.order_by("distance").limit(limit)

    # Execute with query vector parameter
    result = await session.execute(query, {"query_vector": str(query_vector)})

    # Format results
    results = []
    for embedding, document, distance in result:
        if metric == "cosine":
            similarity = 1 - distance
        else:
            similarity = 1 / (1 + distance)

        results.append(
            {
                "id": embedding.id,
                "document_id": document.id,
                "project_id": document.project_id,
                "file_path": document.file_path,
                "file_type": document.file_type,
                "chunk_index": embedding.chunk_index,
                "chunk_text": embedding.chunk_text,
                "metadata": embedding.embedding_metadata,
                "similarity": similarity,
                "distance": distance,
            }
        )

    elapsed = (time.time() - start_time) * 1000
    logger.info(
        f"Filtered vector search completed in {elapsed:.1f}ms, "
        f"returned {len(results)} results"
    )

    return results
