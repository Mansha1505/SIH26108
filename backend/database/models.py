"""
SQLAlchemy ORM Data Models for SIH26108 Standards Intelligence.

Maps Indian Standard persistence records to relational tables.
Supports PostgreSQL (with JSON/JSONB) and SQLite (for testing/development).
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import String, Integer, Text, JSON, ForeignKey, UniqueConstraint, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base
from backend.database.vector import Vector
from backend.models.schemas import IndianStandardRecord
from backend.config import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION


class StandardModel(Base):
    """
    SQLAlchemy ORM Model representing an Indian Standard record in PostgreSQL/SQLAlchemy.
    Mirrors the application domain schema `IndianStandardRecord`.
    """
    __tablename__ = "standards"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, index=True, comment="Unique identifier (e.g. 'IS-1180-P1')")
    is_number: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True, comment="Official IS designation code")
    title: Mapped[str] = mapped_column(String(500), nullable=False, comment="Official standard title")
    scope: Mapped[str] = mapped_column(Text, nullable=False, comment="Technical scope description")
    sector: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="Engineering sector")
    product_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="Product domain category")
    keywords: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list, comment="List of indexed keywords")
    revision_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Revision year")
    status: Mapped[str] = mapped_column(String(100), nullable=False, default="Active (DEMO / SAMPLE DATA)", comment="Corpus status flag")
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="Source URL if available")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Extended overview description")
    amendments: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list, comment="Structured amendment history records")
    related_standards: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list, comment="List of cross-referenced standard designations")

    # Relationship to associated vector embeddings (one-to-many, cascading deletion)
    embeddings: Mapped[List["StandardEmbeddingModel"]] = relationship(
        "StandardEmbeddingModel",
        back_populates="standard",
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Converts ORM model instance attributes into a dictionary matching domain requirements."""
        return {
            "id": self.id,
            "is_number": self.is_number,
            "title": self.title,
            "scope": self.scope,
            "sector": self.sector,
            "product_category": self.product_category,
            "keywords": self.keywords or [],
            "revision_year": self.revision_year,
            "status": self.status,
            "source_url": self.source_url,
            "description": self.description,
            "amendments": self.amendments or [],
            "related_standards": self.related_standards or []
        }

    def to_pydantic(self) -> IndianStandardRecord:
        """Converts ORM model instance directly into a validated IndianStandardRecord domain model."""
        return IndianStandardRecord(**self.to_dict())

    @classmethod
    def from_pydantic(cls, record: Any) -> "StandardModel":
        """Creates a new StandardModel ORM instance from an IndianStandardRecord domain model or dict."""
        if hasattr(record, "model_dump"):
            rec_dict = record.model_dump()
        elif isinstance(record, dict):
            rec_dict = record
        else:
            rec_dict = dict(record)

        return cls(
            id=rec_dict["id"],
            is_number=rec_dict["is_number"],
            title=rec_dict["title"],
            scope=rec_dict["scope"],
            sector=rec_dict["sector"],
            product_category=rec_dict["product_category"],
            keywords=rec_dict.get("keywords", []),
            revision_year=rec_dict.get("revision_year"),
            status=rec_dict.get("status", "Active (DEMO / SAMPLE DATA)"),
            source_url=rec_dict.get("source_url"),
            description=rec_dict.get("description"),
            amendments=rec_dict.get("amendments", []),
            related_standards=rec_dict.get("related_standards", [])
        )



class StandardEmbeddingModel(Base):
    """
    SQLAlchemy ORM Model representing semantic dense vector embeddings for standard text content.
    Supports pgvector storage (via `Vector`), metadata tracking, multi-model co-existence,
    and foreign-key cascade link to `StandardModel`.
    """
    __tablename__ = "standard_embeddings"
    __table_args__ = (
        UniqueConstraint("standard_id", "content", "embedding_model", name="uq_standard_content_model"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="Surrogate primary key")
    standard_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("standards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key referencing standards.id"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Text chunk/content encoded by this vector")
    embedding = mapped_column(Vector(DEFAULT_EMBEDDING_DIMENSION), nullable=True, comment="pgvector dense embedding vector")
    embedding_model: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default=DEFAULT_EMBEDDING_MODEL,
        index=True,
        comment="Embedding model identifier (e.g. 'paraphrase-multilingual-MiniLM-L12-v2')"
    )
    embedding_dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_EMBEDDING_DIMENSION,
        comment="Vector space dimensionality"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record update timestamp"
    )

    # Reverse relationship to associated Indian Standard ORM record
    standard: Mapped["StandardModel"] = relationship(
        "StandardModel",
        back_populates="embeddings"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Returns dictionary representation of the embedding metadata."""
        return {
            "id": self.id,
            "standard_id": self.standard_id,
            "content": self.content,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

