from fastapi import APIRouter, UploadFile, File, HTTPException, status
from backend.models.schemas import (
    DocumentExtractionResponse,
    RequirementExtractionRequest,
    RequirementExtractionResponse
)
from backend.processing.document_processor import extract_text_from_pdf_bytes
from backend.processing.requirement_extractor import extract_requirements
from backend.utils.logger import get_logger

logger = get_logger("API_Documents")
router = APIRouter(prefix="/api/documents", tags=["Document Processing"])

@router.post(
    "/extract",
    response_model=DocumentExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract clean text from uploaded tender or technical specification PDF",
    description="Uploads a PDF file, validates format and size, extracts text page-by-page using PyMuPDF (fitz), applies technical text cleaning, and returns structured page-level text JSON."
)
async def extract_pdf_document(file: UploadFile = File(...)) -> DocumentExtractionResponse:
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file was uploaded."
        )

    # Validate file extension
    filename = file.filename or "uploaded_document.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type for '{filename}'. Only PDF documents (.pdf) are supported."
        )

    try:
        pdf_bytes = await file.read()
        logger.info(f"Received PDF extract request for '{filename}' (size: {len(pdf_bytes)} bytes)")
        
        result = extract_text_from_pdf_bytes(pdf_bytes, filename)
        return result
    except ValueError as ve:
        logger.warning(f"Validation error processing PDF '{filename}': {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Internal error processing PDF '{filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error processing PDF document: {str(e)}"
        )


@router.post(
    "/extract-requirements",
    response_model=RequirementExtractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract structured technical procurement requirements from document text",
    description="Analyzes tender specification text using deterministic regex patterns and domain rules to extract technical attributes (values, units, capacity, voltage, IP ratings), IS mentions, safety clauses, and product metadata."
)
async def extract_requirements_endpoint(
    request: RequirementExtractionRequest
) -> RequirementExtractionResponse:
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text content for requirement extraction cannot be empty."
            )
        
        result = extract_requirements(request.text, request.filename)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting requirements from text: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during requirement extraction: {str(e)}"
        )
