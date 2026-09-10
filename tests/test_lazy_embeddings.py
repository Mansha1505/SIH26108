"""
Unit and Integration Tests for Lazy Embedding Model Initialization.

Verifies:
1. Constructing SemanticEmbeddingEngine does NOT eagerly load SentenceTransformer.
2. Constructing RecommendationService does NOT eagerly load the embedding model.
3. BM25 search functionality works independently without triggering embedding model load.
4. Lazy embedding initialization occurs when dense retrieval is actually requested.
5. Repeated calls reuse the initialized model without re-initialization.
"""

import pytest
from backend.retrieval.loader import get_default_repository
from backend.retrieval.bm25 import BM25SearchEngine
from backend.retrieval.embeddings import SemanticEmbeddingEngine
from backend.services.recommendation_service import RecommendationService


def test_embedding_engine_lazy_construction():
    """Verify that constructing SemanticEmbeddingEngine does NOT load SentenceTransformer immediately."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards)

    # Core assertion: model must NOT be loaded on __init__
    assert engine._is_initialized is False
    assert engine._model is None
    assert engine._doc_embeddings is None
    assert engine.active_model_name is not None
    assert engine.vector_dimension > 0


def test_recommendation_service_lazy_construction():
    """Verify that constructing RecommendationService does NOT load SentenceTransformer immediately."""
    repo = get_default_repository()
    service = RecommendationService(repository=repo)
    service.initialize()

    # Core assertion: RecommendationService is ready, but embedding model is not yet loaded
    assert service._is_initialized is True
    assert service.embedding_engine is not None
    assert service.embedding_engine._is_initialized is False
    assert service.embedding_engine._model is None


def test_bm25_works_independently_without_embeddings():
    """Verify that BM25 keyword search operates without triggering dense embedding model load."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    bm25 = BM25SearchEngine(standards)
    results = bm25.search("distribution transformer 100 kVA")

    assert len(results) == len(standards)
    assert any(score > 0 for _, score in results)


def test_lazy_embedding_initialization_on_dense_search():
    """Verify that dense retrieval search() lazily triggers embedding model loading."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards)
    assert engine._is_initialized is False

    # Perform dense vector search
    results = engine.search("LED street light luminaire")

    # Core assertion: model should now be initialized
    assert engine._is_initialized is True
    assert engine._model is not None
    assert engine._doc_embeddings is not None
    assert len(results) == len(standards)


def test_repeated_search_calls_reuse_initialized_model():
    """Verify that repeated search calls reuse the initialized model without re-initializing."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards)
    engine.search("first query")
    assert engine._is_initialized is True

    model_ref = engine._model
    doc_emb_ref = engine._doc_embeddings

    # Second search query
    results2 = engine.search("second query")

    # Core assertion: exact same model and embeddings references are reused
    assert engine._model is model_ref
    assert engine._doc_embeddings is doc_emb_ref
    assert len(results2) == len(standards)
