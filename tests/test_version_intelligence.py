import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.intelligence.version_intelligence import VersionAmendmentAnalyzer

client = TestClient(app)


def test_1_revision_year_extraction():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-1",
        "is_number": "IS 1000 : 2020",
        "revision_year": 2020,
        "status": "Active (DEMO DATA)",
        "amendments": []
    }
    result = analyzer.analyze(std)
    assert result["revision_year"] == 2020
    assert result["version_status"] == "Active — latest known revision in corpus"


def test_2_no_amendment_case():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-2",
        "is_number": "IS 2000 : 2015",
        "revision_year": 2015,
        "status": "Active (DEMO DATA)",
        "amendments": []
    }
    result = analyzer.analyze(std)
    assert result["amendment_count"] == 0
    assert result["has_amendments"] is False
    assert result["latest_known_amendment_year"] is None
    assert result["latest_known_amendment_number"] is None


def test_3_one_amendment_case():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-3",
        "is_number": "IS 3000 : 2012",
        "revision_year": 2012,
        "status": "Active (DEMO DATA)",
        "amendments": [
            {"amendment_number": 1, "year": 2016, "title": "Amendment 1 Safety"}
        ]
    }
    result = analyzer.analyze(std)
    assert result["amendment_count"] == 1
    assert result["has_amendments"] is True
    assert result["latest_known_amendment_year"] == 2016
    assert result["latest_known_amendment_number"] == 1
    assert result["version_status"] == "Active — amendments recorded in corpus"


def test_4_multiple_amendments():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-4",
        "is_number": "IS 4000 : 2010",
        "revision_year": 2010,
        "status": "Active (DEMO DATA)",
        "amendments": [
            {"amendment_number": 1, "year": 2012, "title": "Amendment 1"},
            {"amendment_number": 2, "year": 2015, "title": "Amendment 2"},
            {"amendment_number": 3, "year": 2018, "title": "Amendment 3"}
        ]
    }
    result = analyzer.analyze(std)
    assert result["amendment_count"] == 3
    assert result["has_amendments"] is True


def test_5_latest_amendment_selection():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-5",
        "is_number": "IS 5000 : 2008",
        "revision_year": 2008,
        "status": "Active (DEMO DATA)",
        "amendments": [
            {"amendment_number": 1, "year": 2010, "title": "Amd 1"},
            {"amendment_number": 2, "year": 2019, "title": "Amd 2"}
        ]
    }
    result = analyzer.analyze(std)
    assert result["latest_known_amendment_year"] == 2019
    assert result["latest_known_amendment_number"] == 2


def test_6_amendment_sorting():
    analyzer = VersionAmendmentAnalyzer()
    # Provide unordered amendments
    std = {
        "id": "IS-TEST-6",
        "is_number": "IS 6000 : 2005",
        "revision_year": 2005,
        "status": "Active (DEMO DATA)",
        "amendments": [
            {"amendment_number": 2, "year": 2014, "title": "Amd 2"},
            {"amendment_number": 1, "year": 2009, "title": "Amd 1"},
            {"amendment_number": 3, "year": 2021, "title": "Amd 3"}
        ]
    }
    result = analyzer.analyze(std)
    history = result["amendment_history"]
    assert history[0]["year"] == 2021
    assert history[1]["year"] == 2014
    assert history[2]["year"] == 2009


def test_7_missing_amendment_list():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-7",
        "is_number": "IS 7000 : 2011",
        "revision_year": 2011,
        "status": "Active (DEMO DATA)",
        "amendments": None
    }
    result = analyzer.analyze(std)
    assert result["amendment_count"] == 0
    assert result["has_amendments"] is False
    assert result["amendment_history"] == []


def test_8_missing_revision_year():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-8",
        "is_number": "IS 8000",
        "revision_year": None,
        "status": "Active (DEMO DATA)",
        "amendments": []
    }
    result = analyzer.analyze(std)
    assert result["revision_year"] is None
    assert result["version_status"] == "Revision information unavailable"


def test_9_superseded_status():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-9",
        "is_number": "IS 9000 : 1990",
        "revision_year": 1990,
        "status": "Superseded by IS 9001",
        "amendments": []
    }
    result = analyzer.analyze(std)
    assert result["version_status"] == "Superseded"


def test_10_verification_required_behavior():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-10",
        "is_number": "IS 10000 : 2015",
        "revision_year": 2015,
        "status": "Active (DEMO DATA)",
        "amendments": []
    }
    result = analyzer.analyze(std)
    assert result["verification_required"] is True


def test_11_no_mutation_of_original_record():
    analyzer = VersionAmendmentAnalyzer()
    original_amendments = [
        {"amendment_number": 1, "year": 2010, "title": "Amd 1"},
        {"amendment_number": 2, "year": 2020, "title": "Amd 2"}
    ]
    std = {
        "id": "IS-TEST-11",
        "is_number": "IS 11000 : 2005",
        "revision_year": 2005,
        "status": "Active (DEMO DATA)",
        "amendments": original_amendments
    }
    # Deep copy representation before call
    amendments_before = [dict(a) for a in original_amendments]
    
    analyzer.analyze(std)
    
    assert std["amendments"] == amendments_before
    assert std["revision_year"] == 2005


def test_12_malformed_amendment_data():
    analyzer = VersionAmendmentAnalyzer()
    std = {
        "id": "IS-TEST-12",
        "is_number": "IS 12000 : 2016",
        "revision_year": 2016,
        "status": "Active (DEMO DATA)",
        "amendments": [
            "invalid_string_amendment",
            {"amendment_number": "invalid_num", "year": "2018", "title": "Amd Title"},
            {"amendment_number": 2, "year": None, "title": None}
        ]
    }
    # Should not raise exception
    result = analyzer.analyze(std)
    assert isinstance(result, dict)
    assert result["has_amendments"] is True
    # The valid dict entries are extracted safely
    assert result["amendment_count"] == 2


def test_13_recommendation_integration():
    res = client.post("/api/recommend", json={"query": "100 kVA distribution transformer", "top_k": 3})
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    
    item = data["recommendations"][0]
    assert "version_intelligence" in item
    v_intel = item["version_intelligence"]
    assert v_intel is not None
    assert "version_status" in v_intel
    assert "summary" in v_intel
    assert "verification_required" in v_intel


def test_14_existing_api_regression():
    # 1. Health check
    h_res = client.get("/api/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"

    # 2. Amendments overview endpoint
    a_res = client.get("/api/standards/amendments")
    assert a_res.status_code == 200
    a_data = a_res.json()
    assert a_data["total_standards"] >= 14
    assert "standards_with_amendments" in a_data
    assert len(a_data["items"]) >= 14

    # 3. Recommend query
    r_res = client.post("/api/recommend", json={"query": "HDPE pipes for water supply", "top_k": 2})
    assert r_res.status_code == 200
    assert len(r_res.json()["recommendations"]) == 2


def test_15_structured_recommendation_regression():
    req_payload = {
        "requirements": {
            "product": {"name": "LED Street Light", "category": "Lighting"},
            "technical_requirements": [
                {"attribute": "power", "value": "50", "unit": "W", "source_text": "50W LED street light"}
            ],
            "standards_mentions": [],
            "safety_requirements": [],
            "installation_requirements": [],
            "keywords": ["LED", "street light"],
            "raw_text": "50W LED street light"
        },
        "top_k": 2
    }
    res = client.post("/api/recommend/from-requirements", json=req_payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["recommendations"]) > 0
    first_item = data["recommendations"][0]
    assert first_item["version_intelligence"] is not None
