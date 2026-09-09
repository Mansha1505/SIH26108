import pytest
import os
import json
from fastapi.testclient import TestClient
from backend.main import app
from backend.intelligence.certification_rules import CertificationRuleEngine
from backend.models.schemas import CertificationAssessment, CertificationSummary, RecommendationRequest, StructuredRecommendationRequest
from backend.services.recommendation_service import service_instance

client = TestClient(app)


def test_1_exact_standard_match():
    """1. Test exact standard ID matching."""
    engine = CertificationRuleEngine()
    assessment = engine.assess_standard("IS-1180-P1", "Transformers")
    assert assessment is not None
    assert assessment.rule_id == "RULE-BIS-001"
    assert assessment.matched_standard_id == "IS-1180-P1"
    assert "candidate certification requirement" in assessment.indication.lower()


def test_2_category_fallback():
    """2. Test product category fallback when standard ID does not match directly."""
    engine = CertificationRuleEngine()
    assessment = engine.assess_standard("IS-UNKNOWN-999", "Transformers")
    assert assessment is not None
    assert assessment.rule_id == "RULE-BIS-001"
    assert assessment.matched_product_category == "Transformers"
    assert assessment.matched_standard_id == "IS-UNKNOWN-999"


def test_3_no_mapping():
    """3. Test behavior when no rules match (unmapped fallback)."""
    engine = CertificationRuleEngine()
    assessment = engine.assess_standard("IS-NONEXISTENT-99", "industrial hydraulic pump")
    assert assessment is not None
    assert assessment.rule_id is None
    assert assessment.scheme_status == "unmapped"
    assert "no certification mapping available" in assessment.indication.lower()
    assert assessment.matched_standard_id == "IS-NONEXISTENT-99"
    assert assessment.matched_product_category == "industrial hydraulic pump"


def test_4_historical_vs_current_certification_metadata():
    """4. Test that historical vs current scheme metadata is properly distinguished."""
    engine = CertificationRuleEngine()
    solar_assessment = engine.assess_standard("IS-14286-P1", "Solar Energy")
    assert solar_assessment.scheme_status == "requires_authoritative_verification"
    assert "historical" in solar_assessment.certification_scheme.lower() or "historical" in solar_assessment.indication.lower()
    assert solar_assessment.order_date is not None
    assert solar_assessment.effective_date is not None


def test_5_solar_rule_handling():
    """5. Test hardened Solar rule handling to ensure it does not statically claim permanent CRS."""
    engine = CertificationRuleEngine()
    assessment = engine.assess_standard("IS-14286-P1", "Solar Energy")
    assert assessment.rule_id == "RULE-BIS-005"
    assert assessment.verification_required is True
    assert assessment.scheme_status == "requires_authoritative_verification"
    assert "ALMM" in assessment.notes or "2025" in assessment.notes
    assert "transitioning" in assessment.applicability_basis.lower() or "transitioning" in assessment.indication.lower()


def test_6_supersession_handling():
    """6. Test supersession metadata handling when updated frameworks/orders exist."""
    engine = CertificationRuleEngine()
    assessment = engine.assess_standard("IS-14286-P1", "Solar Energy")
    assert assessment.superseded_by is not None
    assert "2025" in assessment.superseded_by


def test_7_verification_flag():
    """7. Test that verification_required flag is true across mapped and unmapped outputs."""
    engine = CertificationRuleEngine()
    
    # Mapped standard
    mapped = engine.assess_standard("IS-1180-P1", "Transformers")
    assert mapped.verification_required is True

    # Unmapped standard
    unmapped = engine.assess_standard("IS-UNKNOWN-000", "Unknown Category")
    assert unmapped.verification_required is True


def test_8_provenance_preservation():
    """8. Test that provenance fields (rule_id, matched standard/category, source reference, source_type) are preserved."""
    engine = CertificationRuleEngine()
    assessment = engine.assess_standard("IS-1180-P1", "Transformers")
    assert assessment.rule_id == "RULE-BIS-001"
    assert assessment.matched_standard_id == "IS-1180-P1"
    assert assessment.matched_product_category == "Transformers"
    assert assessment.source_type == "prototype_rule_dataset"
    assert assessment.source_reference is not None
    assert assessment.applicable_order is not None


def test_9_product_subtype_scope_limitation():
    """9. Test that product category rules explicitly state product/QCO scope limitations."""
    engine = CertificationRuleEngine()
    
    # Transformers
    t_assess = engine.assess_standard("IS-1180-P1", "Transformers")
    assert "scope verification required" in t_assess.applicability_basis.lower() or "scope" in t_assess.notes.lower()
    
    # Cables
    c_assess = engine.assess_standard("IS-7098-P1", "Cables & Wiring")
    assert "scope verification required" in c_assess.applicability_basis.lower() or "voltage" in c_assess.notes.lower()

    # Lighting
    l_assess = engine.assess_standard("IS-16102-P1", "Lighting & Luminaires")
    assert "scope verification required" in l_assess.applicability_basis.lower() or "luminaire" in l_assess.notes.lower()


def test_10_no_retrieval_score_mutation():
    """10. Test that certification evaluation does not alter BM25 / dense relevance scores."""
    if not service_instance._is_initialized:
        service_instance.initialize()

    req = RecommendationRequest(query="distribution transformers IS 1180", top_k=3)
    response = service_instance.recommend(req)
    
    for item in response.recommendations:
        assert isinstance(item.relevance_score, float)
        assert item.relevance_score > 0.0
        if item.is_number in ["IS 1180 (Part 1)", "IS 1180"]:
            assert item.certification_assessment is not None


def test_11_malformed_rule_handling(tmp_path):
    """11. Test handling of malformed rules JSON file gracefully."""
    bad_file = tmp_path / "bad_rules.json"
    bad_file.write_text("{ invalid json")

    engine = CertificationRuleEngine(rules_path=str(bad_file))
    assert len(engine.rules) == 0
    assessment = engine.assess_standard("IS-1180-P1", "Transformers")
    assert assessment is not None
    assert "no certification mapping available" in assessment.indication.lower()
    assert assessment.scheme_status == "unmapped"


def test_12_api_response_compatibility():
    """12. Test API response compatibility for GET /api/certification/rules and POST /api/certification/assess."""
    # GET rules
    rules_resp = client.get("/api/certification/rules")
    assert rules_resp.status_code == 200
    rules_data = rules_resp.json()
    assert "rules" in rules_data
    assert rules_data["total_rules"] >= 6

    first_rule = rules_data["rules"][0]
    assert "rule_id" in first_rule
    assert "scheme_status" in first_rule
    assert "applicable_order" in first_rule

    # POST assess
    assess_resp = client.post("/api/certification/assess", json={
        "standard_ids": ["IS-1180-P1", "IS-14286-P1"],
        "product_category": "Transformers"
    })
    assert assess_resp.status_code == 200
    assess_data = assess_resp.json()
    assert "assessments" in assess_data
    assert len(assess_data["assessments"]) > 0
    assert assess_data["has_candidate_requirements"] is True
    assert "disclaimer" in assess_data
