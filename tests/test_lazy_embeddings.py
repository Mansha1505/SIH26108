"""
Unit and Integration Tests for Lazy Embedding Model Initialization & Multilingual Memory-Constrained Retrieval.

Verifies:
1. Constructing SemanticEmbeddingEngine does NOT eagerly load SentenceTransformer.
2. Constructing RecommendationService does NOT eagerly load the embedding model.
3. BM25 search functionality works independently without triggering embedding model load.
4. Lazy embedding initialization occurs when dense retrieval is actually requested.
5. Repeated calls reuse the initialized model without re-initialization.
6. Configured model selection (intfloat/multilingual-e5-small) and 384-dim validation.
7. Multilingual semantic retrieval (English, Hindi Devanagari, Hinglish) ranks IS 1180 Part 1 #1.
8. Environment-controlled reranker disabling (RERANK_ENABLED=False) executes cleanly.
"""

import pytest
import os
from backend.retrieval.loader import get_default_repository
from backend.retrieval.bm25 import BM25SearchEngine
from backend.retrieval.embeddings import SemanticEmbeddingEngine
from backend.retrieval.reranker import CrossEncoderReranker
from backend.services.recommendation_service import RecommendationService
from backend.models.schemas import RecommendationRequest


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


def test_configured_multilingual_e5_small_model_selection_and_dimension():
    """Verify that intfloat/multilingual-e5-small can be explicitly selected and maintains 384 dimensions."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards, model_name="intfloat/multilingual-e5-small")
    assert engine._is_initialized is False

    results = engine.search("distribution transformer 100 kVA")

    assert engine._is_initialized is True
    assert engine.active_model_name == "intfloat/multilingual-e5-small"
    assert engine.vector_dimension == 384
    assert engine.doc_embeddings.shape[1] == 384
    assert len(results) == len(standards)


def test_explicit_multilingual_e5_small_configuration():
    """Verify explicit intfloat/multilingual-e5-small Render production configuration, lazy init, and 384 dimensions."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards, model_name="intfloat/multilingual-e5-small")
    assert engine._is_initialized is False

    results = engine.search("distribution transformer 100 kVA")

    assert engine._is_initialized is True
    assert engine.active_model_name == "intfloat/multilingual-e5-small"
    assert engine.vector_dimension == 384
    assert engine.doc_embeddings.shape[1] == 384
    assert len(results) == len(standards)


@pytest.mark.parametrize("query_text, lang_label", [
    ("100 kVA 11 kV 433 V outdoor oil immersed distribution transformer", "English"),
    ("100 केवीए 11 केवी 433 वोल्ट तीन फेज आउटडोर ऑयल इमर्स्ड डिस्ट्रीब्यूशन ट्रांसफॉर्मर", "Hindi/Devanagari"),
    ("100 kVA 11 kV 433V three phase outdoor oil immersed transformer", "Hinglish")
])
def test_multilingual_recommendation_pipeline_constrained_config(query_text, lang_label, monkeypatch):
    """Verify that lightweight multilingual model intfloat/multilingual-e5-small ranks IS 1180 Part 1 #1 for English, Hindi, and Hinglish under RERANK_ENABLED=false."""
    monkeypatch.setattr("backend.retrieval.reranker.RERANK_ENABLED", False)

    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine_e5 = SemanticEmbeddingEngine(standards, model_name="intfloat/multilingual-e5-small")
    service = RecommendationService(repository=repo)
    service.initialize(embedding_engine=engine_e5)

    req = RecommendationRequest(query=query_text, top_k=5)
    rec_res = service.recommend(req)

    assert len(rec_res.recommendations) == 5
    top_rec = rec_res.recommendations[0]
    assert top_rec.is_number.startswith("IS 1180"), (
        f"[{lang_label}] Expected IS 1180 as top recommendation for '{query_text}', got {top_rec.is_number}"
    )
    assert top_rec.relevance_score > 0.2


def test_reranker_disabled_configuration(monkeypatch):
    """Verify that setting RERANK_ENABLED=false explicitly disables reranker without breaking retrieval."""
    monkeypatch.setattr("backend.retrieval.reranker.RERANK_ENABLED", False)

    reranker = CrossEncoderReranker()
    assert reranker.is_available is False

    mock_candidates = [
        {"doc_index": 0, "relevance_score": 0.85},
        {"doc_index": 1, "relevance_score": 0.65}
    ]
    res = reranker.rerank("transformer", mock_candidates, [])
    assert len(res) == 2
    assert res[0]["relevance_score"] == 0.85
    assert res[0]["reranked"] is False
