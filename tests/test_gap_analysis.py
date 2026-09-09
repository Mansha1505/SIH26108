import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.intelligence.gap_analysis import GapAnalysisEngine
from backend.services.recommendation_service import service_instance
from backend.models.schemas import (
    CoverageStatus,
    GapAnalysisRequest,
    GapAnalysisResponse,
    RequirementCoverage,
    RecommendationRequest
)

client = TestClient(app)


def test_gap_analysis_engine_basic_coverage():
    """1-6. Test technical attribute, product, capacity, voltage, material, and application matching."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    engine = GapAnalysisEngine()
    
    # 1. Query: Transformer with capacity 100 kVA, 11 kV, 433 V
    rec_res = service_instance.recommend(RecommendationRequest(query="100 kVA 11 kV 433 V three phase oil immersed distribution transformer", top_k=2))
    gap_res = engine.analyze_gaps(
        query="100 kVA 11 kV 433 V three phase oil immersed distribution transformer",
        recommendations=rec_res.recommendations
    )

    assert gap_res.total_requirements > 0
    assert gap_res.covered_count >= 1
    assert gap_res.verification_required is True

    # Verify specific covered requirements
    texts = [r.requirement_text for r in gap_res.requirements]
    statuses = {r.requirement_text: r.status for r in gap_res.requirements}
    
    # Should have covered capacity or voltage or product
    assert any(s == CoverageStatus.COVERED for s in statuses.values())


def test_gap_analysis_material_and_application_matching():
    """3 & 5. Test HDPE material and potable water supply application matching."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    engine = GapAnalysisEngine()
    rec_res = service_instance.recommend(RecommendationRequest(query="HDPE potable water supply pipe", top_k=2))
    gap_res = engine.analyze_gaps(
        query="HDPE potable water supply pipe",
        recommendations=rec_res.recommendations
    )

    assert gap_res.covered_count >= 1
    hdpe_reqs = [r for r in gap_res.requirements if "hdpe" in r.requirement_text.lower() or "pipe" in r.requirement_text.lower()]
    assert len(hdpe_reqs) > 0
    assert hdpe_reqs[0].status == CoverageStatus.COVERED
    assert any("IS 4984" in std_id for std_id in hdpe_reqs[0].supporting_standard_ids)


def test_not_evidenced_status_and_wording_guardrail():
    """9 & 14. Test 'not_evidenced' status and strictly enforce 'Not evidenced in current prototype corpus' phrasing."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    engine = GapAnalysisEngine()
    
    # Query with a requirement deliberately absent from the prototype corpus
    query = "Transformer with acoustic noise limit of 45 dB"
    rec_res = service_instance.recommend(RecommendationRequest(query=query, top_k=2))
    gap_res = engine.analyze_gaps(query=query, recommendations=rec_res.recommendations)

    assert gap_res.not_evidenced_count >= 1

    # Find the acoustic noise requirement
    noise_reqs = [r for r in gap_res.requirements if "noise" in r.requirement_text.lower() or "45" in r.requirement_text.lower()]
    assert len(noise_reqs) > 0
    noise_req = noise_reqs[0]

    assert noise_req.status == CoverageStatus.NOT_EVIDENCED
    assert noise_req.coverage_score == 0.0
    assert len(noise_req.supporting_standard_ids) == 0

    # STRICT GUARDRAIL CHECK: MUST NOT SAY "No Indian Standard exists" or "No BIS standard"
    full_output_text = (
        gap_res.coverage_summary + " " +
        " ".join(noise_req.missing_aspects) + " " +
        " ".join(noise_req.limitations) + " " +
        gap_res.disclaimer
    )

    assert "no indian standard exists" not in full_output_text.lower()
    assert "no bis standard" not in full_output_text.lower()
    assert "not evidenced in current prototype corpus" in full_output_text.lower()


def test_requires_verification_status():
    """10. Test requires_verification status for general safety/installation clause."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    engine = GapAnalysisEngine()
    query = "50W LED street light with IP65 outdoor weather protection"
    rec_res = service_instance.recommend(RecommendationRequest(query=query, top_k=2))
    gap_res = engine.analyze_gaps(query=query, recommendations=rec_res.recommendations)

    assert gap_res.total_requirements > 0
    assert gap_res.verification_required is True


def test_pydantic_validation():
    """15. Test Pydantic schema validation for RequirementCoverage and GapAnalysisResponse."""
    req_cov = RequirementCoverage(
        requirement_id="REQ-001",
        requirement_text="11 kV voltage rating",
        category="voltage",
        status=CoverageStatus.COVERED,
        coverage_score=1.0,
        supporting_standard_ids=["IS 7098 (Part 2)"],
        evidence=["Scope covers 3.3 kV up to 33 kV"],
        missing_aspects=[],
        verification_required=True,
        limitations=["Prototype dataset limitation"]
    )
    assert req_cov.requirement_id == "REQ-001"
    assert req_cov.status == CoverageStatus.COVERED
    assert req_cov.coverage_score == 1.0

    resp = GapAnalysisResponse(
        query="XLPE cable 11 kV",
        total_requirements=1,
        covered_count=1,
        partially_covered_count=0,
        not_evidenced_count=0,
        requires_verification_count=0,
        coverage_summary="1 requirement covered.",
        requirements=[req_cov],
        verification_required=True,
        limitations=["Demo corpus limitation"]
    )
    assert resp.total_requirements == 1
    assert resp.covered_count == 1


def test_score_and_ranking_isolation():
    """13. Test that gap analysis does NOT alter retrieval scores or candidate ranking order."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    req = RecommendationRequest(query="crystalline silicon photovoltaic module", top_k=3)
    orig_resp = service_instance.recommend(req)
    orig_ids = [r.is_number for r in orig_resp.recommendations]
    orig_scores = [r.relevance_score for r in orig_resp.recommendations]

    # Run gap analysis
    engine = GapAnalysisEngine()
    _ = engine.analyze_gaps(query="crystalline silicon photovoltaic module", recommendations=orig_resp.recommendations)

    # Re-fetch recommendation
    post_resp = service_instance.recommend(req)
    post_ids = [r.is_number for r in post_resp.recommendations]
    post_scores = [r.relevance_score for r in post_resp.recommendations]

    assert orig_ids == post_ids
    assert orig_scores == post_scores


def test_api_gap_analysis_endpoint():
    """16. Test POST /api/recommend/gap-analysis API endpoint."""
    response = client.post("/api/recommend/gap-analysis", json={"query": "XLPE cable 11 kV", "top_k": 2})
    assert response.status_code == 200
    data = response.json()

    assert "total_requirements" in data
    assert "covered_count" in data
    assert "requirements" in data
    assert len(data["requirements"]) > 0
    assert data["verification_required"] is True

