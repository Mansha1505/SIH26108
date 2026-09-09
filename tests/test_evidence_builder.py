import pytest
from backend.intelligence.evidence_builder import EvidenceBuilder
from backend.services.recommendation_service import service_instance
from backend.models.schemas import RecommendationRequest, RequirementExtractionResponse, ProductInfo


def test_evidence_package_construction():
    """1. Test building an evidence package from retrieved recommendations."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    builder = EvidenceBuilder()
    req = RecommendationRequest(query="distribution transformers IS 1180", top_k=2)
    rec_response = service_instance.recommend(req)

    package = builder.build_evidence_package(
        query="distribution transformers IS 1180",
        recommendations=rec_response.recommendations
    )

    assert package.query == "distribution transformers IS 1180"
    assert len(package.standards_evidence) == 2
    assert package.total_standards_evaluated == 2

    first_ev = package.standards_evidence[0]
    assert first_ev.is_number is not None
    assert first_ev.title is not None
    assert first_ev.scope is not None
    assert isinstance(first_ev.relevance_score, float)
    assert len(first_ev.provenance_sources) > 0


def test_missing_evidence_handling():
    """2. Test handling of minimal recommendation items with missing optional metadata."""
    builder = EvidenceBuilder()
    minimal_item = {
        "id": "IS-MIN-001",
        "is_number": "IS 0000",
        "title": "Minimal Standard Test",
        "scope": "Minimal Scope",
        "sector": "General",
        "product_category": "General",
        "keywords": [],
        "relevance_score": 0.5
    }

    package = builder.build_evidence_package(query="test", recommendations=[minimal_item])
    assert len(package.standards_evidence) == 1
    ev = package.standards_evidence[0]
    assert ev.version_intelligence is None
    assert ev.certification_assessment is None
    assert len(ev.graph_relationships) == 0
    assert "standards.json (demo corpus)" in ev.provenance_sources


def test_evidence_extraction_with_requirements():
    """3. Test building evidence with extracted technical requirements."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    builder = EvidenceBuilder()
    req_extraction = RequirementExtractionResponse(
        product=ProductInfo(category="Transformers"),
        technical_requirements=[
            {"attribute": "capacity", "value": "100", "unit": "kVA", "source_text": "100 kVA transformer"}
        ],
        raw_text="100 kVA distribution transformer"
    )

    rec_response = service_instance.recommend(RecommendationRequest(query="100 kVA transformer", top_k=1))
    package = builder.build_evidence_package(
        query="100 kVA transformer",
        recommendations=rec_response.recommendations,
        extracted_requirements=req_extraction
    )

    first_ev = package.standards_evidence[0]
    assert len(first_ev.matched_technical_requirements) > 0
    assert first_ev.matched_technical_requirements[0]["attribute"] == "capacity"
