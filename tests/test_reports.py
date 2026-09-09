"""
Unit and Integration Test Suite for Procurement Reports & PDF/JSON Export (Phase 10D).

Tests report generation from raw query and structured requirements, section content integrity,
version & certification intelligence integration, gap analysis integration, JSON export, PDF generation,
FastAPI endpoints, and default backend configuration preservation.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.schemas import (
    ReportRequest,
    ProcurementReport,
    RequirementExtractionResponse,
    ProductInfo,
    TechnicalAttribute
)
from backend.services.recommendation_service import service_instance
from backend.services.report_service import report_service_instance as report_service
from backend.config import REPOSITORY_TYPE, VECTOR_BACKEND

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def initialize_service():
    """Ensures RecommendationService is initialized before running tests."""
    service_instance.initialize()


# 1. Report generation from raw query
def test_report_generation_from_raw_query():
    req = ReportRequest(query="50W LED street light outdoor", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)

    assert isinstance(report, ProcurementReport)
    assert report.metadata.report_id.startswith("REP-")
    assert report.input_requirement.query == "50W LED street light outdoor"
    assert len(report.recommendations) > 0
    assert len(report.recommendations) <= 3


# 2. Report generation from structured requirements
def test_report_generation_from_structured_requirements():
    extracted = RequirementExtractionResponse(
        product=ProductInfo(name="LED Street Light", category="Lighting"),
        technical_requirements=[
            TechnicalAttribute(attribute="wattage", value="50", unit="W", source_text="50W LED luminaire")
        ],
        standards_mentions=["IS 10322"],
        safety_requirements=["IP66 protection"],
        installation_requirements=["Pole mounted"],
        keywords=["led", "street", "light", "luminaire"],
        raw_text="50W LED street light luminaire conforming to IS 10322 IP66 protection."
    )
    req = ReportRequest(requirements=extracted, top_k=4, uploaded_document_name="tender_specs.pdf")
    report = report_service.generate_procurement_report(req, service_instance)

    assert report.input_requirement.uploaded_document_name == "tender_specs.pdf"
    assert report.extracted_requirements is not None
    assert report.extracted_requirements.product.name == "LED Street Light"
    assert len(report.recommendations) > 0


# 3. Report metadata formatting
def test_report_metadata_formatting():
    req = ReportRequest(query="Transformer specification", top_k=2)
    report = report_service.generate_procurement_report(req, service_instance)

    meta = report.metadata
    assert meta.report_id is not None
    assert meta.generated_at is not None
    assert "SIH26108" in meta.application_name
    assert "DISCLAIMER" in meta.disclaimer


# 4. Extracted requirements inclusion
def test_extracted_requirements_inclusion():
    extracted = RequirementExtractionResponse(
        product=ProductInfo(name="Transformer", category="Transformers"),
        technical_requirements=[],
        keywords=["transformer", "distribution"],
        raw_text="11kV 100kVA Distribution Transformer specification."
    )
    req = ReportRequest(requirements=extracted, top_k=2)
    report = report_service.generate_procurement_report(req, service_instance)

    assert report.extracted_requirements is not None
    assert "transformer" in report.extracted_requirements.keywords


# 5. Recommended standards data structure
def test_recommended_standards_structure():
    req = ReportRequest(query="LED luminaire", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)

    for item in report.recommendations:
        assert item.id is not None
        assert item.is_number is not None
        assert item.title is not None
        assert item.relevance_score >= 0.0 and item.relevance_score <= 1.0
        assert item.status is not None


# 6. Version intelligence section integration
def test_version_intelligence_integration():
    req = ReportRequest(query="LED street light", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)

    assert isinstance(report.version_intelligence, list)
    assert len(report.version_intelligence) > 0
    v = report.version_intelligence[0]
    assert v.is_number is not None
    assert v.verification_required is True


# 7. Certification assessment section integration
def test_certification_assessment_integration():
    req = ReportRequest(query="LED luminaire street light", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)

    cert = report.certification_assessment
    assert cert.total_rules_matched >= 0
    assert cert.verification_required is True
    assert "DISCLAIMER" in cert.disclaimer


# 8. Standards network information section
def test_standards_network_information():
    req = ReportRequest(query="LED light", top_k=5)
    report = report_service.generate_procurement_report(req, service_instance)

    assert isinstance(report.network_information, list)


# 9. Gap analysis section integration
def test_gap_analysis_section_integration():
    req = ReportRequest(query="50W LED street light outdoor IP66", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)

    assert report.gap_analysis is not None
    gap = report.gap_analysis
    assert gap.total_requirements >= 0
    assert gap.verification_required is True


# 10. Evidence provenance section integration
def test_evidence_provenance_integration():
    req = ReportRequest(query="LED street light", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)

    assert report.evidence_package is not None
    assert "DISCLAIMER" in report.evidence_package.provenance_disclaimer


# 11. Explicit prototype disclaimers present
def test_explicit_disclaimers_present():
    req = ReportRequest(query="Street light", top_k=2)
    report = report_service.generate_procurement_report(req, service_instance)

    assert "EXPLICIT PROTOTYPE DISCLAIMER" in report.disclaimer
    assert "authoritative verification" in report.disclaimer.lower()


# 12. JSON export output validity
def test_json_export_output():
    req = ReportRequest(query="LED street light", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)
    json_dict = report_service.export_report_json(report)

    assert isinstance(json_dict, dict)
    assert "metadata" in json_dict
    assert "recommendations" in json_dict
    assert json_dict["metadata"]["report_id"] == report.metadata.report_id


# 13. PDF export generation validity
def test_pdf_export_generation():
    req = ReportRequest(query="50W LED street light outdoor municipal roads", top_k=3)
    report = report_service.generate_procurement_report(req, service_instance)
    pdf_bytes = report_service.export_report_pdf(report)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


# 14. API endpoints test
def test_api_generate_report_endpoint():
    response = client.post("/api/reports/generate", json={"query": "LED street light", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "recommendations" in data
    assert "certification_assessment" in data
    assert "gap_analysis" in data
    assert "disclaimer" in data


def test_api_export_json_endpoint():
    response = client.post("/api/reports/export/json", json={"query": "LED street light", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert data["metadata"]["report_id"].startswith("REP-")


def test_api_export_pdf_endpoint():
    response = client.post("/api/reports/export/pdf", json={"query": "LED street light", "top_k": 3})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert "procurement_standards_report_" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")


def test_api_reports_error_handling_empty_payload():
    """Verify that submitting an empty payload returns a 400 Bad Request error."""
    response = client.post("/api/reports/generate", json={})
    assert response.status_code == 400
    assert "detail" in response.json()

    response_json = client.post("/api/reports/export/json", json={})
    assert response_json.status_code == 400

    response_pdf = client.post("/api/reports/export/pdf", json={})
    assert response_pdf.status_code == 400


def test_api_reports_structured_requirements_export():
    """Verify report generation and PDF export from structured requirement payload."""
    payload = {
        "query": "11kV distribution transformer 100kVA",
        "top_k": 3,
        "uploaded_document_name": "transformer_tender_spec.pdf",
        "requirements": {
            "product": {"name": "Distribution Transformer", "category": "Transformers"},
            "technical_requirements": [
                {"attribute": "voltage", "value": "11kV", "unit": "kV", "source_text": "11kV rating"},
                {"attribute": "capacity", "value": "100", "unit": "kVA", "source_text": "100kVA rating"}
            ],
            "standards_mentions": ["IS 1180"],
            "safety_requirements": ["Oil level indicator"],
            "installation_requirements": ["Outdoor plinth"],
            "keywords": ["transformer", "11kv", "distribution"],
            "raw_text": "11kV 100kVA outdoor distribution transformer specification conforming to IS 1180."
        }
    }
    res_gen = client.post("/api/reports/generate", json=payload)
    assert res_gen.status_code == 200
    assert res_gen.json()["input_requirement"]["uploaded_document_name"] == "transformer_tender_spec.pdf"

    res_pdf = client.post("/api/reports/export/pdf", json=payload)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 1000


# 15. Default repository and vector backend defaults preserved
def test_defaults_preserved():
    assert REPOSITORY_TYPE == "json"
    assert VECTOR_BACKEND == "faiss"

