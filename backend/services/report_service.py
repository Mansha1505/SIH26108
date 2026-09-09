"""
Procurement Report Generation and PDF/JSON Export Service for SIH26108 (Phase 10D).

Aggregates recommendation results, extracted technical requirements, version & amendment intelligence,
certification assessments, standards network relationships, gap analysis, and evidence provenance into
a unified ProcurementReport model. Generates publication-quality PDF documents using ReportLab.
"""

import io
import datetime
import uuid
from typing import Optional, List, Dict, Any

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)

from backend.models.schemas import (
    ReportRequest,
    ProcurementReport,
    ReportMetadata,
    ReportInputRequirement,
    RecommendationRequest,
    StructuredRecommendationRequest,
    CertificationAssessmentRequest,
    GapAnalysisRequest
)
from backend.intelligence.evidence_builder import EvidenceBuilder
from backend.utils.logger import get_logger

logger = get_logger("ReportService")


class ReportService:
    """
    Service responsible for generating structured procurement reports and exporting them as JSON or PDF.
    Does NOT alter retrieval ranking or recommendation logic.
    """
    def __init__(self):
        self.evidence_builder = EvidenceBuilder()

    def generate_procurement_report(
        self,
        request: ReportRequest,
        recommendation_service: Any
    ) -> ProcurementReport:
        """
        Builds a comprehensive ProcurementReport from existing intelligence services.
        """
        logger.info(f"Generating procurement report for query='{request.query}', top_k={request.top_k}")

        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
        report_id = f"REP-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # 1. Input Requirement metadata
        raw_snippet = None
        if request.requirements and request.requirements.raw_text:
            raw_snippet = request.requirements.raw_text[:500]
        elif request.query:
            raw_snippet = request.query[:500]

        input_req = ReportInputRequirement(
            query=request.query,
            uploaded_document_name=request.uploaded_document_name,
            raw_text_snippet=raw_snippet
        )

        # 2. Recommendations & Version Intelligence
        if request.requirements is not None:
            rec_response = recommendation_service.recommend_from_requirements(
                StructuredRecommendationRequest(requirements=request.requirements, top_k=request.top_k)
            )
        else:
            rec_response = recommendation_service.recommend(
                RecommendationRequest(query=request.query, top_k=request.top_k)
            )

        recommendations = rec_response.recommendations

        # Collect version intelligence
        version_intel_list = [
            item.version_intelligence for item in recommendations if item.version_intelligence
        ]

        # 3. Certification Assessment
        std_ids = [item.id for item in recommendations if item.id]
        product_cat = None
        if request.requirements and request.requirements.product and request.requirements.product.category:
            product_cat = request.requirements.product.category
        elif recommendations:
            product_cat = recommendations[0].product_category

        cert_summary = recommendation_service.assess_certification(
            CertificationAssessmentRequest(
                standard_ids=std_ids,
                product_category=product_cat
            )
        )

        # 4. Standards Network Information
        network_rels = []
        for item in recommendations:
            for rel in item.graph_relationships:
                if rel not in network_rels:
                    network_rels.append(rel)

        # 5. Gap Analysis
        gap_req = GapAnalysisRequest(
            query=request.query,
            requirements=request.requirements,
            top_k=request.top_k
        )
        gap_response = recommendation_service.analyze_gaps(gap_req)

        # 6. Evidence Package
        query_text = request.query or (request.requirements.raw_text if request.requirements else "")
        evidence_package = self.evidence_builder.build_evidence_package(
            query=query_text,
            recommendations=recommendations,
            extracted_requirements=request.requirements
        )

        # Assemble metadata
        metadata = ReportMetadata(
            report_id=report_id,
            generated_at=now_str
        )

        report = ProcurementReport(
            metadata=metadata,
            input_requirement=input_req,
            extracted_requirements=request.requirements,
            recommendations=recommendations,
            version_intelligence=version_intel_list,
            certification_assessment=cert_summary,
            network_information=network_rels,
            gap_analysis=gap_response,
            evidence_package=evidence_package
        )

        logger.info(f"Successfully generated ProcurementReport '{report_id}' with {len(recommendations)} recommendations.")
        return report

    def export_report_json(self, report: ProcurementReport) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary representation of the report."""
        return report.model_dump()

    def export_report_pdf(self, report: ProcurementReport) -> bytes:
        """
        Generates a publication-quality PDF document bytes for the report using ReportLab.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=0.5 * inch,
            rightMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch
        )

        # Styles
        styles = getSampleStyleSheet()
        
        # Color Palette
        NAVY = colors.HexColor("#1A365D")
        TEAL = colors.HexColor("#0D9488")
        DARK_GRAY = colors.HexColor("#1F2937")
        LIGHT_BG = colors.HexColor("#F8FAFC")
        BORDER_GRAY = colors.HexColor("#E2E8F0")
        AMBER = colors.HexColor("#D97706")
        RED = colors.HexColor("#DC2626")
        GREEN = colors.HexColor("#16A34A")

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=NAVY,
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=TEAL,
            spaceAfter=10
        )
        h2_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=DARK_GRAY
        )
        body_bold = ParagraphStyle(
            "ReportBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )
        tbl_header_style = ParagraphStyle(
            "TblHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white
        )
        tbl_cell_style = ParagraphStyle(
            "TblCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=DARK_GRAY
        )
        disclaimer_style = ParagraphStyle(
            "DisclaimerText",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#475569")
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("SIH26108 STANDARDS INTELLIGENCE", subtitle_style))
        elements.append(Paragraph("Procurement Standards Intelligence Report", title_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=8))

        # 2. Metadata Box Table
        meta = report.metadata
        inp = report.input_requirement
        meta_data = [
            [
                Paragraph("<b>Report ID:</b>", body_style), Paragraph(meta.report_id, body_style),
                Paragraph("<b>Generated Date:</b>", body_style), Paragraph(meta.generated_at[:19].replace("T", " "), body_style)
            ],
            [
                Paragraph("<b>Application:</b>", body_style), Paragraph(meta.application_name, body_style),
                Paragraph("<b>Corpus Status:</b>", body_style), Paragraph("Local Demo Prototype Baseline", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[1.1*inch, 2.4*inch, 1.3*inch, 2.7*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
            ('BOX', (0,0), (-1,-1), 1, BORDER_GRAY),
            ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        # Core Disclaimer Box
        disc_box = Table(
            [[Paragraph(f"<b>NOTICE:</b> {report.disclaimer}", disclaimer_style)]],
            colWidths=[7.5*inch]
        )
        disc_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF3C7")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#F59E0B")),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        elements.append(disc_box)
        elements.append(Spacer(1, 10))

        # 3. Section 1: Procurement Input Requirement
        elements.append(Paragraph("1. Input Procurement Requirement", h2_style))
        req_summary = []
        if inp.query:
            req_summary.append([Paragraph("<b>Original Query:</b>", body_style), Paragraph(inp.query, body_style)])
        if inp.uploaded_document_name:
            req_summary.append([Paragraph("<b>Uploaded Document:</b>", body_style), Paragraph(inp.uploaded_document_name, body_style)])
        if inp.raw_text_snippet:
            snippet_text = inp.raw_text_snippet if len(inp.raw_text_snippet) < 300 else inp.raw_text_snippet[:300] + "..."
            req_summary.append([Paragraph("<b>Text Snippet:</b>", body_style), Paragraph(snippet_text, body_style)])

        if req_summary:
            req_table = Table(req_summary, colWidths=[1.5*inch, 6.0*inch])
            req_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
                ('BOX', (0,0), (-1,-1), 0.5, BORDER_GRAY),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            elements.append(req_table)
        elements.append(Spacer(1, 10))

        # 4. Section 2: Extracted Requirements (if available)
        if report.extracted_requirements:
            ext = report.extracted_requirements
            elements.append(Paragraph("2. Extracted Requirements Details", h2_style))
            
            p_name = ext.product.name or "N/A"
            p_cat = ext.product.category or "N/A"
            elements.append(Paragraph(f"<b>Identified Product:</b> {p_name} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Category Domain:</b> {p_cat}", body_style))
            elements.append(Spacer(1, 4))

            if ext.technical_requirements:
                attr_rows = [[
                    Paragraph("Attribute", tbl_header_style),
                    Paragraph("Value", tbl_header_style),
                    Paragraph("Unit", tbl_header_style),
                    Paragraph("Source Snippet", tbl_header_style)
                ]]
                for attr in ext.technical_requirements:
                    attr_rows.append([
                        Paragraph(attr.attribute, tbl_cell_style),
                        Paragraph(attr.value, tbl_cell_style),
                        Paragraph(attr.unit or "-", tbl_cell_style),
                        Paragraph(attr.source_text[:100], tbl_cell_style)
                    ])
                attr_table = Table(attr_rows, colWidths=[1.8*inch, 1.2*inch, 0.8*inch, 3.7*inch])
                attr_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), NAVY),
                    ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
                    ('TOPPADDING', (0,0), (-1,-1), 3),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ]))
                elements.append(attr_table)

            if ext.standards_mentions:
                mentions_str = ", ".join(ext.standards_mentions)
                elements.append(Spacer(1, 4))
                elements.append(Paragraph(f"<b>Explicit Standards Mentioned in Input:</b> {mentions_str}", body_style))
            elements.append(Spacer(1, 10))

        # 5. Section 3: Recommended Indian Standards
        elements.append(Paragraph("3. Recommended Indian Standards", h2_style))
        rec_rows = [[
            Paragraph("Rank", tbl_header_style),
            Paragraph("IS Designation", tbl_header_style),
            Paragraph("Title", tbl_header_style),
            Paragraph("Category", tbl_header_style),
            Paragraph("Relevance Score", tbl_header_style),
            Paragraph("Corpus Status", tbl_header_style)
        ]]
        for idx, item in enumerate(report.recommendations, 1):
            score_pct = f"{item.relevance_score * 100:.1f}%"
            rec_rows.append([
                Paragraph(str(idx), tbl_cell_style),
                Paragraph(f"<b>{item.is_number}</b>", tbl_cell_style),
                Paragraph(item.title, tbl_cell_style),
                Paragraph(item.product_category, tbl_cell_style),
                Paragraph(f"<b>{score_pct}</b>", tbl_cell_style),
                Paragraph(item.status, tbl_cell_style)
            ])

        rec_table = Table(rec_rows, colWidths=[0.5*inch, 1.8*inch, 2.5*inch, 1.2*inch, 0.8*inch, 0.7*inch])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_BG])
        ]))
        elements.append(rec_table)
        elements.append(Spacer(1, 10))

        # 6. Section 4: Version & Amendment Intelligence
        elements.append(Paragraph("4. Version & Amendment Intelligence", h2_style))
        ver_rows = [[
            Paragraph("IS Designation", tbl_header_style),
            Paragraph("Revision Year", tbl_header_style),
            Paragraph("Amendments Recorded", tbl_header_style),
            Paragraph("Corpus Version Status", tbl_header_style),
            Paragraph("Authoritative Check Needed", tbl_header_style)
        ]]
        for ver in report.version_intelligence:
            latest_amd = f"Latest Amd {ver.latest_known_amendment_number} ({ver.latest_known_amendment_year})" if ver.has_amendments else "None recorded"
            ver_rows.append([
                Paragraph(f"<b>{ver.is_number}</b>", tbl_cell_style),
                Paragraph(str(ver.revision_year or "N/A"), tbl_cell_style),
                Paragraph(f"{ver.amendment_count} ({latest_amd})", tbl_cell_style),
                Paragraph(ver.version_status, tbl_cell_style),
                Paragraph("<font color='#D97706'><b>YES (Official BIS Verification Required)</b></font>", tbl_cell_style)
            ])
        ver_table = Table(ver_rows, colWidths=[1.8*inch, 1.0*inch, 2.0*inch, 1.5*inch, 1.2*inch])
        ver_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), TEAL),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(ver_table)
        elements.append(Spacer(1, 10))

        # 7. Section 5: Certification Assessment
        elements.append(Paragraph("5. Certification Assessment", h2_style))
        cert = report.certification_assessment
        cert_rows = [[
            Paragraph("Certification Scheme", tbl_header_style),
            Paragraph("Status / Indication", tbl_header_style),
            Paragraph("Applicable QCO / CRO Reference", tbl_header_style),
            Paragraph("Provenance", tbl_header_style)
        ]]
        for ass in cert.assessments:
            cert_rows.append([
                Paragraph(f"<b>{ass.certification_scheme}</b>", tbl_cell_style),
                Paragraph(ass.indication, tbl_cell_style),
                Paragraph(ass.applicable_order or "N/A", tbl_cell_style),
                Paragraph(ass.source_reference, tbl_cell_style)
            ])
        cert_table = Table(cert_rows, colWidths=[2.2*inch, 2.0*inch, 1.8*inch, 1.5*inch])
        cert_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))
        elements.append(cert_table)
        elements.append(Spacer(1, 10))

        # 8. Section 6: Standards Network Information
        if report.network_information:
            elements.append(Paragraph("6. Standards Network & Relationships", h2_style))
            net_rows = [[
                Paragraph("Target Standard", tbl_header_style),
                Paragraph("Title", tbl_header_style),
                Paragraph("Relationship Type", tbl_header_style),
                Paragraph("Label", tbl_header_style),
                Paragraph("Provenance", tbl_header_style)
            ]]
            for rel in report.network_information[:10]:
                net_rows.append([
                    Paragraph(f"<b>{rel.is_number}</b>", tbl_cell_style),
                    Paragraph(rel.title, tbl_cell_style),
                    Paragraph(rel.relationship_type, tbl_cell_style),
                    Paragraph(rel.relationship_label, tbl_cell_style),
                    Paragraph("Inferred (Category)" if rel.is_inferred else "Source Declared", tbl_cell_style)
                ])
            net_table = Table(net_rows, colWidths=[1.5*inch, 2.3*inch, 1.4*inch, 1.3*inch, 1.0*inch])
            net_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), TEAL),
                ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            elements.append(net_table)
            elements.append(Spacer(1, 10))

        # 9. Section 7: Procurement Gap Analysis
        if report.gap_analysis:
            gap = report.gap_analysis
            elements.append(Paragraph("7. Procurement Gap Analysis", h2_style))
            
            gap_counts_str = (
                f"<b>Total Evaluated:</b> {gap.total_requirements} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<font color='#16A34A'><b>Covered:</b> {gap.covered_count}</font> &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<font color='#D97706'><b>Partially Covered:</b> {gap.partially_covered_count}</font> &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"<font color='#DC2626'><b>Not Evidenced:</b> {gap.not_evidenced_count}</font>"
            )
            elements.append(Paragraph(gap_counts_str, body_style))
            elements.append(Spacer(1, 4))

            gap_rows = [[
                Paragraph("Req ID", tbl_header_style),
                Paragraph("Requirement Text", tbl_header_style),
                Paragraph("Category", tbl_header_style),
                Paragraph("Coverage Status", tbl_header_style),
                Paragraph("Supporting Evidence", tbl_header_style)
            ]]
            for req_cov in gap.requirements:
                status_clr = "#16A34A" if req_cov.status == "covered" else ("#D97706" if req_cov.status == "partially_covered" else "#DC2626")
                ev_text = "; ".join(req_cov.evidence) if req_cov.evidence else "No direct evidence found"
                gap_rows.append([
                    Paragraph(req_cov.requirement_id, tbl_cell_style),
                    Paragraph(req_cov.requirement_text, tbl_cell_style),
                    Paragraph(req_cov.category, tbl_cell_style),
                    Paragraph(f"<font color='{status_clr}'><b>{req_cov.status.upper()}</b></font>", tbl_cell_style),
                    Paragraph(ev_text, tbl_cell_style)
                ])
            gap_table = Table(gap_rows, colWidths=[0.8*inch, 2.2*inch, 1.0*inch, 1.3*inch, 2.2*inch])
            gap_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), NAVY),
                ('GRID', (0,0), (-1,-1), 0.5, BORDER_GRAY),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            elements.append(gap_table)
            elements.append(Spacer(1, 10))

        # 10. Section 8: Evidence Provenance & Final Disclaimers
        elements.append(Paragraph("8. Evidence Provenance & Prototype Boundaries", h2_style))
        prov_text = (
            "<b>Data Attribution:</b> Evidence and recommendation justification scores are computed strictly from "
            "indexed Indian Standards metadata and curated demo Quality Control Order rules.<br/>"
            "<b>Corpus Boundary Notice:</b> This report is generated against a local prototype dataset. "
            "A status of 'Not Evidenced' indicates absence in this demo corpus and MUST NOT be construed as "
            "non-existence in official Bureau of Indian Standards (BIS) publications."
        )
        elements.append(Paragraph(prov_text, body_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Global singleton instance
report_service_instance = ReportService()
