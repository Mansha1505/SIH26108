import pytest
import os
from fastapi.testclient import TestClient
from backend.main import app
from backend.intelligence.llm_explainer import ExplanationEngine, DeterministicExplainer, ConfigurableLLMExplainer
from backend.intelligence.evidence_builder import EvidenceBuilder
from backend.services.recommendation_service import service_instance
from backend.models.schemas import RecommendationRequest, StandardExplanation, RecommendationExplanationResponse, ExplainRecommendationRequest

client = TestClient(app)


def test_deterministic_explanation_generation():
    """1. Test that deterministic explanation engine generates structured explanations."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    engine = ExplanationEngine()
    rec_response = service_instance.recommend(RecommendationRequest(query="distribution transformers IS 1180", top_k=2))
    
    explanation_resp = engine.generate_explanation(
        query="distribution transformers IS 1180",
        recommendations=rec_response.recommendations
    )

    assert explanation_resp.generated_by == "deterministic_evidence_engine"
    assert len(explanation_resp.explanations) == 2
    assert explanation_resp.verification_required is True

    first_exp = explanation_resp.explanations[0]
    assert first_exp.is_number is not None
    assert first_exp.why_relevant is not None
    assert len(first_exp.matched_requirements) > 0
    assert first_exp.verification_required is True


def test_version_and_certification_explanation_notes():
    """2. Test version note and certification note formatting in explanations."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    engine = ExplanationEngine()
    rec_response = service_instance.recommend(RecommendationRequest(query="distribution transformer IS 1180", top_k=1))
    
    explanation_resp = engine.generate_explanation(
        query="distribution transformer IS 1180",
        recommendations=rec_response.recommendations
    )

    first_exp = explanation_resp.explanations[0]
    assert "revision" in first_exp.version_note.lower() or "amendment" in first_exp.version_note.lower()
    assert "verification required" in first_exp.version_note.lower()
    assert "certification" in first_exp.certification_note.lower() or "scheme" in first_exp.certification_note.lower()


def test_graph_relationship_explanation():
    """3. Test that standards network graph relationships are noted in explanation."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    engine = ExplanationEngine()
    rec_response = service_instance.recommend(RecommendationRequest(query="IS 1180 distribution transformer", top_k=1))
    
    explanation_resp = engine.generate_explanation(
        query="IS 1180 distribution transformer",
        recommendations=rec_response.recommendations
    )

    first_exp = explanation_resp.explanations[0]
    assert first_exp.related_standards_explanation is not None
    assert "Network" in first_exp.related_standards_explanation or "Cross-references" in first_exp.related_standards_explanation


def test_llm_disabled_fallback():
    """4. Test that ConfigurableLLMExplainer falls back to deterministic when disabled."""
    llm_explainer = ConfigurableLLMExplainer()
    assert llm_explainer.enabled is False or llm_explainer.provider == "deterministic"

    builder = EvidenceBuilder()
    if not service_instance._is_initialized:
        service_instance.initialize()

    rec_response = service_instance.recommend(RecommendationRequest(query="XLPE cable", top_k=1))
    package = builder.build_evidence_package("XLPE cable", rec_response.recommendations)

    res = llm_explainer.explain(package)
    assert res.generated_by == "deterministic_evidence_engine"


def test_invalid_llm_output_fallback():
    """5. Test fallback to deterministic explainer if LLM raises exception or fails validation."""
    class FaultyLLMExplainer(ConfigurableLLMExplainer):
        def _call_llm_provider(self, evidence_package):
            raise ValueError("Simulated LLM API timeout or malformed JSON")

    explainer = FaultyLLMExplainer()
    explainer.enabled = True
    explainer.provider = "mock_faulty"

    builder = EvidenceBuilder()
    if not service_instance._is_initialized:
        service_instance.initialize()

    rec_response = service_instance.recommend(RecommendationRequest(query="LED street light", top_k=1))
    package = builder.build_evidence_package("LED street light", rec_response.recommendations)

    res = explainer.explain(package)
    assert res.generated_by == "deterministic_evidence_engine"
    assert len(res.explanations) == 1


def test_pydantic_schema_validation():
    """6. Test Pydantic schema validation for StandardExplanation and response."""
    exp_dict = {
        "standard_id": "IS-1180-P1",
        "is_number": "IS 1180 (Part 1)",
        "title": "Distribution Transformers",
        "why_relevant": "Matches category Transformers",
        "matched_requirements": ["Category: Transformers"],
        "technical_alignment": "100kVA 11kV alignment",
        "scope_alignment": "Covers liquid-immersed transformers",
        "related_standards_explanation": "Connected to IS 2026",
        "version_note": "2014 revision. Verification required.",
        "certification_note": "Candidate Scheme-I requirement",
        "evidence_sources": ["standards.json"],
        "limitations": "Prototype limitations",
        "verification_required": True
    }
    model = StandardExplanation(**exp_dict)
    assert model.standard_id == "IS-1180-P1"
    assert model.verification_required is True


def test_api_recommend_explain_endpoint():
    """7. Test POST /api/recommend/explain API endpoint."""
    response = client.post("/api/recommend/explain", json={"query": "distribution transformer 11kV", "top_k": 2})
    assert response.status_code == 200
    data = response.json()

    assert "explanations" in data
    assert len(data["explanations"]) == 2
    assert "generated_by" in data
    assert data["verification_required"] is True

    first = data["explanations"][0]
    assert "why_relevant" in first
    assert "technical_alignment" in first
    assert "scope_alignment" in first
    assert "version_note" in first
    assert "certification_note" in first
    assert "limitations" in first


def test_recommendation_scores_and_ranking_unchanged():
    """8. Test that generating explanations does NOT alter retrieval scores or ranking order."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    req = RecommendationRequest(query="50W LED street light", top_k=3)
    original_resp = service_instance.recommend(req)
    orig_ids = [r.is_number for r in original_resp.recommendations]
    orig_scores = [r.relevance_score for r in original_resp.recommendations]

    # Now request explanations
    explain_req = ExplainRecommendationRequest(query="50W LED street light", top_k=3)
    explain_resp = service_instance.explain_recommendations(explain_req)
    exp_ids = [e.is_number for e in explain_resp.explanations]

    # Re-verify recommendation pipeline output is identical
    post_resp = service_instance.recommend(req)
    post_ids = [r.is_number for r in post_resp.recommendations]
    post_scores = [r.relevance_score for r in post_resp.recommendations]

    assert orig_ids == post_ids
    assert orig_scores == post_scores
    assert orig_ids == exp_ids
