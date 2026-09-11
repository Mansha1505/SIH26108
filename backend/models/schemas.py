from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class IndianStandardRecord(BaseModel):
    """
    Core Domain Model for an Indian Standard (IS / BIS).
    Designed to support local JSON records and PostgreSQL + pgvector entities.
    """
    id: str = Field(..., description="Unique identifier (e.g. 'IS-10322-P5-S3')")
    is_number: str = Field(..., description="Indian Standard designation code (e.g. 'IS 10322 (Part 5/Sec 3) : 2012')")
    title: str = Field(..., description="Official Indian Standard title")
    scope: str = Field(..., description="Detailed technical scope description")
    sector: str = Field(..., description="Engineering sector")
    product_category: str = Field(..., description="Product domain category")
    keywords: List[str] = Field(default_factory=list, description="Indexed keywords")
    revision_year: Optional[int] = Field(None, description="Year of standard revision")
    status: str = Field(default="Active (DEMO / SAMPLE DATA)", description="Status flag clearly indicating DEMO / SAMPLE DATA")
    source_url: Optional[str] = Field(None, description="Source attribution URL if available")
    description: Optional[str] = Field(None, description="Extended summary or procurement overview")
    amendments: List[Dict[str, Any]] = Field(default_factory=list, description="List of issued amendments")
    related_standards: List[str] = Field(default_factory=list, description="List of cross-referenced or related IS numbers")


class RecommendationRequest(BaseModel):
    query: Optional[str] = Field(
        None,
        max_length=500,
        description="Natural language procurement specification or product requirement query.",
        examples=["50W LED street light for outdoor municipal roads"]
    )
    requirements: Optional["RequirementExtractionResponse"] = Field(
        None,
        description="Optional structured procurement requirements object extracted from document."
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of recommended Indian Standards to return."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "50W LED street light for outdoor municipal roads",
                "top_k": 5
            }
        }
    )


class VersionIntelligence(BaseModel):
    standard_id: Optional[str] = Field(None, description="Unique standard identifier")
    is_number: str = Field(..., description="Indian Standard designation code")
    revision_year: Optional[int] = Field(None, description="Year of standard revision")
    status: str = Field(..., description="Status flag clearly indicating DEMO / SAMPLE DATA")
    latest_known_amendment_year: Optional[int] = Field(None, description="Year of the latest known amendment in corpus")
    latest_known_amendment_number: Optional[int] = Field(None, description="Number of the latest known amendment in corpus")
    amendment_count: int = Field(0, description="Total number of amendments recorded in corpus")
    has_amendments: bool = Field(False, description="Flag indicating if amendments exist")
    version_status: str = Field(..., description="Deterministic corpus-relative version status description")
    summary: str = Field(..., description="Human-readable version & amendment summary")
    verification_required: bool = Field(True, description="Flag indicating authoritative BIS verification is required")
    source_url: Optional[str] = Field(None, description="Source attribution URL if available")
    amendment_history: List[Dict[str, Any]] = Field(default_factory=list, description="Sorted list of amendment records")


class GraphNodeModel(BaseModel):
    id: str = Field(..., description="Unique standard identifier")
    is_number: str = Field(..., description="Indian Standard designation code")
    title: str = Field(..., description="Official Indian Standard title")
    sector: str = Field(..., description="Engineering sector")
    product_category: str = Field(..., description="Product domain category")
    revision_year: Optional[int] = Field(None, description="Year of standard revision")
    status: str = Field(..., description="Status flag clearly indicating DEMO / SAMPLE DATA")


class GraphEdgeModel(BaseModel):
    source: str = Field(..., description="Source standard ID")
    target: str = Field(..., description="Target standard ID")
    relationship_type: str = Field(..., description="Relationship type enum ('RELATED_STANDARD', 'SAME_PRODUCT_CATEGORY')")
    relationship_label: str = Field(..., description="Human-readable relationship label")
    source_type: str = Field(..., description="Relationship data origin provenance")
    is_inferred: bool = Field(False, description="Flag indicating if edge was inferred vs declared in source data")


class GraphRelationshipModel(BaseModel):
    standard_id: str = Field(..., description="Target standard ID")
    is_number: str = Field(..., description="Indian Standard designation code")
    title: str = Field(..., description="Official Indian Standard title")
    relationship_type: str = Field(..., description="Relationship type enum ('RELATED_STANDARD', 'SAME_PRODUCT_CATEGORY')")
    relationship_label: str = Field(..., description="Human-readable relationship label")
    is_inferred: bool = Field(False, description="Flag indicating if relationship was inferred")


class CertificationAssessment(BaseModel):
    rule_id: Optional[str] = Field(None, description="Matched rule identifier if available")
    product_category: Optional[str] = Field(None, description="Product category domain associated with rule")
    target_standard_ids: List[str] = Field(default_factory=list, description="Target standard IDs covered by rule")
    certification_scheme: str = Field(..., description="Certification scheme designation (e.g. 'BIS Scheme-I (ISI Mark)', 'Compulsory Registration Scheme (CRS)')")
    scheme_status: str = Field(default="requires_authoritative_verification", description="Status flag: 'notified_prototype_qco', 'requires_authoritative_verification', 'recorded_historical_mapping', 'unmapped'")
    applicable_order: Optional[str] = Field(None, description="Notified Quality Control Order or CRO reference")
    order_date: Optional[str] = Field(None, description="Publication date of notification if available")
    effective_date: Optional[str] = Field(None, description="Effective enforcement date if available")
    superseded_by: Optional[str] = Field(None, description="Superseding order or updated framework reference if applicable")
    indication: str = Field(..., description="Cautionary indication ('candidate certification requirement', 'no certification mapping available')")
    matched_standard_id: Optional[str] = Field(None, description="Matched standard ID if applicable")
    matched_product_category: Optional[str] = Field(None, description="Matched product category if applicable")
    applicability_basis: str = Field(..., description="Metadata basis for certification indication")
    source_type: str = Field(default="prototype_rule_dataset", description="Provenance source type ('prototype_rule_dataset')")
    source_reference: str = Field(..., description="Reference document annotation in prototype corpus")
    source_url: Optional[str] = Field(None, description="Source attribution URL if available")
    verification_required: bool = Field(True, description="Flag indicating authoritative BIS verification is required")
    notes: Optional[str] = Field(None, description="Additional context or operational guidance notes")


class CertificationSummary(BaseModel):
    total_rules_matched: int = Field(..., description="Total certification rules matched")
    has_candidate_requirements: bool = Field(..., description="Flag indicating if candidate certification requirements were identified")
    assessments: List[CertificationAssessment] = Field(..., description="List of certification assessment items")
    verification_required: bool = Field(True, description="Flag indicating authoritative BIS verification is required")
    disclaimer: str = Field(
        default="DISCLAIMER: Certification indications are derived from a local prototype rule dataset. They do NOT constitute legal compliance advice. Authoritative verification required.",
        description="Data provenance disclosure notice"
    )


class CertificationAssessmentRequest(BaseModel):
    standard_ids: List[str] = Field(default_factory=list, description="List of standard IDs to assess")
    product_category: Optional[str] = Field(None, description="Optional product domain category to assess")


class CertificationRulesOverviewResponse(BaseModel):
    total_rules: int = Field(..., description="Total certification rules in dataset")
    rules: List[CertificationAssessment] = Field(..., description="List of rules formatted as assessments")
    disclaimer: str = Field(
        default="DISCLAIMER: Prototype certification rules dataset based on curated demo standards. Authoritative verification against official BIS records required.",
        description="Data provenance disclosure notice"
    )


class RecommendationItem(BaseModel):
    id: Optional[str] = Field(None, description="Unique standard identifier")
    is_number: str = Field(..., description="Indian Standard designation code")
    title: str = Field(..., description="Official Indian Standard title")
    scope: str = Field(..., description="Technical scope & applicability description")
    sector: str = Field(..., description="Engineering sector")
    product_category: str = Field(..., description="Product domain category")
    keywords: List[str] = Field(default_factory=list, description="Indexed keywords")
    revision_year: Optional[int] = Field(None, description="Year of standard revision")
    status: str = Field(..., description="Status flag clearly indicating DEMO / SAMPLE DATA")
    source_url: Optional[str] = Field(None, description="Source attribution URL if available")
    description: Optional[str] = Field(None, description="Extended summary or procurement overview")
    amendments: List[Dict[str, Any]] = Field(default_factory=list, description="List of issued amendments")
    related_standards: List[str] = Field(default_factory=list, description="List of cross-referenced or related IS numbers")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="AI-assisted hybrid relevance score in range [0.0, 1.0]. Not a legal confidence probability."
    )
    relative_match_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="User-facing relative match score percentage relative to top candidate in returned set [0.0, 100.0]."
    )
    hybrid_score: Optional[float] = Field(None, description="First-stage hybrid retrieval score (BM25 + Semantic)")
    cross_encoder_score: Optional[float] = Field(None, description="Second-stage Cross-Encoder deep relevance score")
    reasons: List[str] = Field(..., description="Deterministic metadata-based justification reasons")
    version_intelligence: Optional[VersionIntelligence] = Field(
        None,
        description="Deterministic version, revision, and amendment intelligence object"
    )
    graph_relationships: List[GraphRelationshipModel] = Field(
        default_factory=list,
        description="Graph relationship links to neighboring Indian Standards"
    )
    certification_assessment: Optional[CertificationAssessment] = Field(
        None,
        description="Deterministic certification rule assessment object"
    )


class AmendmentsOverviewResponse(BaseModel):
    total_standards: int = Field(..., description="Total standards evaluated in demo corpus")
    standards_with_amendments: int = Field(..., description="Number of standards with recorded amendments")
    items: List[VersionIntelligence] = Field(..., description="Version intelligence list for all corpus standards")
    disclaimer: str = Field(
        default="DISCLAIMER: Prototype amendment tracking on local demo corpus. Authoritative verification against official BIS records required.",
        description="Data provenance disclosure notice"
    )



class NetworkOverviewResponse(BaseModel):
    total_nodes: int = Field(..., description="Total nodes in graph network")
    total_edges: int = Field(..., description="Total edges in graph network")
    declared_edge_count: int = Field(..., description="Number of source-declared related standard edges")
    inferred_edge_count: int = Field(..., description="Number of category-inferred relationship edges")
    unresolved_reference_count: int = Field(..., description="Number of unresolved related standard references")
    nodes: List[GraphNodeModel] = Field(..., description="List of graph nodes")
    edges: List[GraphEdgeModel] = Field(..., description="List of directional graph edges")
    disclaimer: str = Field(
        default="DISCLAIMER: Standards Network based on relationships available in the prototype corpus. Authoritative verification required.",
        description="Data provenance disclosure notice"
    )


class StandardSubgraphResponse(BaseModel):
    standard_id: str = Field(..., description="Center node standard ID")
    depth: int = Field(..., description="Traversal depth limit (depth <= 2)")
    center_node: GraphNodeModel = Field(..., description="Center node metadata")
    total_nodes: int = Field(..., description="Total nodes in subgraph neighborhood")
    total_edges: int = Field(..., description="Total edges in subgraph neighborhood")
    nodes: List[GraphNodeModel] = Field(..., description="List of subgraph nodes")
    edges: List[GraphEdgeModel] = Field(..., description="List of subgraph edges")
    disclaimer: str = Field(
        default="DISCLAIMER: Standards Network subgraph based on relationships available in the prototype corpus.",
        description="Data provenance disclosure notice"
    )




class RecommendationResponse(BaseModel):
    query: str = Field(..., description="Original input query")
    recommendations: List[RecommendationItem] = Field(..., description="Ranked list of recommended standards")
    total_candidates: int = Field(..., description="Total standards evaluated in demo corpus")
    reranking_enabled: bool = Field(default=False, description="Flag indicating if Cross-Encoder reranking stage was applied")
    semantic_status: str = Field(
        default="hf_e5_small",
        description="Status of semantic inference ('hf_e5_small' or 'fallback_bm25')"
    )
    disclaimer: str = Field(
        default="DISCLAIMER: This system provides AI-assisted recommendation scores for demo/sample Indian Standards records. It is NOT a legal compliance engine and recommendations are not legally binding.",
        description="System positioning and legal disclaimer notice."
    )


class DocumentPage(BaseModel):
    page_number: int = Field(..., description="Page number (1-indexed)")
    text: str = Field(..., description="Cleaned extracted text for this page")
    char_count: int = Field(..., description="Character length of page text")


class DocumentExtractionResponse(BaseModel):
    filename: str = Field(..., description="Original uploaded PDF filename")
    page_count: int = Field(..., description="Total pages processed")
    extraction_method: str = Field(..., description="Method used ('pymupdf' or 'pymupdf_with_ocr')")
    text: str = Field(..., description="Unified cleaned text extracted across all pages")
    pages: List[DocumentPage] = Field(..., description="Page-by-page extraction details")
    warning: Optional[str] = Field(None, description="Informational warning or OCR notice if applicable")


class TechnicalAttribute(BaseModel):
    attribute: str = Field(..., description="Technical attribute name (e.g. 'capacity', 'voltage', 'dimension')")
    value: str = Field(..., description="Extracted numerical/technical value (e.g. '50', '240')")
    unit: Optional[str] = Field(None, description="Extracted physical/technical unit (e.g. 'W', 'V', 'mm')")
    source_text: str = Field(..., description="Exact original text snippet from document")


class ProductInfo(BaseModel):
    name: Optional[str] = Field(None, description="Identified product name/noun phrase")
    category: Optional[str] = Field(None, description="Identified product category domain")


class RequirementExtractionRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Raw or cleaned document text from tender/specification")
    filename: Optional[str] = Field(None, description="Source document filename")


class RequirementExtractionResponse(BaseModel):
    product: ProductInfo = Field(default_factory=ProductInfo, description="Identified product details")
    technical_requirements: List[TechnicalAttribute] = Field(default_factory=list, description="Extracted technical attributes")
    standards_mentions: List[str] = Field(default_factory=list, description="Explicitly mentioned IS/Indian Standard codes")
    safety_requirements: List[str] = Field(default_factory=list, description="Extracted safety & protection clauses")
    installation_requirements: List[str] = Field(default_factory=list, description="Extracted installation & environmental conditions")
    keywords: List[str] = Field(default_factory=list, description="Extracted technical keywords")
    raw_text: str = Field(..., description="Reference raw text")
    disclaimer: str = Field(
        default="Detected from document text using deterministic pattern extraction. Not legal compliance advice or verified standard parameters.",
        description="Quality & auditability disclosure notice"
    )


class StructuredRecommendationRequest(BaseModel):
    requirements: RequirementExtractionResponse = Field(..., description="Structured procurement requirements object extracted from document.")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of recommended Indian Standards to return.")


class HealthCheckResponse(BaseModel):
    status: str
    total_standards_indexed: int
    data_source: str
    database_status: Optional[str] = Field(None, description="Database connection status ('connected', 'unavailable', 'not_configured')")
    repository_type: Optional[str] = Field(None, description="Active standards repository type ('json' or 'postgres')")
    vector_backend: Optional[str] = Field(None, description="Active vector backend ('faiss' or 'pgvector')")
    embedding_model: Optional[str] = Field(None, description="Active multilingual dense embedding model name")
    embedding_dimension: Optional[int] = Field(None, description="Dense embedding vector dimensionality")
    reranker_model: Optional[str] = Field(None, description="Active Cross-Encoder reranking model name")
    reranker_enabled: bool = Field(default=False, description="Flag indicating whether reranking is enabled and initialized")



class StandardEvidence(BaseModel):
    standard_id: Optional[str] = Field(None, description="Unique standard identifier")
    is_number: str = Field(..., description="Indian Standard designation code")
    title: str = Field(..., description="Official Indian Standard title")
    scope: str = Field(..., description="Technical scope description")
    sector: str = Field(..., description="Engineering sector")
    product_category: str = Field(..., description="Product category domain")
    keywords: List[str] = Field(default_factory=list, description="Indexed technical keywords")
    revision_year: Optional[int] = Field(None, description="Revision year")
    status: str = Field(..., description="Corpus status string")
    description: Optional[str] = Field(None, description="Extended description if available")
    matched_keywords: List[str] = Field(default_factory=list, description="Keywords matching the query")
    matched_technical_requirements: List[Dict[str, str]] = Field(default_factory=list, description="Technical requirements matching query")
    relevance_score: float = Field(..., description="AI hybrid relevance score")
    relative_match_score: Optional[float] = Field(None, description="User-facing relative match score percentage")
    hybrid_score: Optional[float] = Field(None, description="First-stage hybrid score")
    cross_encoder_score: Optional[float] = Field(None, description="Second-stage Cross-Encoder score")
    amendments: List[Dict[str, Any]] = Field(default_factory=list, description="Recorded amendments")
    related_standards: List[str] = Field(default_factory=list, description="Cross-referenced standards")
    version_intelligence: Optional[VersionIntelligence] = Field(None, description="Version intelligence object")
    graph_relationships: List[GraphRelationshipModel] = Field(default_factory=list, description="Graph relationships")
    certification_assessment: Optional[CertificationAssessment] = Field(None, description="Certification assessment object")
    provenance_sources: List[str] = Field(default_factory=list, description="List of evidence provenance sources")


class EvidencePackage(BaseModel):
    query: str = Field(..., description="Original input query")
    standards_evidence: List[StandardEvidence] = Field(..., description="List of evidence items per standard")
    total_standards_evaluated: int = Field(..., description="Total corpus standards evaluated")
    provenance_disclaimer: str = Field(
        default="DISCLAIMER: Evidence package compiled strictly from available prototype corpus and rule datasets. No external claims manufactured.",
        description="Data provenance notice"
    )


class StandardExplanation(BaseModel):
    standard_id: Optional[str] = Field(None, description="Unique standard identifier")
    is_number: str = Field(..., description="Indian Standard designation code")
    title: str = Field(..., description="Official Indian Standard title")
    why_relevant: str = Field(..., description="Evidence-grounded rationale for relevance")
    matched_requirements: List[str] = Field(default_factory=list, description="Explicit matched requirements or key signals")
    technical_alignment: str = Field(..., description="Explanation of technical parameter and keyword alignment")
    scope_alignment: str = Field(..., description="Explanation of technical scope alignment")
    related_standards_explanation: Optional[str] = Field(None, description="Explanation of cross-referenced standards in graph")
    version_note: str = Field(..., description="Version & amendment status note")
    certification_note: str = Field(..., description="Certification scheme indication note")
    evidence_sources: List[str] = Field(default_factory=list, description="Specific evidence sources used")
    limitations: str = Field(..., description="Prototype limitations and scope boundaries notice")
    verification_required: bool = Field(True, description="Flag indicating authoritative verification is required")


class ExplainRecommendationRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=500, description="Natural language query")
    requirements: Optional[RequirementExtractionResponse] = Field(None, description="Optional structured requirement payload")
    top_k: int = Field(default=5, ge=1, le=20, description="Top K recommendations to explain")


class RecommendationExplanationResponse(BaseModel):
    query: str = Field(..., description="Input procurement query or display requirement")
    explanations: List[StandardExplanation] = Field(..., description="Structured, evidence-grounded explanations per standard")
    generated_by: str = Field(..., description="Explanation generator engine ('deterministic_evidence_engine' or 'llm_grounded_explainer')")
    model: Optional[str] = Field(None, description="Active explanation model designation")
    evidence_count: int = Field(..., description="Number of evidence packages processed")
    verification_required: bool = Field(True, description="Flag indicating authoritative verification is required")
    disclaimer: str = Field(
        default="DISCLAIMER: Explanations are derived strictly from retrieved prototype evidence. They do NOT constitute legal advice or statutory compliance determinations. Authoritative verification against official BIS records is required.",
        description="Legal and positioning disclaimer notice"
    )


class CoverageStatus(str, Enum):
    COVERED = "covered"
    PARTIALLY_COVERED = "partially_covered"
    NOT_EVIDENCED = "not_evidenced"
    REQUIRES_VERIFICATION = "requires_verification"


class RequirementCoverage(BaseModel):
    requirement_id: str = Field(..., description="Unique requirement identifier (e.g. 'REQ-001')")
    requirement_text: str = Field(..., description="Original extracted requirement text or parameter description")
    category: str = Field(..., description="Requirement classification category (e.g. 'product_type', 'capacity', 'voltage', 'material', 'safety')")
    status: CoverageStatus = Field(..., description="Evidence coverage status ('covered', 'partially_covered', 'not_evidenced', 'requires_verification')")
    coverage_score: float = Field(..., ge=0.0, le=1.0, description="Prototype evidence score [0.0, 1.0]. NOT a legal compliance percentage.")
    supporting_standard_ids: List[str] = Field(default_factory=list, description="IS standard numbers or IDs providing evidence")
    evidence: List[str] = Field(default_factory=list, description="Specific supporting evidence clauses or metadata alignments")
    missing_aspects: List[str] = Field(default_factory=list, description="Explicit missing technical attributes or unevidenced specifications")
    verification_required: bool = Field(True, description="Flag indicating authoritative BIS verification is required")
    limitations: List[str] = Field(default_factory=list, description="Scope and prototype dataset limitations")


class GapAnalysisRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=500, description="Natural language procurement query")
    requirements: Optional[RequirementExtractionResponse] = Field(None, description="Optional structured requirements payload extracted from tender document")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top candidates to include in evidence comparison")


class GapAnalysisResponse(BaseModel):
    query: str = Field(..., description="Input procurement query or specification reference")
    total_requirements: int = Field(..., description="Total requirements evaluated")
    covered_count: int = Field(..., description="Number of requirements with full supporting evidence in corpus")
    partially_covered_count: int = Field(..., description="Number of requirements with partial supporting evidence in corpus")
    not_evidenced_count: int = Field(..., description="Number of requirements with NO evidence in the current prototype corpus")
    requires_verification_count: int = Field(..., description="Number of requirements requiring ambiguous/authoritative verification")
    coverage_summary: str = Field(..., description="Human-readable deterministic coverage summary")
    requirements: List[RequirementCoverage] = Field(..., description="Granular per-requirement coverage assessments")
    verification_required: bool = Field(True, description="Flag indicating authoritative verification is required")
    limitations: List[str] = Field(default_factory=list, description="Corpus boundaries and positioning notes")
    disclaimer: str = Field(
        default="DISCLAIMER: Gap analysis compares extracted requirements against available prototype corpus evidence. 'Not evidenced' means no evidence was found in this demo corpus; it does NOT imply that no applicable Indian Standard exists in the official BIS library.",
        description="Legal and data honesty disclosure"
    )


class ReportMetadata(BaseModel):
    report_id: str = Field(..., description="Unique generated report identifier")
    generated_at: str = Field(..., description="ISO 8601 generation timestamp")
    application_name: str = Field(
        default="SIH26108 Indian Standards Intelligence Engine",
        description="Application name and designation"
    )
    disclaimer: str = Field(
        default="DISCLAIMER: AI-assisted standards intelligence report. Demo prototype corpus only. Legal and statutory compliance requires authoritative verification against official BIS records.",
        description="Core prototype report legal disclosure notice"
    )


class ReportInputRequirement(BaseModel):
    query: Optional[str] = Field(None, description="Original natural-language procurement query")
    uploaded_document_name: Optional[str] = Field(None, description="Filename of source procurement document if uploaded")
    raw_text_snippet: Optional[str] = Field(None, description="First 500 characters of raw input text")


class ReportRequest(BaseModel):
    query: Optional[str] = Field(None, max_length=500, description="Natural language procurement query")
    requirements: Optional[RequirementExtractionResponse] = Field(None, description="Optional structured requirements payload")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of recommendations to include")
    uploaded_document_name: Optional[str] = Field(None, description="Filename of source document if available")


class ProcurementReport(BaseModel):
    metadata: ReportMetadata = Field(..., description="Report generation metadata")
    input_requirement: ReportInputRequirement = Field(..., description="Input procurement query or document metadata")
    extracted_requirements: Optional[RequirementExtractionResponse] = Field(None, description="Extracted requirements details")
    recommendations: List[RecommendationItem] = Field(..., description="Recommended Indian Standards")
    version_intelligence: List[VersionIntelligence] = Field(..., description="Version & amendment status per recommendation")
    certification_assessment: CertificationSummary = Field(..., description="Certification assessment details")
    network_information: List[GraphRelationshipModel] = Field(default_factory=list, description="Standards network links")
    gap_analysis: Optional[GapAnalysisResponse] = Field(None, description="Procurement gap analysis details")
    evidence_package: Optional[EvidencePackage] = Field(None, description="Source evidence and provenance package")
    disclaimer: str = Field(
        default="EXPLICIT PROTOTYPE DISCLAIMER: Recommendations are AI-assisted search results based on a demo Indian Standards corpus. Certification/legal status requires authoritative verification against official BIS publications. 'Not evidenced in current prototype corpus' does NOT imply that no Indian Standard exists in the complete BIS library.",
        description="Data honesty and positioning disclaimer"
    )


