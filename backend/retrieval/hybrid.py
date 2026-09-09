from typing import List, Tuple, Dict, Optional
from backend.utils.logger import get_logger

logger = get_logger("HybridFusion")

def min_max_normalize(scores: List[float]) -> List[float]:
    """
    Min-Max Normalization scaling raw scores to [0.0, 1.0].
    Formula: x_norm = (x - min) / (max - min)
    If max == min, returns 0.0 for all scores if min == 0 else 1.0.
    """
    if not scores:
        return []
    min_val = min(scores)
    max_val = max(scores)
    
    if max_val == min_val:
        return [1.0 if max_val > 0 else 0.0 for _ in scores]
    
    range_val = max_val - min_val
    return [(s - min_val) / range_val for s in scores]


class HybridRetriever:
    """
    Hybrid Retriever combining Lexical BM25 Search and Dense Semantic Vector Search.
    
    SCORING STRATEGY & MATHEMATICAL FORMULATION:
    ----------------------------------------------------------------------
    1. Lexical BM25 score vector: S_bm25 = [s_bm25_1, s_bm25_2, ..., s_bm25_N]
    2. Dense Semantic cosine similarity vector: S_sem = [s_sem_1, s_sem_2, ..., s_sem_N]
    
    3. Normalization:
       S_bm25_norm = MinMaxNormalize(S_bm25)
       S_sem_norm  = MinMaxNormalize(S_sem)  (Cosine similarity is already [0,1], normalized for contrast)
       
    4. Weighted Linear Score Fusion:
       relevance_score_i = alpha * S_sem_norm_i + (1 - alpha) * S_bm25_norm_i
       
       where alpha in [0.0, 1.0] (default alpha = 0.6 favors semantic match while preserving keyword precision).
       
    NOTE ON INTERPRETATION:
    - 'relevance_score' is an AI-assisted relevance score indicating keyword & semantic alignment.
    - It is NOT a legal compliance confidence metric or probability of statutory applicability.
    """
    def __init__(self, bm25_engine, embedding_engine, alpha: float = 0.6):
        self.bm25_engine = bm25_engine
        self.embedding_engine = embedding_engine
        self.alpha = alpha

    def get_candidate_scores(
        self, query: str, semantic_query: Optional[str] = None
    ) -> List[Dict[str, float]]:
        """
        Executes both BM25 and Semantic search, normalizes scores, and merges candidate scores.
        If semantic_query is provided, BM25 searches with `query` and Semantic Engine searches with `semantic_query`.
        Returns list of dicts per document.
        """
        bm25_results = self.bm25_engine.search(query)
        sem_query_to_use = semantic_query if semantic_query is not None else query
        sem_results = self.embedding_engine.search(sem_query_to_use)
        
        num_docs = len(bm25_results)
        bm25_raw_list = [score for _, score in bm25_results]
        sem_raw_list = [score for _, score in sem_results]
        
        bm25_norm_list = min_max_normalize(bm25_raw_list)
        sem_norm_list = min_max_normalize(sem_raw_list)
        
        candidates = []
        for i in range(num_docs):
            bm25_norm = bm25_norm_list[i]
            sem_norm = sem_norm_list[i]
            
            # Weighted fusion
            relevance = (self.alpha * sem_norm) + ((1.0 - self.alpha) * bm25_norm)
            relevance = round(float(relevance), 4)
            
            candidates.append({
                "doc_index": i,
                "bm25_raw": round(bm25_raw_list[i], 4),
                "bm25_norm": round(bm25_norm, 4),
                "semantic_raw": round(sem_raw_list[i], 4),
                "semantic_norm": round(sem_norm, 4),
                "relevance_score": relevance
            })
            
        return candidates
