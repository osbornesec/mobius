"""Database package initialization.

This module exports the main database components for use throughout the application.
"""

from app.db.base import (
    Base,
    async_session,
    engine,
    get_db,
    check_database_health,
    dispose_engine,
)
from app.db.models import Project, Document, Embedding
from app.db.vector_ops import (
    insert_embeddings,
    similarity_search,
    vector_search_with_filters,
)

__all__ = [
    # Base components
    "Base",
    "engine",
    "async_session",
    "get_db",
    "check_database_health",
    "dispose_engine",
    # Models
    "Project",
    "Document",
    "Embedding",
    # Vector operations
    "insert_embeddings",
    "similarity_search",
    "vector_search_with_filters",
]
