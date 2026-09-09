import io
import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.processing.document_processor import (
    extract_text_from_pdf_bytes,
    clean_extracted_text,
    validate_pdf_bytes
)

def create_sample_pdf_bytes() -> bytes:
    """Helper to generate a valid 2-page sample PDF byte stream in memory using PyMuPDF."""
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text(
        (50, 50),
        "TENDER SPECIFICATION - SECTION 3.2\n"
        "Requirement for 50W LED Street Light Luminaire\n"
        "Operating Voltage: 240V AC, 50Hz. IP66 Protection rating.\n"
        "Mandatory Compliance with IS 10322 (Part 5/Sec 3) : 2012."
    )
    
    # Page 2
    page2 = doc.new_page()
    page2.insert_text(
        (50, 50),
        "SECTION 4: ELECTRICAL CABLES & WIRING\n"
        "Underground Power Cable: XLPE Insulated Armored Cable 1100V.\n"
        "Mandatory Compliance with IS 7098 (Part 1) : 1988."
    )
    
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_clean_extracted_text():
    raw_text = "   50W   LED   street   light  \r\n\r\n\n\nOperating Voltage: 240V   AC\nIS 10322   "
    cleaned = clean_extracted_text(raw_text)
    assert "50W LED street light" in cleaned
    assert "240V AC" in cleaned
    assert "IS 10322" in cleaned

def test_validate_pdf_bytes_invalid():
    with pytest.raises(ValueError, match="not a valid PDF document"):
        validate_pdf_bytes(b"INVALID_HEADER_NOT_PDF", "sample.txt")

def test_pdf_extraction_page_numbering():
    pdf_bytes = create_sample_pdf_bytes()
    result = extract_text_from_pdf_bytes(pdf_bytes, "tender_sample.pdf")
    
    assert result.filename == "tender_sample.pdf"
    assert result.page_count == 2
    assert result.extraction_method == "pymupdf"
    assert len(result.pages) == 2
    
    # Verify Page 1
    p1 = result.pages[0]
    assert p1.page_number == 1
    assert "50W LED Street Light" in p1.text
    assert "IS 10322" in p1.text
    
    # Verify Page 2
    p2 = result.pages[1]
    assert p2.page_number == 2
    assert "1100V" in p2.text
    assert "IS 7098" in p2.text

def test_api_extract_endpoint_valid_pdf():
    pdf_bytes = create_sample_pdf_bytes()
    with TestClient(app) as client:
        files = {"file": ("tender_spec.pdf", pdf_bytes, "application/pdf")}
        response = client.post("/api/documents/extract", files=files)
        assert response.status_code == 200
        data = response.json()
        
        assert data["filename"] == "tender_spec.pdf"
        assert data["page_count"] == 2
        assert data["extraction_method"] == "pymupdf"
        assert len(data["pages"]) == 2
        assert "50W LED" in data["text"]

def test_api_extract_endpoint_invalid_file_type():
    with TestClient(app) as client:
        files = {"file": ("invalid_doc.txt", b"Plain text file content", "text/plain")}
        response = client.post("/api/documents/extract", files=files)
        assert response.status_code == 400
        data = response.json()
        assert "Only PDF documents" in data["detail"]

def test_empty_or_poor_extraction_handling():
    # Create a 1-page PDF with empty text
    doc = fitz.open()
    doc.new_page()  # blank page
    empty_pdf_bytes = doc.tobytes()
    doc.close()
    
    result = extract_text_from_pdf_bytes(empty_pdf_bytes, "blank_scanned.pdf")
    assert result.page_count == 1
    # OCR fallback warning notice triggered
    assert result.warning is not None
    assert "OCR fallback" in result.warning or "Scanned PDF" in result.warning
