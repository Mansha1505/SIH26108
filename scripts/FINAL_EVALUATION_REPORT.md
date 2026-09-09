# SIH26108 Final Retrieval Evaluation & Benchmark Report (Phase 10E)

**Timestamp:** `2026-09-09T18:34:54.996151+00:00`  
**Active Vector Backend:** `faiss`  
**Active Repository:** `json`  
**Dense Embedding Model:** `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensions)  
**Cross-Encoder Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (Active=True)

---

## 1. Methodology & Dataset Overview

- **Corpus Size:** 14 Indian Standard Records (Demo Prototype Baseline)
- **Evaluation Dataset:** 20 Gold-Standard Procurement Queries (`scripts/evaluation_dataset.json`)
- **Language Distribution:** English (`en`: 11 queries), Hindi Devanagari (`hi`: 4 queries), Hinglish Transliterated (`hi-Latn`: 5 queries)
- **Relevance Grading:** Graded multi-level labels (0 = Irrelevant, 1 = Secondary related standard, 2 = Primary exact match)

## 2. System Metrics Benchmark Comparison

| System Architecture | Precision@1 | Precision@3 | Recall@1 | Recall@3 | Recall@5 | MRR | NDCG@3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BM25 Keyword Only | 0.8500 | 0.4167 | 0.6167 | 0.8083 | 0.8500 | 0.8500 | 0.8233 |
| Dense Vector (FAISS) | 1.0000 | 0.4833 | 0.7417 | 0.9583 | 1.0000 | 1.0000 | 0.9733 |
| Hybrid (BM25 + Dense) | 1.0000 | 0.5000 | 0.7417 | 0.9833 | 1.0000 | 1.0000 | 0.9718 |
| Hybrid + Cross-Encoder Reranker | 1.0000 | 0.5000 | 0.7417 | 0.9833 | 1.0000 | 1.0000 | 0.9718 |

## 3. Multilingual Performance Breakdown (Hybrid + Cross-Encoder Reranker)

| Language Code | Language Description | Query Count | Precision@1 | Precision@3 | Recall@3 | MRR | NDCG@3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `en` | English | 11 | 1.0000 | 0.4848 | 0.9697 | 1.0000 | 0.9857 |
| `hi` | Hindi (Devanagari) | 4 | 1.0000 | 0.5000 | 1.0000 | 1.0000 | 0.8984 |
| `hi-Latn` | Hinglish (Latin) | 5 | 1.0000 | 0.5333 | 1.0000 | 1.0000 | 1.0000 |

## 4. pgvector vs FAISS Vector Backend Benchmark

- **Status:** `SKIPPED`
- **Reason:** PostgreSQL/pgvector test environment exception: Database driver not installed for 'postgresql+psycopg://postgres:postgres@localhost:5432/sih26108_standards': No module named 'psycopg'
- **Note:** FAISS remains the active production default (`VECTOR_BACKEND=faiss`).

## 5. System Positioning & Honest Interpretation

> [!IMPORTANT]
> **PROTOTYPE BOUNDARY DISCLAIMER:**
> Benchmark scores reported above reflect retrieval effectiveness measured against a 14-standard demo corpus using 20 gold evaluation queries.
> These metrics MUST NOT be interpreted as 100% legal accuracy or full coverage of the complete Bureau of Indian Standards (BIS) library.
> Recommendations are AI-assisted search relevance indications. Authoritative verification against official BIS publications is required for statutory compliance.
