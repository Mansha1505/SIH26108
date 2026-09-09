import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.schemas import (
    RequirementExtractionResponse,
    ProductInfo,
    TechnicalAttribute
)
from backend.retrieval.query_builder import build_retrieval_query

client = TestClient(app)


def test_build_retrieval_query_transformer():
    """Test requirement-aware query construction for a distribution transformer."""
    reqs = RequirementExtractionResponse(
        product=ProductInfo(name="Distribution Transformer", category="Transformers"),
        technical_requirements=[
            TechnicalAttribute(attribute="capacity", value="100", unit="kVA", source_text="100 kVA"),
            TechnicalAttribute(attribute="voltage", value="11", unit="kV", source_text="11 kV"),
            TechnicalAttribute(attribute="voltage", value="433", unit="V", source_text="433 V"),
            TechnicalAttribute(attribute="frequency", value="50", unit="Hz", source_text="50 Hz"),
            TechnicalAttribute(attribute="efficiency", value="98", unit="%", source_text="98%")
        ],
        standards_mentions=["IS 2026", "IS 1180"],
        safety_requirements=["Oil immersed with fire safety protection", "Outdoor installation"],
        installation_requirements=["Pole mounted outdoor municipal substation"],
        keywords=["transformer", "distribution", "kVA", "substation"],
        raw_text="Sample tender text"
    )

    query_res = build_retrieval_query(reqs)

    # 1. Product/Category preservation
    assert "Distribution Transformer" in query_res.bm25_query
    assert "Transformers" in query_res.bm25_query
    assert "Distribution Transformer" in query_res.semantic_query
    assert "Transformers" in query_res.semantic_query

    # 2. Technical values & units preservation
    assert "100" in query_res.bm25_query
    assert "kVA" in query_res.bm25_query
    assert "100kVA" in query_res.bm25_query
    assert "11" in query_res.bm25_query
    assert "kV" in query_res.bm25_query
    assert "11kV" in query_res.bm25_query

    # 3. IS number preservation
    assert "IS 2026" in query_res.bm25_query
    assert "IS 1180" in query_res.bm25_query
    assert "IS 2026" in query_res.semantic_query

    # 4. Safety & installation preservation
    assert "outdoor" in query_res.bm25_query.lower() or "outdoor" in query_res.semantic_query.lower()
    assert "municipal" in query_res.bm25_query.lower() or "municipal" in query_res.semantic_query.lower()


def test_build_retrieval_query_led_light():
    """Test requirement-aware query construction for an outdoor LED street light."""
    reqs = RequirementExtractionResponse(
        product=ProductInfo(name="LED Street Light", category="Lighting & Luminaires"),
        technical_requirements=[
            TechnicalAttribute(attribute="capacity", value="50", unit="W", source_text="50W"),
            TechnicalAttribute(attribute="voltage", value="240", unit="V", source_text="240V"),
            TechnicalAttribute(attribute="ingress_protection", value="IP66", unit=None, source_text="IP66")
        ],
        standards_mentions=["IS 10322"],
        safety_requirements=["Dielectric strength and surge protection up to 10 kV"],
        installation_requirements=["Outdoor municipal street lighting"],
        keywords=["led", "luminaire", "street", "light"],
        raw_text="Sample LED text"
    )

    query_res = build_retrieval_query(reqs)

    assert "LED Street Light" in query_res.bm25_query
    assert "IP66" in query_res.bm25_query
    assert "50W" in query_res.bm25_query or "50 W" in query_res.bm25_query
    assert "IS 10322" in query_res.bm25_query
    assert "Lighting & Luminaires" in query_res.semantic_query


def test_build_retrieval_query_hdpe_pipe():
    """Test requirement-aware query construction for HDPE water pipes."""
    reqs = RequirementExtractionResponse(
        product=ProductInfo(name="HDPE Pipe", category="Pipes & Fittings"),
        technical_requirements=[
            TechnicalAttribute(attribute="dimension", value="110", unit="mm", source_text="110 mm")
        ],
        standards_mentions=["IS 4984"],
        safety_requirements=["Pressure rating PN 10 for potable water supply"],
        installation_requirements=["Underground municipal water supply pipeline"],
        keywords=["hdpe", "pipe", "water", "polyethylene"],
        raw_text="Sample HDPE pipe text"
    )

    query_res = build_retrieval_query(reqs)

    assert "HDPE Pipe" in query_res.bm25_query
    assert "110" in query_res.bm25_query
    assert "mm" in query_res.bm25_query
    assert "IS 4984" in query_res.bm25_query
    assert "underground" in query_res.bm25_query.lower() or "underground" in query_res.semantic_query.lower()


def test_api_recommend_from_requirements_endpoint():
    """Integration test for POST /api/recommend/from-requirements endpoint."""
    payload = {
        "requirements": {
            "product": {
                "name": "Distribution Transformer",
                "category": "Transformers"
            },
            "technical_requirements": [
                {"attribute": "capacity", "value": "100", "unit": "kVA", "source_text": "100 kVA"},
                {"attribute": "voltage", "value": "11", "unit": "kV", "source_text": "11 kV"}
            ],
            "standards_mentions": ["IS 2026", "IS 1180"],
            "safety_requirements": ["Outdoor oil immersed fire safety"],
            "installation_requirements": ["Substation outdoor installation"],
            "keywords": ["transformer", "distribution"],
            "raw_text": "Distribution transformer 100 kVA 11 kV IS 2026"
        },
        "top_k": 3
    }

    response = client.post("/api/recommend/from-requirements", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "query" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 3
    assert data["total_candidates"] > 0
    assert "DISCLAIMER" in data["disclaimer"]

    top_rec = data["recommendations"][0]
    assert "is_number" in top_rec
    assert "relevance_score" in top_rec
    assert top_rec["relevance_score"] >= 0.0
    assert isinstance(top_rec["reasons"], list)


def test_api_recommend_raw_query_regression():
    """Regression test ensuring legacy POST /api/recommend endpoint functions seamlessly."""
    payload = {
        "query": "50W LED street light for outdoor municipal roads",
        "top_k": 5
    }

    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "50W LED street light for outdoor municipal roads"
    assert len(data["recommendations"]) == 5
    assert data["total_candidates"] > 0


def test_api_recommend_with_embedded_requirements():
    """Test POST /api/recommend endpoint when optional requirements object is provided in payload."""
    payload = {
        "requirements": {
            "product": {
                "name": "LED Street Light",
                "category": "Lighting & Luminaires"
            },
            "technical_requirements": [
                {"attribute": "capacity", "value": "50", "unit": "W", "source_text": "50W"}
            ],
            "standards_mentions": ["IS 10322"],
            "safety_requirements": [],
            "installation_requirements": [],
            "keywords": ["led", "luminaire"],
            "raw_text": "50W LED luminaire"
        },
        "top_k": 3
    }

    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert len(data["recommendations"]) <= 3
    assert "LED" in data["query"] or "Lighting" in data["query"] or "50W" in data["query"]
