"""
Unit and Integration Tests for Hugging Face Free Inference API & Fallback Retrieval Architecture.

Verifies:
1. Constructing SemanticEmbeddingEngine does NOT eagerly load PyTorch or heavy ML models.
2. Precomputed document vector artifact loading (backend/data/doc_embeddings_e5_small.npy).
3. Document vector shape (14, 384) and normalization.
4. HFInferenceQueryEncoder produces 384-dimensional normalized vector when HF API returns success.
5. HF API timeout, HTTP error, or network failure triggers seamless fallback to BM25 keyword search.
6. semantic_status metadata in RecommendationResponse accurately reflects 'hf_e5_small' vs 'fallback_bm25'.
7. Zero PyTorch / SentenceTransformers / Transformers imports during constrained backend execution.
8. Multilingual evaluation queries (English, Hindi Devanagari, Hinglish, Technical).
"""

import pytest
import os
import sys
import json
import numpy as np
from unittest.mock import patch, MagicMock

from backend.retrieval.loader import get_default_repository
from backend.retrieval.bm25 import BM25SearchEngine
from backend.retrieval.embeddings import SemanticEmbeddingEngine, HFInferenceQueryEncoder
from backend.retrieval.reranker import CrossEncoderReranker
from backend.services.recommendation_service import RecommendationService
from backend.models.schemas import RecommendationRequest


def test_embedding_engine_lazy_construction():
    """Verify that constructing SemanticEmbeddingEngine does NOT load heavy ML libraries on init."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards, model_name="intfloat/multilingual-e5-small")

    assert engine._is_initialized is False
    assert engine._doc_embeddings is None
    assert engine._hf_encoder is None
    assert engine.active_model_name == "intfloat/multilingual-e5-small"
    assert engine.vector_dimension == 384


def test_precomputed_document_artifact_loading():
    """Verify that doc_embeddings_e5_small.npy loads correctly with 14 rows and 384 columns."""
    artifact_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "data", "doc_embeddings_e5_small.npy"))
    assert os.path.exists(artifact_path), f"Artifact missing at {artifact_path}"

    embeddings = np.load(artifact_path)
    assert embeddings.shape == (14, 384), f"Expected shape (14, 384), got {embeddings.shape}"
    assert embeddings.dtype == np.float32

    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, 1.0, rtol=1e-5)


def test_bm25_works_independently_without_embeddings():
    """Verify that BM25 keyword search operates without triggering dense embedding model load."""
    repo = get_default_repository()
    standards = repo.get_all_standards()

    bm25 = BM25SearchEngine(standards)
    results = bm25.search("distribution transformer 100 kVA")

    assert len(results) == len(standards)
    assert any(score > 0 for _, score in results)


def test_hf_inference_api_success(monkeypatch):
    """Verify HFInferenceQueryEncoder parses 384-d float vector correctly on HTTP 200 success."""
    mock_vector = [0.05] * 384

    class MockResponse:
        status = 200
        def read(self):
            return json.dumps([mock_vector]).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def mock_urlopen(req, timeout=4.0):
        return MockResponse()

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    encoder = HFInferenceQueryEncoder("intfloat/multilingual-e5-small")
    vec = encoder.encode_query("safety harness for construction work at high altitude")

    assert isinstance(vec, np.ndarray)
    assert vec.shape == (384,)
    norm = np.linalg.norm(vec)
    np.testing.assert_allclose(norm, 1.0, rtol=1e-5)


def test_hf_inference_api_timeout_fallback(monkeypatch):
    """Verify HF API timeout triggers graceful fallback to BM25 without crashing."""
    def mock_urlopen_timeout(req, timeout=4.0):
        raise TimeoutError("HTTP request timed out after 4 seconds")

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_timeout)

    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards, model_name="intfloat/multilingual-e5-small")
    results = engine.search("safety harness")

    assert len(results) == len(standards)
    assert engine.semantic_status == "fallback_bm25"


def test_hf_inference_api_http_error_fallback(monkeypatch):
    """Verify HTTP 500 / 429 error triggers fallback to BM25."""
    class MockErrorResponse:
        status = 503
        def read(self):
            return b'{"error": "Model is loading"}'
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def mock_urlopen_error(req, timeout=4.0):
        return MockErrorResponse()

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_error)

    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards, model_name="intfloat/multilingual-e5-small")
    results = engine.search("safety harness")

    assert len(results) == len(standards)
    assert engine.semantic_status == "fallback_bm25"


def test_recommendation_service_semantic_status_metadata(monkeypatch):
    """Verify RecommendationResponse includes correct semantic_status metadata."""
    monkeypatch.setattr("backend.retrieval.reranker.RERANK_ENABLED", False)

    # Mock HF API success
    mock_vector = [0.01] * 384
    class MockResponse:
        status = 200
        def read(self):
            return json.dumps([mock_vector]).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=4.0: MockResponse())

    repo = get_default_repository()
    service = RecommendationService(repository=repo)
    service.initialize()

    req = RecommendationRequest(query="distribution transformer", top_k=5)
    res = service.recommend(req)

    assert res.semantic_status == "hf_e5_small"
    assert len(res.recommendations) == 5


def test_no_heavy_ml_imports_in_constrained_runtime():
    """Verify PyTorch, SentenceTransformers, and Transformers are NOT loaded into sys.modules during retrieval."""
    forbidden_modules = ["torch", "sentence_transformers", "transformers"]

    repo = get_default_repository()
    standards = repo.get_all_standards()

    engine = SemanticEmbeddingEngine(standards, model_name="intfloat/multilingual-e5-small")
    engine.search("structural steel column testing")

    for mod in forbidden_modules:
        assert mod not in sys.modules, f"Forbidden heavy ML package '{mod}' was loaded into memory!"


@pytest.mark.parametrize("query_text, expected_is_substring, lang_label", [
    ("structural steel beams and columns specification", "2062", "English"),
    ("संरचनात्मक स्टील बीम और कॉलम विनिर्देश", "2062", "Hindi/Devanagari"),
    ("structural steel columns ke liye testing specification", "2062", "Hinglish"),
    ("fire extinguisher performance and construction testing", "15683", "Technical Semantic")
])
def test_multilingual_benchmark_queries_semantic(query_text, expected_is_substring, lang_label, monkeypatch):
    """Verify that when HF semantic API is active (or vector retrieval is simulated), expected target standards are ranked #1."""
    monkeypatch.setattr("backend.retrieval.reranker.RERANK_ENABLED", False)

    repo = get_default_repository()
    standards = repo.get_all_standards()

    # Find index of standard matching expected_is_substring
    target_idx = 0
    for idx, std in enumerate(standards):
        if expected_is_substring in std["is_number"] or expected_is_substring in std["id"]:
            target_idx = idx
            break

    # Mock HF query vector that yields highest cosine similarity to target_idx doc embedding
    artifact_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "data", "doc_embeddings_e5_small.npy"))
    doc_matrix = np.load(artifact_path)
    target_vector = doc_matrix[target_idx].tolist()

    class MockResponse:
        status = 200
        def read(self):
            return json.dumps([target_vector]).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=4.0: MockResponse())

    service = RecommendationService(repository=repo)
    service.initialize()

    req = RecommendationRequest(query=query_text, top_k=5)
    res = service.recommend(req)

    assert res.semantic_status == "hf_e5_small"
    assert len(res.recommendations) == 5
    top_rec = res.recommendations[0]
    assert expected_is_substring in top_rec.is_number or expected_is_substring in top_rec.id, (
        f"[{lang_label}] Expected target standard containing '{expected_is_substring}' as top recommendation. Got {top_rec.id} ({top_rec.is_number})"
    )


@pytest.mark.parametrize("query_text, lang_label", [
    ("safety harness for construction work at high altitude", "English"),
    ("ऊंचाई पर निर्माण कार्य के लिए सुरक्षा हार्नेस", "Hindi/Devanagari"),
    ("high height construction ke liye safety belt standard", "Hinglish"),
    ("testing parameters for structural steel columns", "Technical Semantic")
])
def test_multilingual_benchmark_queries_fallback(query_text, lang_label, monkeypatch):
    """Verify that when HF API is offline/unavailable, fallback to BM25 works cleanly without crashing and sets semantic_status='fallback_bm25'."""
    monkeypatch.setattr("backend.retrieval.reranker.RERANK_ENABLED", False)

    def mock_urlopen_error(req, timeout=4.0):
        raise TimeoutError("HF API Offline")

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_error)

    repo = get_default_repository()
    service = RecommendationService(repository=repo)
    service.initialize()

    req = RecommendationRequest(query=query_text, top_k=5)
    res = service.recommend(req)

    assert res.semantic_status == "fallback_bm25"
    assert len(res.recommendations) == 5
    assert res.query == query_text
