from typing import Optional, Any
from backend.retrieval.loader import get_default_repository, StandardsRepository
from backend.retrieval.bm25 import BM25SearchEngine
from backend.retrieval.embeddings import SemanticEmbeddingEngine, get_default_embedding_engine

from backend.retrieval.hybrid import HybridRetriever
from backend.retrieval.reranker import CrossEncoderReranker
from backend.retrieval.ranking import CandidateRanker
from backend.retrieval.query_builder import build_retrieval_query
from backend.intelligence.standards_graph import StandardsGraphBuilder
from backend.intelligence.certification_rules import CertificationRuleEngine
from backend.intelligence.llm_explainer import ExplanationEngine
from backend.intelligence.gap_analysis import GapAnalysisEngine
from backend.models.schemas import (
    RecommendationRequest,
    StructuredRecommendationRequest,
    RecommendationResponse,
    RequirementExtractionResponse,
    NetworkOverviewResponse,
    StandardSubgraphResponse,
    CertificationAssessmentRequest,
    CertificationSummary,
    CertificationRulesOverviewResponse,
    ExplainRecommendationRequest,
    RecommendationExplanationResponse,
    GapAnalysisRequest,
    GapAnalysisResponse
)
from backend.utils.logger import get_logger

logger = get_logger("RecommendationService")


class RecommendationService:
    """
    Core service orchestrating the standards recommendation pipeline.
    Uses StandardsRepository abstraction to load standard records.
    Integrates BM25, Multilingual Dense Embeddings, Cross-Encoder Reranking,
    NetworkX Knowledge Graph Intelligence, Certification Rule Engine, and Explanation Engine.
    """
    def __init__(self, repository: Optional[StandardsRepository] = None):
        self.repository = repository
        self.standards = []
        self.bm25_engine = None
        self.embedding_engine = None
        self.hybrid_retriever = None
        self.reranker = None
        self.graph_builder = None
        self.certification_engine = None
        self.explanation_engine = None
        self.gap_engine = None
        self.ranker = None
        self._is_initialized = False

    def initialize(self, repository: Optional[StandardsRepository] = None, embedding_engine: Optional[Any] = None):
        """Loads corpus via repository abstraction and initializes retrieval & intelligence components."""
        if self._is_initialized:
            return

        logger.info("Initializing RecommendationService...")
        repo = repository or self.repository or get_default_repository()
        self.standards = repo.get_all_standards()

        self.bm25_engine = BM25SearchEngine(self.standards)
        self.embedding_engine = embedding_engine or get_default_embedding_engine(self.standards)
        self.hybrid_retriever = HybridRetriever(self.bm25_engine, self.embedding_engine, alpha=0.6)

        self.reranker = CrossEncoderReranker()

        self.graph_builder = StandardsGraphBuilder()
        self.graph_builder.build_graph(self.standards)

        self.certification_engine = CertificationRuleEngine()
        self.explanation_engine = ExplanationEngine()
        self.gap_engine = GapAnalysisEngine()

        self.ranker = CandidateRanker(
            self.standards,
            graph_builder=self.graph_builder,
            rule_engine=self.certification_engine
        )
        
        self._is_initialized = True
        from backend.config import RERANK_ENABLED
        logger.info(
            f"RecommendationService initialized with {len(self.standards)} standards. "
            f"Reranker Configured={RERANK_ENABLED}, Graph Built={self.graph_builder._is_built}, "
            f"Certification Rules={len(self.certification_engine.rules)}"
        )

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        """
        Executes hybrid retrieval, Cross-Encoder reranking, and explainable ranking.
        Backward compatible with legacy raw query requests.
        """
        if not self._is_initialized:
            self.initialize()

        if request.requirements is not None:
            return self.recommend_from_requirements(
                StructuredRecommendationRequest(requirements=request.requirements, top_k=request.top_k)
            )

        query_str = request.query or ""
        logger.info(f"Processing raw query recommendation request: '{query_str}' (top_k={request.top_k})")
        
        # 1. First-Stage: Retrieve hybrid candidate scores (Min-Max normalized BM25 + Semantic fusion)
        candidate_scores = self.hybrid_retriever.get_candidate_scores(query_str)
        
        # 2. Second-Stage: Apply Cross-Encoder candidate pool reranking (if available)
        reranked_candidates = self.reranker.rerank(
            query=query_str,
            candidates=candidate_scores,
            standards=self.standards
        )

        # 3. Final Ranking: Rank candidates and generate deterministic explanations
        recommendations = self.ranker.rerank_and_explain(
            query=query_str,
            candidates=reranked_candidates,
            top_k=request.top_k
        )
        
        # 4. Format response
        sem_status = getattr(self.embedding_engine, "semantic_status", "fallback_bm25") if self.embedding_engine else "fallback_bm25"
        return RecommendationResponse(
            query=query_str,
            recommendations=recommendations,
            total_candidates=len(self.standards),
            reranking_enabled=self.reranker.is_available,
            semantic_status=sem_status
        )

    def recommend_from_requirements(self, request: StructuredRecommendationRequest) -> RecommendationResponse:
        """
        Executes requirement-aware hybrid retrieval & Cross-Encoder reranking using structured procurement requirements.
        """
        if not self._is_initialized:
            self.initialize()

        # 1. Build structured dual-query representation
        structured_query = build_retrieval_query(request.requirements)
        logger.info(
            f"Processing structured recommendation request for '{structured_query.display_query}': "
            f"BM25='{structured_query.bm25_query}', Semantic='{structured_query.semantic_query}'"
        )

        # 2. First-Stage: Retrieve hybrid candidate scores
        candidate_scores = self.hybrid_retriever.get_candidate_scores(
            query=structured_query.bm25_query,
            semantic_query=structured_query.semantic_query
        )

        # 3. Second-Stage: Apply Cross-Encoder candidate pool reranking
        reranked_candidates = self.reranker.rerank(
            query=structured_query.semantic_query,
            candidates=candidate_scores,
            standards=self.standards
        )

        # 4. Final Ranking: Rank candidates using candidate ranker
        recommendations = self.ranker.rerank_and_explain(
            query=structured_query.bm25_query,
            candidates=reranked_candidates,
            top_k=request.top_k
        )

        # 5. Format response
        sem_status = getattr(self.embedding_engine, "semantic_status", "fallback_bm25") if self.embedding_engine else "fallback_bm25"
        return RecommendationResponse(
            query=structured_query.display_query,
            recommendations=recommendations,
            total_candidates=len(self.standards),
            reranking_enabled=self.reranker.is_available,
            semantic_status=sem_status
        )

    def explain_recommendations(self, request: ExplainRecommendationRequest) -> RecommendationExplanationResponse:
        """
        Builds evidence packages and generates evidence-grounded explanations for top recommended standards.
        Does NOT alter retrieval scores or ranking.
        """
        if not self._is_initialized:
            self.initialize()

        # 1. Obtain recommendations via existing retrieval pipeline
        if request.requirements is not None:
            rec_response = self.recommend_from_requirements(
                StructuredRecommendationRequest(requirements=request.requirements, top_k=request.top_k)
            )
            query_str = rec_response.query
        else:
            rec_response = self.recommend(
                RecommendationRequest(query=request.query, top_k=request.top_k)
            )
            query_str = request.query or ""

        # 2. Generate structured evidence-grounded explanations
        return self.explanation_engine.generate_explanation(
            query=query_str,
            recommendations=rec_response.recommendations,
            extracted_requirements=request.requirements,
            use_llm=False
        )

    def get_amendments_overview(self):
        """
        Generates deterministic version and amendment intelligence overview for all standards in corpus.
        """
        if not self._is_initialized:
            self.initialize()

        from backend.intelligence.version_intelligence import VersionAmendmentAnalyzer
        from backend.models.schemas import AmendmentsOverviewResponse

        analyzer = VersionAmendmentAnalyzer()
        intel_items = [analyzer.analyze(std) for std in self.standards]
        standards_with_amd = sum(1 for item in intel_items if item["has_amendments"])

        return AmendmentsOverviewResponse(
            total_standards=len(self.standards),
            standards_with_amendments=standards_with_amd,
            items=intel_items
        )

    def get_network_overview(self) -> NetworkOverviewResponse:
        """Returns overview of full standards network graph."""
        if not self._is_initialized:
            self.initialize()

        overview_data = self.graph_builder.get_network_overview()
        return NetworkOverviewResponse(**overview_data)

    def get_standard_subgraph(self, standard_id: str, depth: int = 1) -> Optional[StandardSubgraphResponse]:
        """Returns bounded neighborhood subgraph for a given standard_id."""
        if not self._is_initialized:
            self.initialize()

        subgraph_data = self.graph_builder.get_standard_subgraph(standard_id, depth=depth)
        if not subgraph_data:
            return None
        return StandardSubgraphResponse(**subgraph_data)

    def get_certification_rules(self) -> CertificationRulesOverviewResponse:
        """Returns all loaded certification rules formatted as assessments."""
        if not self._is_initialized:
            self.initialize()

        raw_rules = self.certification_engine.get_all_rules()
        rule_assessments = [
            self.certification_engine._build_assessment(r, matched_standard_id=None, matched_product_category=r.get("product_category"))
            for r in raw_rules
        ]
        return CertificationRulesOverviewResponse(
            total_rules=len(rule_assessments),
            rules=rule_assessments
        )

    def assess_certification(self, request: CertificationAssessmentRequest) -> CertificationSummary:
        """Runs certification assessment for requested standard IDs and product category."""
        if not self._is_initialized:
            self.initialize()

        return self.certification_engine.assess_requirements(
            standard_ids=request.standard_ids,
            product_category=request.product_category
        )

    def analyze_gaps(self, request: GapAnalysisRequest) -> GapAnalysisResponse:
        """Evaluates extracted procurement requirements against evidence from recommended Indian Standards."""
        if not self._is_initialized:
            self.initialize()

        query_text = request.query or ""
        if not query_text and request.requirements and request.requirements.raw_text:
            query_text = request.requirements.raw_text

        rec_req = RecommendationRequest(
            query=query_text,
            requirements=request.requirements,
            top_k=request.top_k
        )
        rec_response = self.recommend(rec_req)

        return self.gap_engine.analyze_gaps(
            query=query_text,
            recommendations=rec_response.recommendations,
            requirements=request.requirements
        )


# Global singleton instance for app lifespan injection
service_instance = RecommendationService()



