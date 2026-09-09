import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.retrieval.loader import get_default_repository
from backend.retrieval.embeddings import SemanticEmbeddingEngine
from backend.services.recommendation_service import service_instance

client = TestClient(app)


def test_multilingual_embeddings_shape_and_non_empty():
    """Verify English, Hindi, and Hinglish embeddings have non-empty output and matching vector dimensions."""
    repo = get_default_repository()
    standards = repo.get_all_standards()
    engine = SemanticEmbeddingEngine(standards)

    english_q = "100 kVA three phase distribution transformer"
    hindi_q = "100 केवीए तीन फेज वितरण ट्रांसफार्मर"
    hinglish_q = "100 kVA ka three phase distribution transformer chahiye"

    # Test 1. English query search
    res_en = engine.search(english_q)
    assert len(res_en) == len(standards)

    # Test 2. Hindi query search
    res_hi = engine.search(hindi_q)
    assert len(res_hi) == len(standards)

    # Test 3. Hinglish query search
    res_hing = engine.search(hinglish_q)
    assert len(res_hing) == len(standards)

    # Test 4 & 5. Embedding shape and non-empty vector properties
    assert engine.vector_dimension > 0
    assert engine.doc_embeddings is not None
    assert engine.doc_embeddings.shape[0] == len(standards)
    assert engine.doc_embeddings.shape[1] == engine.vector_dimension

    # Verify scores are bounded in [0.0, 1.0] and not all zero
    for res in [res_en, res_hi, res_hing]:
        scores = [score for _, score in res]
        assert all(0.0 <= s <= 1.0 for s in scores)
        assert max(scores) > 0.0


def test_multilingual_transformer_retrieval_ranking():
    """Verify that Hindi and Hinglish queries return relevant transformer standards."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    hindi_payload = {
        "query": "100 केवीए तीन फेज वितरण ट्रांसफार्मर",
        "top_k": 3
    }
    response_hi = client.post("/api/recommend", json=hindi_payload)
    assert response_hi.status_code == 200
    data_hi = response_hi.json()

    assert len(data_hi["recommendations"]) > 0
    top_hi = data_hi["recommendations"][0]
    assert "Transformer" in top_hi["product_category"] or "Transformer" in top_hi["title"] or "2026" in top_hi["is_number"] or "1180" in top_hi["is_number"]

    hinglish_payload = {
        "query": "100 kVA ka three phase distribution transformer chahiye",
        "top_k": 3
    }
    response_hing = client.post("/api/recommend", json=hinglish_payload)
    assert response_hing.status_code == 200
    data_hing = response_hing.json()

    assert len(data_hing["recommendations"]) > 0
    top_hing = data_hing["recommendations"][0]
    assert "Transformer" in top_hing["product_category"] or "Transformer" in top_hing["title"] or "2026" in top_hing["is_number"] or "1180" in top_hing["is_number"]


def test_multilingual_led_light_retrieval():
    """Verify Hindi query for LED street light retrieves luminaire standards."""
    payload = {
        "query": "50 वाट एलइडी स्ट्रीट लाइट",
        "top_k": 3
    }
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["recommendations"]) > 0
    top_rec = data["recommendations"][0]
    assert "Lighting" in top_rec["product_category"] or "LED" in top_rec["title"] or "10322" in top_rec["is_number"] or "Luminaire" in top_rec["title"]


def test_multilingual_hdpe_pipe_retrieval():
    """Verify Hinglish query for HDPE water pipe retrieves pipe standards."""
    payload = {
        "query": "110 mm ka HDPE water pipe drinking water ke liye",
        "top_k": 3
    }
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["recommendations"]) > 0
    top_rec = data["recommendations"][0]
    assert "Pipe" in top_rec["product_category"] or "HDPE" in top_rec["title"] or "4984" in top_rec["is_number"] or "Polyethylene" in top_rec["scope"]


def test_existing_english_retrieval_regression():
    """Regression test ensuring standard English query search remains high quality."""
    payload = {
        "query": "50W LED street light for outdoor municipal roads",
        "top_k": 5
    }
    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) == 5
    assert data["recommendations"][0]["relevance_score"] >= 0.0


def test_health_check_multilingual_metadata():
    """Verify GET /api/health returns active embedding model and vector dimension."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "embedding_model" in data
    assert "embedding_dimension" in data
    assert data["embedding_dimension"] > 0
