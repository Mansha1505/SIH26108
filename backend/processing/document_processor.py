import re
from typing import List, Tuple, Optional
import fitz  # PyMuPDF
from backend.models.schemas import DocumentPage, DocumentExtractionResponse
from backend.utils.logger import get_logger

logger = get_logger("DocumentProcessor")

# Maximum upload size: 25 MB
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

def validate_pdf_bytes(pdf_bytes: bytes, filename: str) -> None:
    """
    Validates PDF byte stream size and magic header signature (%PDF-).
    Raises ValueError if invalid.
    """
    if not pdf_bytes:
        raise ValueError("Uploaded file is empty.")

    if len(pdf_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(f"File size exceeds maximum upload limit of 25 MB (Received {(len(pdf_bytes) / (1024*1024)):.1f} MB).")

    # Check PDF magic header bytes %PDF-
    if not pdf_bytes.startswith(b"%PDF-"):
        raise ValueError(f"File '{filename}' is not a valid PDF document (missing %PDF- header signature).")


def clean_extracted_text(text: str) -> str:
    """
    Cleans extracted PDF text while strictly preserving:
    - IS designation codes (e.g. IS 10322, IS 455)
    - Technical parameters & units (e.g. 50W, 240V, 1100V, IP66, 10kV, 2500 kVA, 1000 mm)
    - Line breaks, headings, and bullet points.
    """
    if not text:
        return ""

    # Normalize carriage returns and null bytes
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")

    # Replace multiple horizontal spaces/tabs with single space (preserve newlines)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)

    # Normalize excessive blank lines (more than 2 consecutive newlines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Clean leading/trailing spaces per line
    lines = [line.strip() for line in cleaned.split("\n")]
    cleaned = "\n".join(lines).strip()

    return cleaned


def attempt_ocr_fallback(pdf_bytes: bytes) -> Tuple[str, str, Optional[str]]:
    """
    Modular OCR fallback interface.
    Invoked when PyMuPDF yields minimal or no embedded text (< 50 characters).
    If OCR libraries (pytesseract/pdf2image/Tesseract OCR engine) are unconfigured,
    returns a clear informational warning rather than failing silently.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        logger.info("Attempting OCR text extraction fallback using pytesseract...")
        
        images = convert_from_bytes(pdf_bytes)
        ocr_pages = []
        for img in images:
            page_text = pytesseract.image_to_string(img)
            ocr_pages.append(clean_extracted_text(page_text))
            
        full_ocr_text = "\n\n".join(ocr_pages).strip()
        if full_ocr_text:
            return full_ocr_text, "pymupdf_with_ocr", None
        else:
            return "", "pymupdf", "OCR engine attempted but extracted no readable text from scanned images."
    except ImportError:
        logger.info("OCR dependencies (pytesseract/pdf2image) unconfigured on host.")
        return (
            "",
            "pymupdf",
            "Scanned PDF detected with minimal embedded text. OCR fallback dependencies (Tesseract / pytesseract) are unconfigured on host system."
        )
    except Exception as e:
        logger.warning(f"OCR fallback execution error: {e}")
        return (
            "",
            "pymupdf",
            f"Scanned PDF detected. OCR fallback encountered system error: {str(e)}"
        )


def extract_text_from_pdf_bytes(pdf_bytes: bytes, filename: str) -> DocumentExtractionResponse:
    """
    Extracts text page-by-page from PDF bytes using PyMuPDF (fitz).
    Preserves page numbers, cleans technical whitespace, and triggers OCR fallback notice if needed.
    """
    validate_pdf_bytes(pdf_bytes, filename)

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.error(f"PyMuPDF failed to parse PDF stream for '{filename}': {e}")
        raise ValueError(f"Could not parse PDF file structure: {str(e)}")

    page_count = doc.page_count
    if page_count == 0:
        raise ValueError("PDF document contains 0 pages.")

    pages: List[DocumentPage] = []
    full_text_parts: List[str] = []

    for page_idx in range(page_count):
        page = doc[page_idx]
        raw_text = page.get_text("text")
        cleaned_text = clean_extracted_text(raw_text)
        
        doc_page = DocumentPage(
            page_number=page_idx + 1,
            text=cleaned_text,
            char_count=len(cleaned_text)
        )
        pages.append(doc_page)
        if cleaned_text:
            full_text_parts.append(f"--- Page {page_idx + 1} ---\n" + cleaned_text)

    doc.close()

    unified_text = "\n\n".join(full_text_parts).strip()
    total_chars = sum(p.char_count for p in pages)
    extraction_method = "pymupdf"
    warning = None

    # Trigger OCR fallback if extracted text is insufficient (< 50 chars total)
    if total_chars < 50:
        logger.info(f"Insufficient text extracted ({total_chars} chars) from '{filename}'. Triggering OCR fallback handler.")
        ocr_text, method, ocr_warning = attempt_ocr_fallback(pdf_bytes)
        if ocr_text:
            unified_text = ocr_text
            extraction_method = method
        else:
            warning = ocr_warning

    return DocumentExtractionResponse(
        filename=filename,
        page_count=page_count,
        extraction_method=extraction_method,
        text=unified_text,
        pages=pages,
        warning=warning
    )
