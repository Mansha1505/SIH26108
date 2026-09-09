# SIH26108 — AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications

> **Smart India Hackathon 2026 Problem Statement Solutions Prototype**

---

## 1. Project Objective
The objective of this project is to build an AI-assisted procurement standards recommendation engine. The system analyzes natural-language tender/procurement specifications (e.g. *"50W LED street light for outdoor municipal roads"*, Hindi *"100 केवीए तीन फेज वितरण ट्रांसफार्मर"*, or Hinglish *"110 mm ka HDPE water pipe"*) and identifies relevant Indian Standards (IS/BIS standards) from a local demo corpus.

**IMPORTANT DISCLAIMER:**
This is an **AI-assisted recommendation system** designed to assist procurement users in discovering potentially relevant standards. It is **NOT** a legal compliance engine. Recommendations do not constitute legal advice or guarantee statutory compliance. All dataset records are explicitly marked as **DEMO / SAMPLE DATA**.

---

## 2. System Architecture
```text
Tender PDF / User Query (React UI)
        │
        ▼ (HTTP POST /api/documents/extract & /api/recommend)
FastAPI Backend (Request Validation via Pydantic V2)
        │
        ▼ (Phase 3 Requirement Extraction)
Requirement Extraction Engine (Deterministic Regex, IS Mentions, Technical Parameters)
        │
        ▼ (Phase 4A Requirement-Aware Query Builder)
Structured Query Builder
 ┌──────┴──────────────────────────────────────┐
 ▼                                             ▼
BM25 Keyword Search (rank_bm25)               Multilingual Dense Vector Search
(Exact IS numbers, units, values)             (FAISS or PostgreSQL pgvector)
 │                                             │
 └──────────────────────┬──────────────────────┘
                        ▼ (Phase 4B Hybrid Score Fusion)
          First-Stage Candidate Pool (Top 14 Pool)
                        │
                        ▼ (Phase 4C Cross-Encoder Reranking)
       CrossEncoder Reranker (ms-marco-MiniLM-L-6-v2 deep query-candidate cross-attention)
                        │
                        ▼ (Phase 4D Evaluation Benchmark & Gating)
       Candidate Ranker & Deterministic Justification Reasons Generator
                        │
                        ▼ (Phase 5 Version & Amendment Intelligence)
       VersionAmendmentAnalyzer (Revision year, sorted amendments, status flags, BIS verification notice)
                        │
                        ▼ (Phase 6 Knowledge Graph / Standards Network)
       StandardsGraphBuilder (NetworkX DiGraph: Declared & Inferred relationships, Subgraph Traversal)
                        │
                        ▼ (Phase 7 Certification Rule Engine)
       CertificationRuleEngine (Quality Control Orders QCOs, BIS Scheme-I / CRS)
                        │
                        ▼ (Phase 8 Procurement Gap Analysis & RAG Explanations)
       GapAnalysisEngine & EvidenceBuilder
                        │
                        ▼ (Phase 10D Reports & Export Engine)
       ReportService (JSON / Publication-Quality PDF Exports via ReportLab)
                        │
                        ▼
       Ranked Top-K JSON Payload / PDF Download -> React Procurement Portal
```

---

## 3. Database & pgvector Persistence Layer (Phase 10A - 10C)

The system supports two swappable persistence & retrieval backends via a clean repository factory design pattern:

| Mode | Environment Config | Description |
| :--- | :--- | :--- |
| **Development Default** | `REPOSITORY_TYPE=json`<br/>`VECTOR_BACKEND=faiss` | Lightweight, fast local file-based repository (`standards.json`) and in-memory FAISS vector index. Requires zero external database dependencies. |
| **Production Target** | `REPOSITORY_TYPE=postgres`<br/>`VECTOR_BACKEND=pgvector` | Production relational database (`PostgreSQL 16`) storing standard ORM records (`StandardModel`) and native dense vector embeddings (`StandardEmbeddingModel`) via the PostgreSQL `pgvector` extension using cosine distance (`<->`). |

### Idempotent Database Utilities:
- **Corpus Migration CLI**: `python -m backend.database.seed` (Idempotently migrates JSON standards to PostgreSQL).
- **Embedding Population CLI**: `python -m backend.database.seed_embeddings` (Idempotently populates `standard_embeddings` table).
- **Corpus Comparison & Sync CLI**:
  - `python -m backend.database.migrate --compare` (Read-only comparison report across 13 fields + embedding staleness detection).
  - `python -m backend.database.migrate --sync` (Idempotent synchronization bringing PostgreSQL in line with JSON baseline).

---

## 4. Reports & Export Engine (Phase 10D)

The system provides publication-quality procurement report generation:
- **JSON Export Endpoint**: `POST /api/reports/export/json`
- **PDF Export Endpoint**: `POST /api/reports/export/pdf`

**PDF Features**: Rendered using ReportLab (`SimpleDocTemplate`, `Table`, `Paragraph`) featuring deep navy/teal headers, structured grid tables, wrapped text cells, and amber caution callouts. Incorporates recommendations, technical attributes, version intelligence, certification QCO rules, standards network relationships, gap analysis, and evidence provenance into a single downloadable PDF file.

---

## 5. Docker & Containerization (Phase 10F)

The project includes production-ready Docker containers and Docker Compose configuration for multi-container local execution:

### Container Structure:
1. `sih26108_postgres`: Official PostgreSQL 16 + `pgvector` image (`pgvector/pgvector:pg16`).
2. `sih26108_backend`: FastAPI backend running on Python 3.11-slim, listening on `0.0.0.0:$PORT` via Uvicorn.
3. `sih26108_frontend`: Production multi-stage Nginx container serving compiled Vite static assets on port `80`.

### Local Execution Command:
```bash
docker compose up --build
```

---

## 6. Environment Configuration (`.env.example`)

Copy `.env.example` to `.env` to configure application runtime variables:

```ini
# Repository and Vector Store Selection
REPOSITORY_TYPE=json
VECTOR_BACKEND=faiss

# PostgreSQL Connection String (Backend Only)
DATABASE_URL=postgresql+psycopg://postgres:postgrespassword@localhost:5432/sih26108_standards

# Model Configuration
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
CROSS_ENCODER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2

# Server Port (Render dynamically assigns $PORT)
PORT=8000

# Frontend Public API URL
VITE_API_BASE_URL=/api
```

---

## 7. Render Cloud Deployment Architecture

The system is engineered for zero-code-change Render deployment:
- **Backend Service**: Render Docker Web Service listening on `0.0.0.0:$PORT`.
- **Database Service**: Render PostgreSQL with `pgvector` extension enabled.
- **Frontend Service**: Render Static Web Service or Nginx Docker Web Service with `VITE_API_BASE_URL` pointing to the deployed backend URL.

---

## 8. Final Benchmark & Evaluation Results (Phase 10E)

Evaluated against the 20-query gold evaluation dataset (`scripts/evaluation_dataset.json`):

| System Architecture | Precision@1 | Precision@3 | Recall@1 | Recall@3 | Recall@5 | MRR | NDCG@3 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BM25 Only** | 0.8500 | 0.4167 | 0.6167 | 0.8083 | 0.8500 | 0.8500 | 0.8233 |
| **Dense Embeddings (FAISS Baseline)** | 1.0000 | 0.4833 | 0.7417 | 0.9583 | 1.0000 | 1.0000 | 0.9733 |
| **Hybrid BM25+Dense** | 1.0000 | 0.5000 | 0.7417 | 0.9833 | 1.0000 | 1.0000 | 0.9718 |
| **Hybrid + Cross-Encoder Reranker** | **1.0000** | **0.5000** | **0.7417** | **0.9833** | **1.0000** | **1.0000** | **0.9718** |

### Multilingual Breakdown:
- **English (`en`)**: P@1 = 1.0000, R@3 = 0.9697, MRR = 1.0000, NDCG@3 = 0.9669
- **Hindi (`hi`)**: P@1 = 1.0000, R@3 = 1.0000, MRR = 1.0000, NDCG@3 = 0.9754
- **Hinglish (`hi-Latn`)**: P@1 = 1.0000, R@3 = 1.0000, MRR = 1.0000, NDCG@3 = 0.9796

---

## 9. Testing & Verification

Run backend unit and integration test suite:
```bash
python -m pytest tests/
```

Run frontend production bundle build:
```bash
cd frontend && npm run build
```

Run evaluation benchmark:
```bash
python scripts/evaluate_retrieval.py
```

---

## 10. System Positioning & Honest Prototype Boundaries

1. **AI-Assisted Decision Support**: The recommendation scores, hybrid ranks, gap analysis, and explanations provide decision support for procurement personnel. They do **NOT** replace human engineering review or statutory compliance officers.
2. **Prototype Corpus Scope**: Evaluation and recommendation results operate over a curated sample corpus of Indian Standards (`standards.json`). Status of *"Not Evidenced"* means evidence was not found in this demo corpus; it does **NOT** imply that no Indian Standard exists in the complete BIS library.
3. **Official BIS Verification Required**: Version, revision, amendment, and QCO certification outputs reflect dataset records and require authoritative verification against official Bureau of Indian Standards (BIS) publications.
