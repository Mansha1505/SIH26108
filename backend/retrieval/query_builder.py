from typing import Dict, Any, Union, Optional
from pydantic import BaseModel, Field
from backend.models.schemas import RequirementExtractionResponse, TechnicalAttribute
from backend.utils.logger import get_logger

logger = get_logger("QueryBuilder")


class StructuredQuery(BaseModel):
    """
    Dual-representation query produced from structured procurement requirements.
    Optimized for lexical BM25 precision and dense vector semantic recall.
    """
    bm25_query: str = Field(..., description="Tokenized keyword string for exact BM25 matching")
    semantic_query: str = Field(..., description="Structured natural text summary for vector embeddings")
    display_query: str = Field(..., description="Short summary phrase for UI display")


def build_retrieval_query(
    requirements: Union[RequirementExtractionResponse, Dict[str, Any]]
) -> StructuredQuery:
    """
    Converts a RequirementExtractionResponse (or dictionary) into a dual query representation.
    
    Preserves exact technical signals:
    - product name and category
    - technical attributes (values & physical units)
    - explicit IS standard mentions
    - safety & installation requirements
    - extracted technical keywords
    """
    # Convert dict to Pydantic model if necessary
    if isinstance(requirements, dict):
        req_obj = RequirementExtractionResponse(**requirements)
    else:
        req_obj = requirements

    product_name = (req_obj.product.name or "").strip()
    product_cat = (req_obj.product.category or "").strip()

    # 1. Collect technical attributes, values, and units
    attr_tokens_bm25 = []
    attr_phrases_sem = []

    for attr in req_obj.technical_requirements:
        val = attr.value.strip()
        unit = (attr.unit or "").strip()
        
        if val:
            attr_tokens_bm25.append(val)
            if unit:
                attr_tokens_bm25.append(unit)
                # Add concatenated token e.g. "100kVA" or "11kV" or "50Hz" or "IP66"
                attr_tokens_bm25.append(f"{val}{unit}")
                attr_phrases_sem.append(f"{attr.attribute}: {val} {unit}")
            else:
                attr_phrases_sem.append(f"{attr.attribute}: {val}")

    # 2. Collect IS mentions
    is_mentions = req_obj.standards_mentions or []
    is_bm25 = " ".join(is_mentions)

    # 3. Collect Safety and Installation context
    safety_clauses = req_obj.safety_requirements or []
    install_clauses = req_obj.installation_requirements or []
    
    # Extract short salient terms from safety & installation
    context_terms = []
    for clause in safety_clauses + install_clauses:
        # Pick relevant terms (e.g. outdoor, municipal, underground, earthing, insulation, surge)
        for kw in ["outdoor", "indoor", "municipal", "underground", "earthing", "grounding", "insulation", "surge", "flame", "submersible", "marine"]:
            if kw in clause.lower() and kw not in context_terms:
                context_terms.append(kw)

    # 4. Keywords
    keywords = req_obj.keywords or []

    # -------------------------------------------------------------
    # BUILD BM25 KEYWORD QUERY
    # -------------------------------------------------------------
    bm25_parts = []
    if product_name:
        bm25_parts.append(product_name)
    if product_cat and product_cat.lower() not in product_name.lower():
        bm25_parts.append(product_cat)

    if is_bm25:
        bm25_parts.append(is_bm25)

    if attr_tokens_bm25:
        bm25_parts.append(" ".join(attr_tokens_bm25))

    if keywords:
        bm25_parts.append(" ".join(keywords))

    if context_terms:
        bm25_parts.append(" ".join(context_terms))

    bm25_query_str = " ".join(bm25_parts).strip()
    if not bm25_query_str:
        bm25_query_str = req_obj.raw_text[:200] if req_obj.raw_text else "standard technical specification"

    # -------------------------------------------------------------
    # BUILD DENSE SEMANTIC QUERY
    # -------------------------------------------------------------
    sem_parts = []
    
    if product_name:
        if product_cat:
            sem_parts.append(f"Technical specification for {product_name} in category {product_cat}.")
        else:
            sem_parts.append(f"Technical specification for {product_name}.")
    elif product_cat:
        sem_parts.append(f"Technical specification for {product_cat}.")

    if attr_phrases_sem:
        sem_parts.append("Key technical parameters: " + ", ".join(attr_phrases_sem) + ".")

    if context_terms:
        sem_parts.append("Operating environment and safety requirements: " + ", ".join(context_terms) + ".")

    if is_mentions:
        sem_parts.append("Referenced Indian Standards: " + ", ".join(is_mentions) + ".")

    if keywords:
        sem_parts.append("Keywords: " + ", ".join(keywords[:5]) + ".")

    semantic_query_str = " ".join(sem_parts).strip()
    if not semantic_query_str:
        semantic_query_str = bm25_query_str

    # -------------------------------------------------------------
    # BUILD DISPLAY QUERY FOR UI
    # -------------------------------------------------------------
    display_parts = []
    if product_name:
        display_parts.append(product_name)
    elif product_cat:
        display_parts.append(product_cat)
        
    top_attrs = [f"{a.value}{a.unit or ''}" for a in req_obj.technical_requirements[:3]]
    if top_attrs:
        display_parts.append(f"({', '.join(top_attrs)})")

    display_query_str = " ".join(display_parts).strip()
    if not display_query_str:
        display_query_str = "Procurement Requirements"

    logger.debug(f"Built retrieval query: BM25='{bm25_query_str}', Semantic='{semantic_query_str}'")

    return StructuredQuery(
        bm25_query=bm25_query_str,
        semantic_query=semantic_query_str,
        display_query=display_query_str
    )
