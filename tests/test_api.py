from fastapi.testclient import TestClient
from backend.main import app

def test_health_check_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["total_standards_indexed"] > 0
        assert "DEMO" in data["data_source"]

def test_recommend_endpoint_valid_query():
    with TestClient(app) as client:
        payload = {
            "query": "50W LED street light for outdoor municipal roads",
            "top_k": 3
        }
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == payload["query"]
        assert len(data["recommendations"]) > 0
        assert len(data["recommendations"]) <= 3
        
        top_rec = data["recommendations"][0]
        assert "is_number" in top_rec
        assert "title" in top_rec
        assert "relevance_score" in top_rec
        assert "reasons" in top_rec
        assert 0.0 <= top_rec["relevance_score"] <= 1.0

def test_recommend_endpoint_invalid_empty_query():
    with TestClient(app) as client:
        payload = {
            "query": "  ",
            "top_k": 5
        }
        response = client.post("/api/recommend", json=payload)
        # Pydantic / FastAPI validation error for min_length or empty string
        assert response.status_code in [400, 422]
