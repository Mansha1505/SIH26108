import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.retrieval.loader import get_default_repository
from backend.retrieval.reranker import CrossEncoderReranker, sigmoid
from backend.services.recommendation_service import service_instance

client = TestClient(app)


def test_reranker_initialization_and_pair_construction():
    """Test A & B: Verify Reranker initialization and candidate text pair formatting."""
    repo = get_default_repository()
    standards = repo.get_all_standards()
    reranker = CrossEncoderReranker()
    reranker.initialize()

    assert reranker.is_available is True
    assert reranker.model is not None

    sample_text = reranker.build_candidate_text(standards[0])
    assert "Indian Standard:" in sample_text
    assert "Title:" in sample_text
    assert "Category:" in sample_text


def test_reranker_candidate_pool_bounding_and_scoring():
    """Test C, D & E: Verify top N candidate pool bounding, batch prediction, and score fusion."""
    repo = get_default_repository()
    standards = repo.get_all_standards()
    reranker = CrossEncoderReranker()
    reranker.initialize()

    # Mock candidate pool of 5 documents with mock hybrid scores
    mock_candidates = [
        {"doc_index": 0, "bm25_norm": 0.8, "semantic_raw": 0.8, "relevance_score": 0.8},
        {"doc_index": 1, "bm25_norm": 0.6, "semantic_raw": 0.6, "relevance_score": 0.6},
        {"doc_index": 2, "bm25_norm": 0.4, "semantic_raw": 0.4, "relevance_score": 0.4},
    ]

    reranked = reranker.rerank(
        query="distribution transformer 100 kVA",
        candidates=mock_candidates,
        standards=standards,
        candidate_pool_size=2,
        beta=0.5
    )

    assert len(reranked) == 3
    # Top 2 candidates should have reranked metadata
    top_items = [c for c in reranked if c.get("reranked") is True]
    assert len(top_items) == 2

    for item in top_items:
        assert "hybrid_score" in item
        assert "cross_encoder_raw" in item
        assert "cross_encoder_norm" in item
        assert 0.0 <= item["cross_encoder_norm"] <= 1.0
        # Final relevance score is weighted fusion (0.5 * cross_norm + 0.5 * hybrid_score)
        expected = round((0.5 * item["cross_encoder_norm"]) + (0.5 * item["hybrid_score"]), 4)
        assert item["relevance_score"] == expected


def test_reranker_graceful_fallback_on_invalid_model():
    """Test G: Verify system gracefully falls back to hybrid score when model fails to load."""
    fallback_reranker = CrossEncoderReranker(model_name="nonexistent_invalid_model_name_12345")
    fallback_reranker.initialize()

    assert fallback_reranker.is_available is False
    assert fallback_reranker.model is None

    mock_candidates = [
        {"doc_index": 0, "relevance_score": 0.85},
        {"doc_index": 1, "relevance_score": 0.65}
    ]

    res = fallback_reranker.rerank("transformer query", mock_candidates, [])
    assert len(res) == 2
    assert res[0]["relevance_score"] == 0.85
    assert res[0].get("reranked") is False


def test_api_recommend_reranking_integration():
    """Test H: Integration test for POST /api/recommend returning reranked scores and metadata."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    payload = {
        "query": "100 kVA three phase distribution transformer",
        "top_k": 5
    }

    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["reranking_enabled"] is True
    assert len(data["recommendations"]) == 5

    top_rec = data["recommendations"][0]
    assert "hybrid_score" in top_rec
    assert "cross_encoder_score" in top_rec
    assert top_rec["hybrid_score"] is not None
    assert top_rec["cross_encoder_score"] is not None
    assert any("Cross-encoder" in r for r in top_rec["reasons"])


def test_api_recommend_from_requirements_reranking():
    """Test I: Integration test for POST /api/recommend/from-requirements with reranker."""
    payload = {
        "requirements": {
            "product": {"name": "Distribution Transformer", "category": "Transformers"},
            "technical_requirements": [
                {"attribute": "capacity", "value": "100", "unit": "kVA", "source_text": "100 kVA"}
            ],
            "standards_mentions": ["IS 2026"],
            "safety_requirements": [],
            "installation_requirements": [],
            "keywords": ["transformer"],
            "raw_text": "100 kVA distribution transformer"
        },
        "top_k": 3
    }

    response = client.post("/api/recommend/from-requirements", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["reranking_enabled"] is True
    assert len(data["recommendations"]) <= 3
    assert data["recommendations"][0]["hybrid_score"] is not None


def test_health_check_reranker_metadata():
    """Test J: Verify GET /api/health includes reranker_model and reranker_enabled flags."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert "reranker_model" in data
    assert "reranker_enabled" in data
    assert data["reranker_enabled"] is True
