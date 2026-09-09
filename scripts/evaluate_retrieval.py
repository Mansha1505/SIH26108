"""
Final Evaluation & Benchmarking Runner for SIH26108 Standards Recommendation Engine (Phase 10E).

Evaluates BM25, Multilingual Dense (FAISS), Hybrid BM25+Dense, and Hybrid + Cross-Encoder Reranking
against the 20-query gold evaluation dataset across English, Hindi, and Hinglish.
Optionally benchmarks pgvector dense retrieval against FAISS when live PostgreSQL is available.
Generates scripts/final_evaluation_results.json and scripts/FINAL_EVALUATION_REPORT.md.
"""

import sys
import os
import json
import datetime
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath("."))

from backend.services.recommendation_service import service_instance
from backend.models.schemas import RecommendationRequest
from scripts.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    mrr_at_k,
    ndcg_at_k
)
from backend.config import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_DIMENSION,
    REPOSITORY_TYPE,
    VECTOR_BACKEND
)

DATASET_PATH = os.path.join(os.path.dirname(__file__), "evaluation_dataset.json")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
FINAL_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "final_evaluation_results.json")
FINAL_REPORT_PATH = os.path.join(os.path.dirname(__file__), "FINAL_EVALUATION_REPORT.md")


def run_system_bm25(query: str, top_k: int = 14) -> List[str]:
    """System A: BM25 Lexical Keyword Retrieval Only."""
    raw_results = service_instance.bm25_engine.search(query)
    sorted_results = sorted(raw_results, key=lambda x: x[1], reverse=True)[:top_k]
    return [service_instance.standards[idx]["id"] for idx, _ in sorted_results]


def run_system_dense(query: str, top_k: int = 14) -> List[str]:
    """System B: Multilingual Dense Vector Embedding Retrieval (FAISS Baseline)."""
    raw_results = service_instance.embedding_engine.search(query)
    sorted_results = sorted(raw_results, key=lambda x: x[1], reverse=True)[:top_k]
    return [service_instance.standards[idx]["id"] for idx, _ in sorted_results]


def run_system_hybrid(query: str, top_k: int = 14) -> List[str]:
    """System C: First-Stage Hybrid BM25 + Multilingual Dense Retrieval."""
    candidate_scores = service_instance.hybrid_retriever.get_candidate_scores(query)
    sorted_candidates = sorted(candidate_scores, key=lambda x: x["relevance_score"], reverse=True)[:top_k]
    return [service_instance.standards[c["doc_index"]]["id"] for c in sorted_candidates]


def run_system_hybrid_reranker(query: str, top_k: int = 14) -> List[str]:
    """System D: First-Stage Hybrid + Second-Stage Cross-Encoder Reranking."""
    resp = service_instance.recommend(RecommendationRequest(query=query, top_k=top_k))
    return [rec.id for rec in resp.recommendations]


def run_pgvector_benchmark_if_available(gold_dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Optional live pgvector benchmark comparing PostgreSQL vector search against FAISS dense retrieval.
    Skips cleanly if PostgreSQL is unreachable or standard_embeddings table is empty.
    """
    try:
        from backend.database.connection import get_db_engine, check_database_connection
        from backend.database.vector import check_pgvector_extension
        from backend.retrieval.pgvector_search import PgVectorSearchEngine

        engine = get_db_engine()
        if not check_database_connection(engine):
            return {
                "status": "SKIPPED",
                "reason": "PostgreSQL database server is not reachable.",
                "live_postgres_verified": False
            }

        if not check_pgvector_extension(engine):
            return {
                "status": "SKIPPED",
                "reason": "pgvector extension is not installed on PostgreSQL server.",
                "live_postgres_verified": False
            }

        pg_search_engine = PgVectorSearchEngine(embedding_engine=service_instance.embedding_engine)

        pg_results = []
        top1_matches = 0
        total_overlap_ratio = 0.0

        for item in gold_dataset:
            query_text = item["query"]
            faiss_retrieved = run_system_dense(query_text, top_k=5)
            
            try:
                pg_retrieved_items = pg_search_engine.search(query_text, top_k=5)
                pg_retrieved = [rec["id"] for rec in pg_retrieved_items]
            except Exception as e:
                return {
                    "status": "SKIPPED",
                    "reason": f"pgvector query execution error: {e}",
                    "live_postgres_verified": False
                }

            if faiss_retrieved and pg_retrieved and faiss_retrieved[0] == pg_retrieved[0]:
                top1_matches += 1

            set_faiss = set(faiss_retrieved)
            set_pg = set(pg_retrieved)
            union_len = len(set_faiss | set_pg)
            overlap = len(set_faiss & set_pg) / union_len if union_len > 0 else 0.0
            total_overlap_ratio += overlap

            pg_results.append({
                "id": item["id"],
                "faiss_top5": faiss_retrieved,
                "pgvector_top5": pg_retrieved,
                "top1_match": (faiss_retrieved[0] == pg_retrieved[0]) if (faiss_retrieved and pg_retrieved) else False,
                "overlap_ratio": round(overlap, 4)
            })

        num_queries = len(gold_dataset)
        top1_agreement_pct = round((top1_matches / num_queries) * 100.0, 2)
        avg_overlap_pct = round((total_overlap_ratio / num_queries) * 100.0, 2)

        return {
            "status": "COMPLETED",
            "live_postgres_verified": True,
            "queries_evaluated": num_queries,
            "top1_agreement_pct": top1_agreement_pct,
            "avg_top5_overlap_pct": avg_overlap_pct,
            "query_details": pg_results
        }
    except Exception as e:
        return {
            "status": "SKIPPED",
            "reason": f"PostgreSQL/pgvector test environment exception: {e}",
            "live_postgres_verified": False
        }


def aggregate_system_metrics(system_name: str, per_query_records: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculates aggregate mean metrics across queries for a specific retrieval system."""
    sys_records = [r["systems"][system_name] for r in per_query_records]
    num_queries = len(sys_records)

    return {
        "p_1": round(sum(r["p_1"] for r in sys_records) / num_queries, 4),
        "p_3": round(sum(r["p_3"] for r in sys_records) / num_queries, 4),
        "p_5": round(sum(r["p_5"] for r in sys_records) / num_queries, 4),
        "r_1": round(sum(r["r_1"] for r in sys_records) / num_queries, 4),
        "r_3": round(sum(r["r_3"] for r in sys_records) / num_queries, 4),
        "r_5": round(sum(r["r_5"] for r in sys_records) / num_queries, 4),
        "mrr": round(sum(r["mrr"] for r in sys_records) / num_queries, 4),
        "ndcg_3": round(sum(r["ndcg_3"] for r in sys_records) / num_queries, 4),
        "ndcg_5": round(sum(r["ndcg_5"] for r in sys_records) / num_queries, 4),
    }


def generate_markdown_report(
    eval_payload: Dict[str, Any],
    pgvector_eval: Dict[str, Any]
) -> str:
    """Generates a human-readable markdown evaluation report."""
    agg = eval_payload["aggregate_metrics"]
    lang_map = eval_payload["language_metrics"]

    md = []
    md.append("# SIH26108 Final Retrieval Evaluation & Benchmark Report (Phase 10E)\n")
    md.append("**Timestamp:** `" + eval_payload["timestamp"] + "`  ")
    md.append("**Active Vector Backend:** `" + VECTOR_BACKEND + "`  ")
    md.append("**Active Repository:** `" + REPOSITORY_TYPE + "`  ")
    md.append("**Dense Embedding Model:** `" + eval_payload["environment"]["embedding_model"] + "` (" + str(eval_payload["environment"]["embedding_dimension"]) + " dimensions)  ")
    md.append("**Cross-Encoder Reranker:** `" + str(eval_payload["environment"]["reranker_model"]) + "` (Active=" + str(eval_payload["environment"]["reranker_enabled"]) + ")\n")

    md.append("---\n")
    md.append("## 1. Methodology & Dataset Overview\n")
    md.append("- **Corpus Size:** 14 Indian Standard Records (Demo Prototype Baseline)")
    md.append("- **Evaluation Dataset:** 20 Gold-Standard Procurement Queries (`scripts/evaluation_dataset.json`)")
    md.append("- **Language Distribution:** English (`en`: 11 queries), Hindi Devanagari (`hi`: 4 queries), Hinglish Transliterated (`hi-Latn`: 5 queries)")
    md.append("- **Relevance Grading:** Graded multi-level labels (0 = Irrelevant, 1 = Secondary related standard, 2 = Primary exact match)\n")

    md.append("## 2. System Metrics Benchmark Comparison\n")
    md.append("| System Architecture | Precision@1 | Precision@3 | Recall@1 | Recall@3 | Recall@5 | MRR | NDCG@3 |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    systems_display = [
        ("BM25 Keyword Only", agg["BM25"]),
        ("Dense Vector (FAISS)", agg["Dense"]),
        ("Hybrid (BM25 + Dense)", agg["Hybrid"]),
        ("Hybrid + Cross-Encoder Reranker", agg["Hybrid+Reranker"])
    ]
    for name, m in systems_display:
        md.append(f"| {name} | {m['p_1']:.4f} | {m['p_3']:.4f} | {m['r_1']:.4f} | {m['r_3']:.4f} | {m['r_5']:.4f} | {m['mrr']:.4f} | {m['ndcg_3']:.4f} |")

    md.append("\n## 3. Multilingual Performance Breakdown (Hybrid + Cross-Encoder Reranker)\n")
    md.append("| Language Code | Language Description | Query Count | Precision@1 | Precision@3 | Recall@3 | MRR | NDCG@3 |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    lang_names = {"en": "English", "hi": "Hindi (Devanagari)", "hi-Latn": "Hinglish (Latin)"}
    for l_code, m in lang_map.items():
        lname = lang_names.get(l_code, l_code)
        q_count = sum(1 for q in eval_payload["per_query_details"] if q["language"] == l_code)
        md.append(f"| `{l_code}` | {lname} | {q_count} | {m['p_1']:.4f} | {m['p_3']:.4f} | {m['r_3']:.4f} | {m['mrr']:.4f} | {m['ndcg_3']:.4f} |")

    md.append("\n## 4. pgvector vs FAISS Vector Backend Benchmark\n")
    if pgvector_eval.get("status") == "COMPLETED":
        md.append("- **Status:** Completed (Live PostgreSQL + pgvector environment verified)")
        md.append(f"- **Top-1 Agreement:** `{pgvector_eval['top1_agreement_pct']}%`")
        md.append(f"- **Average Top-5 Overlap Ratio:** `{pgvector_eval['avg_top5_overlap_pct']}%`")
    else:
        md.append(f"- **Status:** `{pgvector_eval.get('status', 'SKIPPED')}`")
        md.append(f"- **Reason:** {pgvector_eval.get('reason', 'PostgreSQL database server unavailable.')}")
        md.append("- **Note:** FAISS remains the active production default (`VECTOR_BACKEND=faiss`).\n")

    md.append("## 5. System Positioning & Honest Interpretation\n")
    md.append("> [!IMPORTANT]")
    md.append("> **PROTOTYPE BOUNDARY DISCLAIMER:**")
    md.append("> Benchmark scores reported above reflect retrieval effectiveness measured against a 14-standard demo corpus using 20 gold evaluation queries.")
    md.append("> These metrics MUST NOT be interpreted as 100% legal accuracy or full coverage of the complete Bureau of Indian Standards (BIS) library.")
    md.append("> Recommendations are AI-assisted search relevance indications. Authoritative verification against official BIS publications is required for statutory compliance.\n")

    return "\n".join(md)


def main():
    # 1. Load Gold Evaluation Dataset
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        gold_dataset = json.load(f)

    # 2. Initialize Recommendation Service
    service_instance.initialize()

    print("\n=========================================================================")
    print("SIH26108 FINAL RETRIEVAL EVALUATION & BENCHMARKING FRAMEWORK (Phase 10E)")
    print("Dataset: Prototype evaluation on curated DEMO / SAMPLE corpus (14 Standards)")
    print(f"Queries Evaluated: {len(gold_dataset)}")
    print(f"Dense Embedding Model: {service_instance.embedding_engine.active_model_name} ({service_instance.embedding_engine.vector_dimension} dims)")
    print(f"Cross-Encoder Reranker: {service_instance.reranker.model_name} (Active={service_instance.reranker.is_available})")
    print("=========================================================================\n")

    per_query_results = []
    systems_map = {
        "BM25": run_system_bm25,
        "Dense": run_system_dense,
        "Hybrid": run_system_hybrid,
        "Hybrid+Reranker": run_system_hybrid_reranker
    }

    for item in gold_dataset:
        q_id = item["id"]
        query_text = item["query"]
        lang = item["language"]
        domain = item["domain"]
        relevance_map = item["relevance"]
        expected_ids = item["relevant_standard_ids"]

        query_record = {
            "id": q_id,
            "query": query_text,
            "language": lang,
            "domain": domain,
            "expected_ids": expected_ids,
            "relevance_map": relevance_map,
            "systems": {}
        }

        for sys_name, sys_func in systems_map.items():
            retrieved_ids = sys_func(query_text, top_k=14)
            p1 = precision_at_k(retrieved_ids, relevance_map, k=1)
            p3 = precision_at_k(retrieved_ids, relevance_map, k=3)
            p5 = precision_at_k(retrieved_ids, relevance_map, k=5)
            r1 = recall_at_k(retrieved_ids, relevance_map, k=1)
            r3 = recall_at_k(retrieved_ids, relevance_map, k=3)
            r5 = recall_at_k(retrieved_ids, relevance_map, k=5)
            mrr = mrr_at_k(retrieved_ids, relevance_map, k=5)
            ndcg3 = ndcg_at_k(retrieved_ids, relevance_map, k=3)
            ndcg5 = ndcg_at_k(retrieved_ids, relevance_map, k=5)

            query_record["systems"][sys_name] = {
                "retrieved_ids": retrieved_ids[:5],
                "p_1": p1,
                "p_3": p3,
                "p_5": p5,
                "r_1": r1,
                "r_3": r3,
                "r_5": r5,
                "mrr": mrr,
                "ndcg_3": ndcg3,
                "ndcg_5": ndcg5
            }

        per_query_results.append(query_record)

    # 3. Calculate Overall Aggregate Metrics
    agg_bm25 = aggregate_system_metrics("BM25", per_query_results)
    agg_dense = aggregate_system_metrics("Dense", per_query_results)
    agg_hybrid = aggregate_system_metrics("Hybrid", per_query_results)
    agg_rerank = aggregate_system_metrics("Hybrid+Reranker", per_query_results)

    # 4. Language Breakdown
    languages = sorted(list(set(q["language"] for q in gold_dataset)))
    lang_metrics_map = {}
    for lang in languages:
        lang_recs = [r for r in per_query_results if r["language"] == lang]
        agg_l = aggregate_system_metrics("Hybrid+Reranker", lang_recs)
        lang_metrics_map[lang] = agg_l

    # 5. Optional pgvector benchmark
    pgvector_eval = run_pgvector_benchmark_if_available(gold_dataset)

    # 6. Save Machine-Readable Final Results
    eval_results_payload = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "disclaimer": "Prototype evaluation on curated DEMO / SAMPLE corpus. Authoritative verification against official BIS records required.",
        "environment": {
            "repository_type": REPOSITORY_TYPE,
            "vector_backend": VECTOR_BACKEND,
            "embedding_model": service_instance.embedding_engine.active_model_name,
            "embedding_dimension": service_instance.embedding_engine.vector_dimension,
            "reranker_model": service_instance.reranker.model_name,
            "reranker_enabled": service_instance.reranker.is_available,
            "candidate_pool_size": 14
        },
        "query_count": len(gold_dataset),
        "aggregate_metrics": {
            "BM25": agg_bm25,
            "Dense": agg_dense,
            "Hybrid": agg_hybrid,
            "Hybrid+Reranker": agg_rerank
        },
        "language_metrics": lang_metrics_map,
        "pgvector_comparison": pgvector_eval,
        "per_query_details": per_query_results
    }

    with open(FINAL_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_results_payload, f, indent=2, ensure_ascii=False)

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(eval_results_payload, f, indent=2, ensure_ascii=False)

    print(f"Machine-readable evaluation results saved to: {FINAL_RESULTS_PATH}")

    # 7. Save Human-Readable Markdown Report
    markdown_report = generate_markdown_report(eval_results_payload, pgvector_eval)
    with open(FINAL_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(markdown_report)

    print(f"Human-readable evaluation report saved to: {FINAL_REPORT_PATH}\n")

    # Print summary tables to console
    print("=========================================================================")
    print("OVERALL RETRIEVAL SYSTEM METRICS COMPARISON")
    print("=========================================================================")
    print(f"{'System Architecture':<24} | {'P@1':<7} | {'P@3':<7} | {'R@1':<7} | {'R@3':<7} | {'R@5':<7} | {'MRR':<7} | {'NDCG@3':<7}")
    print("-" * 90)
    for name, agg in [("BM25 Only", agg_bm25), ("Dense Embeddings (FAISS)", agg_dense), ("Hybrid BM25+Dense", agg_hybrid), ("Hybrid+CrossEncoder", agg_rerank)]:
        print(f"{name:<24} | {agg['p_1']:<7.4f} | {agg['p_3']:<7.4f} | {agg['r_1']:<7.4f} | {agg['r_3']:<7.4f} | {agg['r_5']:<7.4f} | {agg['mrr']:<7.4f} | {agg['ndcg_3']:<7.4f}")
    print("=========================================================================\n")


if __name__ == "__main__":
    main()
