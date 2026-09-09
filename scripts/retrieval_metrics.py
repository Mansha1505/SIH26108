import math
from typing import List, Dict, Any, Union


def precision_at_k(retrieved_ids: List[str], relevance_map: Dict[str, int], k: int) -> float:
    """
    Computes Precision@K: Fraction of top K retrieved standards that are relevant.
    Formula: Precision@K = (Hits in Top K) / K
    """
    if not retrieved_ids or k <= 0:
        return 0.0
    
    top_k_items = retrieved_ids[:k]
    hits = sum(1 for item_id in top_k_items if relevance_map.get(item_id, 0) > 0)
    return float(hits / k)


def recall_at_k(retrieved_ids: List[str], relevance_map: Dict[str, int], k: int) -> float:
    """
    Computes Recall@K: Fraction of total relevant ground truth standards retrieved in top K.
    Formula: Recall@K = (Hits in Top K) / (Total Relevant Standards in Ground Truth)
    """
    if not retrieved_ids or k <= 0:
        return 0.0

    total_relevant = sum(1 for rel in relevance_map.values() if rel > 0)
    if total_relevant == 0:
        return 0.0

    top_k_items = retrieved_ids[:k]
    hits = sum(1 for item_id in top_k_items if relevance_map.get(item_id, 0) > 0)
    return float(hits / total_relevant)


def mrr_at_k(retrieved_ids: List[str], relevance_map: Dict[str, int], k: int = 5) -> float:
    """
    Computes Mean Reciprocal Rank (MRR@K): Reciprocal rank of the first relevant standard in top K.
    Formula: MRR = 1 / rank_first_relevant
    """
    if not retrieved_ids or k <= 0:
        return 0.0

    for rank, item_id in enumerate(retrieved_ids[:k], start=1):
        if relevance_map.get(item_id, 0) > 0:
            return float(1.0 / rank)
            
    return 0.0


def ndcg_at_k(retrieved_ids: List[str], relevance_map: Dict[str, int], k: int) -> float:
    """
    Computes Normalized Discounted Cumulative Gain (NDCG@K) supporting graded relevance (0, 1, 2).
    Formula:
      DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)
      IDCG@K = sum_{i=1}^{min(|rel|, K)} (2^{ideal_rel_i} - 1) / log2(i + 1)
      NDCG@K = DCG@K / IDCG@K
    """
    if not retrieved_ids or k <= 0:
        return 0.0

    # 1. Compute Discounted Cumulative Gain (DCG@K) for retrieved sequence
    dcg = 0.0
    for rank, item_id in enumerate(retrieved_ids[:k], start=1):
        rel = float(relevance_map.get(item_id, 0))
        if rel > 0:
            dcg += (2.0**rel - 1.0) / math.log2(rank + 1)

    # 2. Compute Ideal Discounted Cumulative Gain (IDCG@K)
    ideal_relevances = sorted([float(rel) for rel in relevance_map.values() if rel > 0], reverse=True)[:k]
    if not ideal_relevances:
        return 0.0

    idcg = sum((2.0**rel - 1.0) / math.log2(rank + 1) for rank, rel in enumerate(ideal_relevances, start=1))

    return float(dcg / idcg) if idcg > 0 else 0.0
