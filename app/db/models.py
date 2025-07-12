"""SQLAlchemy models for the Mobius database."""

from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    BigInteger,
    ForeignKey,
    UniqueConstraint,
    Index,
    DateTime,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class TimestampMixin:
    """Mixin for automatic timestamp handling."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.utcnow,
    )


class Project(Base, TimestampMixin):
    """Project model for organizing documents and embeddings."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}')>"


class Document(Base, TimestampMixin):
    """Document model for storing files and their metadata."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="documents")
    embeddings: Mapped[List["Embedding"]] = relationship(
        "Embedding", back_populates="document", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("project_id", "file_path", name="uq_project_file_path"),
        Index("idx_document_project_id", "project_id"),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, file_path='{self.file_path}')>"


class Embedding(Base, TimestampMixin):
    """Embedding model for storing vector representations of document chunks."""

    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # OpenAI ada-002 dimension
    embedding_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="embeddings")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk"),
        Index("idx_embedding_document_id", "document_id"),
        # IVFFlat index for vector similarity search
        # Note: This will be created in the migration with proper SQL
        # Index("idx_embedding_vector", "embedding", postgresql_using="ivfflat", postgresql_ops={"embedding": "vector_l2_ops"})
    )

    def __repr__(self) -> str:
        return f"<Embedding(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
