"""
FastAPI API Router for Procurement Standards Reports & Export (Phase 10D).

Exposes endpoints for generating structured procurement reports and exporting them as JSON or PDF documents.
"""

from fastapi import APIRouter, HTTPException, status, Response
from backend.models.schemas import ReportRequest, ProcurementReport
from backend.services.recommendation_service import service_instance as rec_service
from backend.services.report_service import report_service_instance as report_service
from backend.utils.logger import get_logger

logger = get_logger("API_Reports")
router = APIRouter(prefix="/api/reports", tags=["Reports & Export"])


@router.post(
    "/generate",
    response_model=ProcurementReport,
    status_code=status.HTTP_200_OK,
    summary="Generate comprehensive procurement standards report",
    description="Assembles recommendations, extracted requirements, version intelligence, certification assessments, standards network links, gap analysis, and evidence provenance into a unified procurement report payload."
)
async def generate_report(request: ReportRequest) -> ProcurementReport:
    try:
        if not request.query and request.requirements is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either query string or structured requirements payload must be provided for report generation."
            )
        
        report = report_service.generate_procurement_report(
            request=request,
            recommendation_service=rec_service
        )
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating procurement report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error generating report: {str(e)}"
        )


@router.post(
    "/export/json",
    status_code=status.HTTP_200_OK,
    summary="Export procurement report as JSON",
    description="Generates procurement report and returns formatted JSON dictionary payload."
)
async def export_json_report(request: ReportRequest):
    try:
        if not request.query and request.requirements is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either query string or structured requirements payload must be provided."
            )
        
        report = report_service.generate_procurement_report(
            request=request,
            recommendation_service=rec_service
        )
        return report_service.export_report_json(report)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting JSON report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error exporting JSON report: {str(e)}"
        )


@router.post(
    "/export/pdf",
    status_code=status.HTTP_200_OK,
    summary="Export publication-quality PDF procurement report",
    description="Generates procurement report and returns a downloadable binary PDF document stream."
)
async def export_pdf_report(request: ReportRequest):
    try:
        if not request.query and request.requirements is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either query string or structured requirements payload must be provided."
            )

        report = report_service.generate_procurement_report(
            request=request,
            recommendation_service=rec_service
        )
        pdf_bytes = report_service.export_report_pdf(report)
        filename = f"procurement_standards_report_{report.metadata.report_id}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes))
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error exporting PDF report: {str(e)}"
        )
