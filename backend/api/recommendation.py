from fastapi import APIRouter, HTTPException, Query, status
from backend.models.schemas import (
    RecommendationRequest,
    StructuredRecommendationRequest,
    RecommendationResponse,
    HealthCheckResponse,
    AmendmentsOverviewResponse,
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
from backend.services.recommendation_service import service_instance
from backend.utils.logger import get_logger

logger = get_logger("API_Router")
router = APIRouter(prefix="/api", tags=["Standards Recommendation"])


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend applicable Indian Standards for a procurement query",
    description="Analyzes natural-language procurement requirements using BM25 keyword matching and sentence-transformer vector semantic search, returning a ranked list of potentially relevant demo Indian Standards with deterministic reasons."
)
async def recommend_standards(request: RecommendationRequest) -> RecommendationResponse:
    try:
        if (not request.query or not request.query.strip()) and request.requirements is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either query string or structured requirements payload must be provided."
            )
        
        response = service_instance.recommend(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing recommendation request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during recommendation: {str(e)}"
        )


@router.post(
    "/recommend/explain",
    response_model=RecommendationExplanationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate evidence-grounded explanations for standards recommendations",
    description="Compiles bounded evidence packages (standards metadata, technical attributes, version intelligence, standards graph links, certification rules) and generates structured, evidence-grounded explanations without altering retrieval ranking."
)
async def explain_recommendations(request: ExplainRecommendationRequest) -> RecommendationExplanationResponse:
    try:
        if (not request.query or not request.query.strip()) and request.requirements is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either query string or structured requirements payload must be provided for explanation."
            )
        
        response = service_instance.explain_recommendations(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendation explanations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during explanation generation: {str(e)}"
        )


@router.post(
    "/recommend/from-requirements",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend applicable Indian Standards from structured procurement requirements",
    description="Transforms structured procurement requirements into dual BM25 and semantic representations, executing requirement-aware hybrid retrieval."
)
async def recommend_standards_from_requirements(request: StructuredRecommendationRequest) -> RecommendationResponse:
    try:
        response = service_instance.recommend_from_requirements(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing structured recommendation request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during structured recommendation: {str(e)}"
        )


@router.get(
    "/standards/amendments",
    response_model=AmendmentsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get version, revision, and amendment intelligence for all corpus standards",
    description="Returns deterministic version intelligence, revision years, active amendment counts, and latest amendment metadata for all standards in the demo corpus."
)
async def get_standards_amendments() -> AmendmentsOverviewResponse:
    try:
        return service_instance.get_amendments_overview()
    except Exception as e:
        logger.error(f"Error fetching standards amendments overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error fetching amendments overview: {str(e)}"
        )


@router.get(
    "/standards/network",
    response_model=NetworkOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full standards relationship knowledge graph overview",
    description="Returns full NetworkX graph visualization payload containing standard nodes, declared relationship edges, and inferred category edges."
)
async def get_standards_network() -> NetworkOverviewResponse:
    try:
        return service_instance.get_network_overview()
    except Exception as e:
        logger.error(f"Error fetching standards network overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error fetching network overview: {str(e)}"
        )


@router.get(
    "/standards/network/{standard_id}",
    response_model=StandardSubgraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Get standard neighborhood subgraph",
    description="Returns bounded graph neighborhood (depth <= 2) centered on the requested standard ID."
)
async def get_standard_subgraph(
    standard_id: str,
    depth: int = Query(default=1, ge=1, le=2, description="Graph traversal neighborhood depth (bounded 1 to 2)")
) -> StandardSubgraphResponse:
    try:
        subgraph = service_instance.get_standard_subgraph(standard_id, depth=depth)
        if not subgraph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Standard ID or designation '{standard_id}' not found in the graph network."
            )
        return subgraph
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching standard subgraph for '{standard_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error fetching standard subgraph: {str(e)}"
        )



@router.get(
    "/certification/rules",
    response_model=CertificationRulesOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all prototype certification rules",
    description="Returns full list of loaded certification rules mapping Indian Standards and product categories to certification schemes."
)
async def get_certification_rules() -> CertificationRulesOverviewResponse:
    try:
        return service_instance.get_certification_rules()
    except Exception as e:
        logger.error(f"Error fetching certification rules overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error fetching certification rules overview: {str(e)}"
        )


@router.post(
    "/certification/assess",
    response_model=CertificationSummary,
    status_code=status.HTTP_200_OK,
    summary="Assess certification requirements for standard IDs and product category",
    description="Runs deterministic matching against certification rules for provided standard IDs and/or product category."
)
async def assess_certification(request: CertificationAssessmentRequest) -> CertificationSummary:
    try:
        return service_instance.assess_certification(request)
    except Exception as e:
        logger.error(f"Error executing certification assessment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during certification assessment: {str(e)}"
        )


@router.post(
    "/recommend/gap-analysis",
    response_model=GapAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform procurement requirement gap analysis against recommended standards",
    description="Compares structured procurement requirements against evidence from recommended Indian Standards, returning granular coverage assessments."
)
async def analyze_gap(request: GapAnalysisRequest) -> GapAnalysisResponse:
    try:
        if not request.query and request.requirements is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either query string or structured requirements payload must be provided for gap analysis."
            )
        return service_instance.analyze_gaps(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing gap analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during gap analysis: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API health and index status"
)
async def health_check() -> HealthCheckResponse:
    if not service_instance._is_initialized:
        service_instance.initialize()
    
    from backend.config import REPOSITORY_TYPE, VECTOR_BACKEND
    from backend.database.connection import get_db_engine, check_database_connection
    
    db_status = "not_configured"
    if REPOSITORY_TYPE == "postgres" or VECTOR_BACKEND == "pgvector":
        try:
            engine = get_db_engine()
            if check_database_connection(engine):
                db_status = "connected"
            else:
                db_status = "unavailable"
        except Exception:
            db_status = "unavailable"
    else:
        # Check if database is reachable even in JSON mode if needed
        try:
            engine = get_db_engine()
            if check_database_connection(engine):
                db_status = "connected"
            else:
                db_status = "not_configured"
        except Exception:
            db_status = "not_configured"

    model_name = service_instance.embedding_engine.active_model_name if service_instance.embedding_engine else "Unknown"
    vector_dim = service_instance.embedding_engine.vector_dimension if service_instance.embedding_engine else 0
    reranker_model = service_instance.reranker.model_name if service_instance.reranker else None
    reranker_active = service_instance.reranker.is_available if service_instance.reranker else False

    data_src = "PostgreSQL Database" if REPOSITORY_TYPE == "postgres" else "Local JSON Demo Corpus (DEMO / SAMPLE DATA)"

    return HealthCheckResponse(
        status="healthy",
        total_standards_indexed=len(service_instance.standards),
        data_source=data_src,
        database_status=db_status,
        repository_type=REPOSITORY_TYPE,
        vector_backend=VECTOR_BACKEND,
        embedding_model=model_name,
        embedding_dimension=vector_dim,
        reranker_model=reranker_model,
        reranker_enabled=reranker_active
    )


