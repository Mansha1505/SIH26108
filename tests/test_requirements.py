import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.processing.requirement_extractor import (
    extract_requirements,
    extract_technical_attributes,
    extract_is_mentions,
    identify_product
)
from backend.models.schemas import RequirementExtractionRequest, RequirementExtractionResponse

# Test sample 1: Electrical equipment (Transformer)
SAMPLE_TRANSFORMER_TEXT = """
TENDER SPECIFICATION NO: ELEC/2026/TR-100
Item Name: Outdoor Distribution Transformer Substation
Technical Parameters:
1. Nominal Capacity: 100 kVA, 3-Phase, 50 Hz frequency.
2. High Voltage Rating: 11 kV, Low Voltage Rating: 433 V AC.
3. Full Load Efficiency: Minimum 98% at rated power factor.
4. Mandatory Compliance with IS 1180 (Part 1) : 2014 and IS 2062.
5. Safety: Outdoor oil-immersed design with overload protection and earthing terminals.
"""

# Test sample 2: Lighting product (LED Street Light)
SAMPLE_LED_TEXT = """
MUNICIPAL ROAD LIGHTING TENDER
Supply of 50W LED Street Light Luminaire
Technical Specification:
- Power Wattage: 50 W
- Operating Input Voltage: 240 V AC, 50 Hz
- IP Rating: IP66 weather protection
- Rated Surge Protection: 10 kV surge suppressor
- Photometric Efficacy: Minimum 85% luminous output
- Applicable Indian Standards: Mandatory compliance with IS 10322 (Part 5/Sec 3) : 2012 and IS 16106 : 2012.
- Environment: Pole mounting for outdoor municipal roads.
"""

# Test sample 3: Non-electrical product category (HDPE Water Pipe & Slag Cement)
SAMPLE_PIPE_CEMENT_TEXT = """
CIVIL WATERWORKS PROCUREMENT SPECIFICATION
High Density Polyethylene (HDPE) Pipes for Municipal Water Supply Pipeline
Parameters:
- Nominal Outer Diameter: 100 mm
- Pressure Rating: 10 bar
- Material: High Density Polyethylene
- Mandatory Compliance with IS 4984 : 2016 for water supply.
- Concrete Foundation: Portland Slag Cement compliant with IS 455 : 2015.
"""


def test_technical_value_and_unit_extraction():
    attrs = extract_technical_attributes(SAMPLE_TRANSFORMER_TEXT)
    attr_names = [a.attribute for a in attrs]
    units = [a.unit for a in attrs if a.unit]
    values = [a.value for a in attrs]

    assert "capacity" in attr_names
    assert "voltage" in attr_names
    assert "frequency" in attr_names
    assert "efficiency" in attr_names

    assert "kVA" in units
    assert "kV" in units
    assert "V" in units
    assert "Hz" in units
    assert "%" in units

    assert "100" in values
    assert "11" in values
    assert "433" in values
    assert "98" in values


def test_percentage_extraction():
    attrs = extract_technical_attributes(SAMPLE_LED_TEXT)
    eff_attr = next((a for a in attrs if a.attribute == "efficiency"), None)
    assert eff_attr is not None
    assert eff_attr.value == "85"
    assert eff_attr.unit == "%"


def test_is_number_extraction():
    is_codes = extract_is_mentions(SAMPLE_LED_TEXT)
    assert len(is_codes) >= 2
    assert any("10322" in code for code in is_codes)
    assert any("16106" in code for code in is_codes)


def test_product_identification_transformer():
    prod = identify_product(SAMPLE_TRANSFORMER_TEXT)
    assert prod.category == "Transformers"
    assert "Transformer" in prod.name


def test_product_identification_led_light():
    prod = identify_product(SAMPLE_LED_TEXT)
    assert prod.category == "Lighting & Luminaires"
    assert "Street Light" in prod.name or "Luminaire" in prod.name


def test_product_identification_non_electrical_pipe():
    prod = identify_product(SAMPLE_PIPE_CEMENT_TEXT)
    assert prod.category == "Pipes & Fittings" or prod.category == "Cement & Building Materials"


def test_multiple_requirements_full_workflow():
    res = extract_requirements(SAMPLE_LED_TEXT, "led_tender.pdf")
    assert isinstance(res, RequirementExtractionResponse)
    assert res.product.category == "Lighting & Luminaires"
    assert len(res.technical_requirements) >= 4
    assert len(res.standards_mentions) >= 2
    assert len(res.safety_requirements) >= 1
    assert len(res.installation_requirements) >= 1
    assert len(res.keywords) >= 3


def test_missing_optional_fields_leave_absent():
    # Text without voltage or current
    short_text = "Supply of Portland Slag Cement for structural concrete works compliant with IS 455."
    res = extract_requirements(short_text)
    
    # Voltage/Current attributes should NOT be invented
    volt_attrs = [a for a in res.technical_requirements if a.attribute == "voltage"]
    curr_attrs = [a for a in res.technical_requirements if a.attribute == "current"]
    assert len(volt_attrs) == 0
    assert len(curr_attrs) == 0


def test_empty_text_handling():
    res = extract_requirements("   ")
    assert res.product.name is None
    assert len(res.technical_requirements) == 0
    assert len(res.standards_mentions) == 0


def test_api_extract_requirements_endpoint():
    with TestClient(app) as client:
        payload = {"text": SAMPLE_TRANSFORMER_TEXT, "filename": "transformer_spec.txt"}
        response = client.post("/api/documents/extract-requirements", json=payload)
        assert response.status_code == 200
        data = response.json()
        
        assert data["product"]["category"] == "Transformers"
        assert len(data["technical_requirements"]) > 0
        assert len(data["standards_mentions"]) > 0
        assert "Detected from document text" in data["disclaimer"]


def test_api_extract_requirements_empty_error():
    with TestClient(app) as client:
        payload = {"text": "  "}
        response = client.post("/api/documents/extract-requirements", json=payload)
        assert response.status_code in [400, 422]


def test_regression_recommend_endpoint_still_works():
    with TestClient(app) as client:
        payload = {"query": "50W LED street light for outdoor municipal roads", "top_k": 3}
        response = client.post("/api/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) > 0
        assert "is_number" in data["recommendations"][0]
