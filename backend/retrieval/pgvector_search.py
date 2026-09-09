"""
PostgreSQL pgvector Dense Semantic Vector Search Engine for SIH26108 (Phase 10B - Chunk 4).

Queries the standard_embeddings table using pgvector cosine distance operator (<->).
Reuses the existing SemanticEmbeddingEngine for query vector encoding.
Supports configurable vector backends, model/dimension filtering, top_k ordering,
and explicit error surfacing when PostgreSQL is unavailable.
"""

import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.connection import get_db_engine, get_session_factory, check_database_connection
from backend.database.models import StandardEmbeddingModel, StandardModel
from backend.retrieval.embeddings import SemanticEmbeddingEngine
from backend.config import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION, VECTOR_BACKEND
from backend.utils.logger import get_logger

logger = get_logger("PgVectorSearch")


class PgVectorSearchEngine:
    """
    SQLAlchemy / PostgreSQL pgvector Dense Semantic Vector Search Engine.

    Reuses existing `SemanticEmbeddingEngine` for query embedding encoding and queries
    `standard_embeddings` table using pgvector cosine distance (<->) operator.
    """
    def __init__(
        self,
        standards: List[Dict[str, Any]],
        model_name: Optional[str] = None,
        embedding_engine: Optional[SemanticEmbeddingEngine] = None,
        engine=None,
        session_factory=None
    ):
        self.standards = standards
        self.engine = engine
        self._session_factory = session_factory

        # Reuse existing SemanticEmbeddingEngine instance or instantiate one
        self.embedding_engine = embedding_engine or SemanticEmbeddingEngine(standards, model_name=model_name)
        self.active_model_name = self.embedding_engine.active_model_name
        self.vector_dimension = self.embedding_engine.vector_dimension

        # Build standard_id -> index map in self.standards
        self.std_id_to_idx: Dict[str, int] = {
            std["id"]: idx for idx, std in enumerate(standards) if isinstance(std, dict) and "id" in std
        }

    def _get_factory(self):
        if self._session_factory:
            return self._session_factory
        return get_session_factory(engine=self.engine)

    def _encode_query(self, query: str) -> List[float]:
        """Encodes query text into a normalized float vector array using the embedding engine."""
        if self.embedding_engine.model is not None:
            raw_emb = self.embedding_engine.model.encode([query], convert_to_numpy=True)
            norm = np.linalg.norm(raw_emb)
            if norm > 0:
                raw_emb = raw_emb / norm
            return [float(v) for v in raw_emb.flatten()]
        elif hasattr(self.embedding_engine, "vectorizer") and self.embedding_engine.vectorizer is not None:
            raw_emb = self.embedding_engine.vectorizer.transform([query]).toarray()
            norm = np.linalg.norm(raw_emb)
            if norm > 0:
                raw_emb = raw_emb / norm
            return [float(v) for v in raw_emb.flatten()]
        else:
            raise RuntimeError("PgVectorSearchEngine query encoding failed: embedding model is not initialized.")

    def search(self, query: str, top_k: Optional[int] = None) -> List[Tuple[int, float]]:
        """
        Executes vector cosine similarity search against standard_embeddings database table.

        Returns list of (doc_index, cosine_similarity) matching expected HybridRetriever contract.
        If query is empty or whitespace, returns 0.0 similarity for all documents.
        """
        num_docs = len(self.standards)
        if not query or not query.strip():
            return [(idx, 0.0) for idx in range(num_docs)]

        # 1. Encode query vector via underlying embedding engine
        query_vec = self._encode_query(query)

        # 2. Validate vector dimension matches model
        if len(query_vec) != self.vector_dimension:
            raise ValueError(
                f"Query vector dimension mismatch: expected {self.vector_dimension}, got {len(query_vec)}"
            )

        # 3. Query PostgreSQL via SQLAlchemy session
        factory = self._get_factory()
        scores_by_idx: Dict[int, float] = {idx: 0.0 for idx in range(num_docs)}

        try:
            with factory() as session:
                # Query StandardEmbeddingModel filtering strictly by matching embedding_model & embedding_dimension
                # Compute cosine distance using pgvector operator
                stmt = (
                    select(
                        StandardEmbeddingModel.standard_id,
                        StandardEmbeddingModel.embedding.cosine_distance(query_vec).label("distance")
                    )
                    .where(
                        StandardEmbeddingModel.embedding_model == self.active_model_name,
                        StandardEmbeddingModel.embedding_dimension == self.vector_dimension
                    )
                    .order_by(StandardEmbeddingModel.embedding.cosine_distance(query_vec).asc())
                )

                if top_k is not None and top_k > 0:
                    stmt = stmt.limit(top_k)

                results = session.execute(stmt).all()

                for std_id, dist_val in results:
                    if std_id in self.std_id_to_idx:
                        doc_idx = self.std_id_to_idx[std_id]
                        # Convert cosine distance to cosine similarity: sim = max(0, 1 - distance)
                        if dist_val is not None:
                            sim_score = max(0.0, min(1.0, 1.0 - float(dist_val)))
                            scores_by_idx[doc_idx] = max(scores_by_idx[doc_idx], sim_score)

        except Exception as e:
            logger.error(f"PgVectorSearchEngine.search query execution failed: {e}")
            raise RuntimeError(f"PostgreSQL pgvector search engine query failed: {e}") from e

        # Return list of (doc_index, similarity) ordered by doc_index
        return [(idx, scores_by_idx.get(idx, 0.0)) for idx in range(num_docs)]
