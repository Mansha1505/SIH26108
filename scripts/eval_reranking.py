import sys
import os
import math
from typing import List, Dict, Set

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath("."))

from backend.services.recommendation_service import service_instance
from backend.models.schemas import RecommendationRequest

# Ground Truth Target Relevant Standards for the 8 Evaluation Test Queries
EVAL_DATASET = [
    {
        "type": "English Transformer",
        "query": "100 kVA three phase distribution transformer",
        "relevant_is": {"IS 1180 (Part 1) : 2014", "IS 2026 (Part 1) : 2011"}
    },
    {
        "type": "Hindi Transformer",
        "query": "100 केवीए तीन फेज वितरण ट्रांसफार्मर",
        "relevant_is": {"IS 1180 (Part 1) : 2014", "IS 2026 (Part 1) : 2011"}
    },
    {
        "type": "Hinglish Transformer",
        "query": "100 kVA ka three phase distribution transformer chahiye",
        "relevant_is": {"IS 1180 (Part 1) : 2014", "IS 2026 (Part 1) : 2011"}
    },
    {
        "type": "Detailed Transformer",
        "query": "100 kVA 11 kV/433 V three phase oil immersed distribution transformer, outdoor type, 50 Hz, suitable for electricity distribution.",
        "relevant_is": {"IS 1180 (Part 1) : 2014", "IS 2026 (Part 1) : 2011"}
    },
    {
        "type": "HDPE Pipe",
        "query": "110 mm HDPE water pipe PN 10",
        "relevant_is": {"IS 4984 : 2016"}
    },
    {
        "type": "LED Luminaire",
        "query": "50W LED street light luminaire",
        "relevant_is": {"IS 10322 (Part 5/Sec 3) : 2012", "IS 16102 (Part 1) : 2012"}
    },
    {
        "type": "Cement",
        "query": "Portland slag cement for structural concrete",
        "relevant_is": {"IS 455 : 2015", "IS 1489 (Part 1) : 2015"}
    },
    {
        "type": "Semantic Concept",
        "query": "Electrical equipment required to reduce 11 kV distribution voltage to 433 V for local power distribution.",
        "relevant_is": {"IS 1180 (Part 1) : 2014", "IS 2026 (Part 1) : 2011"}
    }
]


def calculate_mrr(retrieved_items: List[str], relevant_set: Set[str]) -> float:
    """Calculates Mean Reciprocal Rank (MRR) for retrieved items."""
    for rank, is_num in enumerate(retrieved_items, start=1):
        if is_num in relevant_set:
            return 1.0 / rank
    return 0.0


def calculate_ndcg(retrieved_items: List[str], relevant_set: Set[str], k: int) -> float:
    """Calculates Normalized Discounted Cumulative Gain (NDCG@K)."""
    dcg = 0.0
    for rank, is_num in enumerate(retrieved_items[:k], start=1):
        rel = 1.0 if is_num in relevant_set else 0.0
        dcg += rel / math.log2(rank + 1)

    ideal_rel = min(len(relevant_set), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_rel + 1))
    return dcg / idcg if idcg > 0 else 0.0


def run_evaluation():
    service_instance.initialize()
    k_val = 3

    print("\n=======================================================")
    print("PHASE 4C — RETRIEVAL & RERANKING EVALUATION BENCHMARK")
    print("Corpus: 14 DEMO / SAMPLE Indian Standards")
    print(f"Embedding Model: {service_instance.embedding_engine.active_model_name}")
    print(f"Reranker Model: {service_instance.reranker.model_name}")
    print("=======================================================\n")

    # 1. Baseline Evaluation (Hybrid Retrieval only)
    baseline_recalls, baseline_precisions, baseline_mrrs, baseline_ndcgs = [], [], [], []
    # Temporarily disable reranker for baseline
    service_instance.reranker.is_available = False

    for item in EVAL_DATASET:
        q = item["query"]
        rel_set = item["relevant_is"]
        resp = service_instance.recommend(RecommendationRequest(query=q, top_k=k_val))
        retrieved_is = [r.is_number for r in resp.recommendations]

        hits = len(set(retrieved_is) & rel_set)
        rec = hits / len(rel_set) if rel_set else 0.0
        prec = hits / k_val
        mrr = calculate_mrr(retrieved_is, rel_set)
        ndcg = calculate_ndcg(retrieved_is, rel_set, k_val)

        baseline_recalls.append(rec)
        baseline_precisions.append(prec)
        baseline_mrrs.append(mrr)
        baseline_ndcgs.append(ndcg)

    # 2. Reranked Evaluation (Hybrid + Cross-Encoder Reranker)
    service_instance.reranker.is_available = True
    reranked_recalls, reranked_precisions, reranked_mrrs, reranked_ndcgs = [], [], [], []

    print(f"{'Query Type':<22} | {'Top Baseline IS':<24} | {'Top Reranked IS':<24} | {'Baseline Score':<14} | {'Final Score':<11}")
    print("-" * 105)

    for item in EVAL_DATASET:
        q = item["query"]
        rel_set = item["relevant_is"]
        resp = service_instance.recommend(RecommendationRequest(query=q, top_k=k_val))
        retrieved_is = [r.is_number for r in resp.recommendations]

        hits = len(set(retrieved_is) & rel_set)
        rec = hits / len(rel_set) if rel_set else 0.0
        prec = hits / k_val
        mrr = calculate_mrr(retrieved_is, rel_set)
        ndcg = calculate_ndcg(retrieved_is, rel_set, k_val)

        reranked_recalls.append(rec)
        reranked_precisions.append(prec)
        reranked_mrrs.append(mrr)
        reranked_ndcgs.append(ndcg)

        top_r = resp.recommendations[0] if resp.recommendations else None
        top_is = top_r.is_number[:22] if top_r else "N/A"
        hyb_sc = f"{top_r.hybrid_score:.4f}" if top_r and top_r.hybrid_score else "N/A"
        fin_sc = f"{top_r.relevance_score:.4f}" if top_r else "N/A"

        print(f"{item['type']:<22} | {top_is:<24} | {top_is:<24} | {hyb_sc:<14} | {fin_sc:<11}")

    print("\n" + "=" * 65)
    print("AGGREGATE RETRIEVAL METRICS SUMMARY (K=3)")
    print("=" * 65)
    print(f"Metric       | Baseline Hybrid | Hybrid + Cross-Encoder | Change")
    print("-" * 65)
    
    b_rec = sum(baseline_recalls) / len(baseline_recalls)
    r_rec = sum(reranked_recalls) / len(reranked_recalls)
    print(f"Recall@3     | {b_rec:.4f}          | {r_rec:.4f}                 | {r_rec - b_rec:+.4f}")

    b_prec = sum(baseline_precisions) / len(baseline_precisions)
    r_prec = sum(reranked_precisions) / len(reranked_precisions)
    print(f"Precision@3  | {b_prec:.4f}          | {r_prec:.4f}                 | {r_prec - b_prec:+.4f}")

    b_mrr = sum(baseline_mrrs) / len(baseline_mrrs)
    r_mrr = sum(reranked_mrrs) / len(reranked_mrrs)
    print(f"MRR          | {b_mrr:.4f}          | {r_mrr:.4f}                 | {r_mrr - b_mrr:+.4f}")

    b_ndcg = sum(baseline_ndcgs) / len(baseline_ndcgs)
    r_ndcg = sum(reranked_ndcgs) / len(reranked_ndcgs)
    print(f"NDCG@3       | {b_ndcg:.4f}          | {r_ndcg:.4f}                 | {r_ndcg - b_ndcg:+.4f}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_evaluation()
