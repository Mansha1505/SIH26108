import math
import numpy as np
from typing import List, Dict, Any, Optional
from backend.config import (
    DEFAULT_CROSS_ENCODER_MODEL,
    RERANK_CANDIDATE_COUNT,
    RERANK_ENABLED,
    RERANK_WEIGHT_BETA
)
from backend.utils.logger import get_logger

logger = get_logger("CrossEncoderReranker")


def sigmoid(x: float) -> float:
    """Computes sigmoid normalization for raw cross-encoder logits into range [0.0, 1.0]."""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 1.0 if x > 0 else 0.0


class CrossEncoderReranker:
    """
    Second-Stage Cross-Encoder Reranking Engine.
    Takes candidate pool from first-stage BM25 + Dense Hybrid Retrieval and applies deep
    cross-attention transformer scoring over (query, candidate_standard_text) pairs.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or DEFAULT_CROSS_ENCODER_MODEL
        self.model = None
        self.is_available: bool = False
        self._is_initialized: bool = False

    def initialize(self):
        """Loads CrossEncoder model once at application startup."""
        if self._is_initialized:
            return

        if not RERANK_ENABLED:
            logger.info("Cross-Encoder reranking is disabled via RERANK_ENABLED configuration.")
            self._is_initialized = True
            return

        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Attempting to load CrossEncoder model: '{self.model_name}'...")
            self.model = CrossEncoder(self.model_name)
            self.is_available = True
            logger.info(f"CrossEncoder model '{self.model_name}' loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load CrossEncoder model '{self.model_name}': {e}. "
                "Application will safely fall back to first-stage hybrid retrieval scores."
            )
            self.is_available = False

        self._is_initialized = True

    def build_candidate_text(self, standard: Dict[str, Any]) -> str:
        """
        Constructs concise, high-signal text representation of standard document for CrossEncoder pair scoring.
        Includes IS number, title, category, scope, and technical description.
        """
        is_num = standard.get("is_number", "")
        title = standard.get("title", "")
        cat = standard.get("product_category", "")
        sector = standard.get("sector", "")
        scope = standard.get("scope", "")
        desc = standard.get("description", "")
        keywords = ", ".join(standard.get("keywords", []))

        text_parts = [
            f"Indian Standard: {is_num}",
            f"Title: {title}",
            f"Category: {cat}",
            f"Sector: {sector}",
            f"Keywords: {keywords}",
            f"Scope: {scope}"
        ]
        if desc:
            text_parts.append(f"Description: {desc[:200]}")

        return " | ".join(text_parts)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        standards: List[Dict[str, Any]],
        candidate_pool_size: Optional[int] = None,
        beta: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Applies CrossEncoder reranking to top N candidates from first-stage hybrid retrieval.
        Combines CrossEncoder score with first-stage hybrid score via weighted fusion:
        final_score = (beta * cross_encoder_norm) + ((1 - beta) * hybrid_score)
        """
        if not self._is_initialized:
            self.initialize()

        if not self.is_available or not self.model or not candidates or not query or not query.strip():
            logger.debug("Reranker not active or empty query; returning original hybrid candidate scores.")
            # Ensure hybrid_score field is populated for consistency
            for c in candidates:
                if "hybrid_score" not in c:
                    c["hybrid_score"] = c.get("relevance_score", 0.0)
                c["reranked"] = False
            return candidates

        pool_size = candidate_pool_size or RERANK_CANDIDATE_COUNT
        fusion_beta = beta if beta is not None else RERANK_WEIGHT_BETA

        # 1. Sort candidate list descending by first-stage hybrid relevance score
        sorted_candidates = sorted(candidates, key=lambda x: x["relevance_score"], reverse=True)
        
        # 2. Select top N candidate pool for reranking
        pool_candidates = sorted_candidates[:pool_size]
        remaining_candidates = sorted_candidates[pool_size:]

        # 3. Construct (query, candidate_text) input pairs
        pairs = []
        for c in pool_candidates:
            std_idx = c["doc_index"]
            std = standards[std_idx]
            cand_text = self.build_candidate_text(std)
            pairs.append((query, cand_text))

        try:
            # 4. Batch prediction using CrossEncoder
            raw_scores = self.model.predict(pairs, show_progress_bar=False)
            if isinstance(raw_scores, (int, float, np.number)):
                raw_scores = [float(raw_scores)]
            else:
                raw_scores = [float(s) for s in raw_scores]

            # 5. Normalize raw cross-encoder scores (sigmoid or min-max normalization)
            norm_scores = [sigmoid(s) for s in raw_scores]

            # 6. Weighted fusion scoring: final_score = beta * cross_norm + (1-beta) * hybrid_score
            reranked_pool = []
            for idx, c in enumerate(pool_candidates):
                hybrid_sc = c.get("relevance_score", 0.0)
                raw_sc = raw_scores[idx]
                norm_sc = norm_scores[idx]

                final_score = (fusion_beta * norm_sc) + ((1.0 - fusion_beta) * hybrid_sc)
                final_score = round(float(final_score), 4)

                c_copy = dict(c)
                c_copy["hybrid_score"] = round(float(hybrid_sc), 4)
                c_copy["cross_encoder_raw"] = round(float(raw_sc), 4)
                c_copy["cross_encoder_norm"] = round(float(norm_sc), 4)
                c_copy["relevance_score"] = final_score
                c_copy["reranked"] = True
                reranked_pool.append(c_copy)

            # Re-sort top pool descending by updated final score
            reranked_pool = sorted(reranked_pool, key=lambda x: x["relevance_score"], reverse=True)

            # Re-attach non-reranked candidates
            for c in remaining_candidates:
                c_copy = dict(c)
                c_copy["hybrid_score"] = round(float(c.get("relevance_score", 0.0)), 4)
                c_copy["reranked"] = False
                reranked_pool.append(c_copy)

            logger.info(f"CrossEncoder reranked top {len(pool_candidates)} candidates for query: '{query[:40]}...'")
            return reranked_pool

        except Exception as e:
            logger.warning(f"Error during CrossEncoder predict: {e}. Falling back to hybrid scores.")
            for c in candidates:
                if "hybrid_score" not in c:
                    c["hybrid_score"] = c.get("relevance_score", 0.0)
                c["reranked"] = False
            return candidates
