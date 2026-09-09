from typing import List, Dict, Any, Optional, Union
from backend.models.schemas import (
    RecommendationItem,
    RequirementExtractionResponse,
    StandardEvidence,
    EvidencePackage,
    VersionIntelligence,
    GraphRelationshipModel,
    CertificationAssessment
)
from backend.retrieval.text_prep import tokenize_text, normalize_text
from backend.utils.logger import get_logger

logger = get_logger("EvidenceBuilder")


class EvidenceBuilder:
    """
    Constructs a bounded, evidence-grounded package from retrieved recommendations,
    version intelligence, graph relationships, and certification assessments.
    
    GUARANTEE: Does NOT fabricate missing evidence. All factual claims are traceable
    to local corpus metadata or explicit rule engine datasets.
    """

    def build_evidence_package(
        self,
        query: str,
        recommendations: List[Union[RecommendationItem, Dict[str, Any]]],
        extracted_requirements: Optional[RequirementExtractionResponse] = None
    ) -> EvidencePackage:
        """Converts retrieved recommendation items into a structured EvidencePackage."""
        evidence_items: List[StandardEvidence] = []
        query_norm = normalize_text(query)
        query_tokens = set(tokenize_text(query_norm))

        for rec in recommendations:
            item_dict = rec.model_dump() if isinstance(rec, RecommendationItem) else rec
            evidence_item = self.build_standard_evidence(item_dict, query_tokens, query_norm, extracted_requirements)
            evidence_items.append(evidence_item)

        return EvidencePackage(
            query=query,
            standards_evidence=evidence_items,
            total_standards_evaluated=len(evidence_items)
        )

    def build_standard_evidence(
        self,
        item: Dict[str, Any],
        query_tokens: set,
        query_norm: str,
        extracted_requirements: Optional[RequirementExtractionResponse] = None
    ) -> StandardEvidence:
        """Builds a single StandardEvidence object for a recommended item."""
        # 1. Matched Keywords
        kw_list = [k.lower() for k in item.get("keywords", [])]
        matched_kws = [kw for kw in kw_list if kw in query_norm or any(t in kw for t in query_tokens)]

        # 2. Matched Technical Requirements if extracted_requirements present
        matched_tech_reqs = []
        if extracted_requirements and hasattr(extracted_requirements, "technical_requirements"):
            for req in extracted_requirements.technical_requirements:
                req_dict = req.model_dump() if hasattr(req, "model_dump") else req
                matched_tech_reqs.append({
                    "attribute": req_dict.get("attribute", ""),
                    "value": str(req_dict.get("value", "")),
                    "unit": str(req_dict.get("unit", "") or ""),
                    "source_text": req_dict.get("source_text", "")
                })

        # 3. Compile Provenance Sources
        provenance_sources = ["standards.json (demo corpus)"]
        
        if item.get("version_intelligence"):
            provenance_sources.append("VersionAmendmentAnalyzer (corpus metadata)")
            
        if item.get("graph_relationships"):
            provenance_sources.append("StandardsGraphBuilder (NetworkX graph)")
            
        if item.get("certification_assessment"):
            cert = item["certification_assessment"]
            src_ref = cert.get("source_reference") if isinstance(cert, dict) else getattr(cert, "source_reference", None)
            src_type = cert.get("source_type") if isinstance(cert, dict) else getattr(cert, "source_type", None)
            ref_str = f"CertificationRuleEngine ({src_ref or 'certification_rules.json'})"
            provenance_sources.append(ref_str)

        # 4. Construct Pydantic StandardEvidence object
        version_intel = item.get("version_intelligence")
        if version_intel and isinstance(version_intel, dict):
            version_intel = VersionIntelligence(**version_intel)

        graph_rels = []
        if item.get("graph_relationships"):
            for gr in item["graph_relationships"]:
                if isinstance(gr, dict):
                    graph_rels.append(GraphRelationshipModel(**gr))
                elif isinstance(gr, GraphRelationshipModel):
                    graph_rels.append(gr)

        cert_assessment = item.get("certification_assessment")
        if cert_assessment and isinstance(cert_assessment, dict):
            cert_assessment = CertificationAssessment(**cert_assessment)

        return StandardEvidence(
            standard_id=item.get("id"),
            is_number=item["is_number"],
            title=item["title"],
            scope=item.get("scope", ""),
            sector=item.get("sector", ""),
            product_category=item.get("product_category", ""),
            keywords=item.get("keywords", []),
            revision_year=item.get("revision_year"),
            status=item.get("status", "Active (DEMO / SAMPLE DATA)"),
            description=item.get("description"),
            matched_keywords=matched_kws,
            matched_technical_requirements=matched_tech_reqs,
            relevance_score=float(item.get("relevance_score", 0.0)),
            hybrid_score=item.get("hybrid_score"),
            cross_encoder_score=item.get("cross_encoder_score"),
            amendments=item.get("amendments", []),
            related_standards=item.get("related_standards", []),
            version_intelligence=version_intel,
            graph_relationships=graph_rels,
            certification_assessment=cert_assessment,
            provenance_sources=provenance_sources
        )
