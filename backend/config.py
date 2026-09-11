import os

# Centralized Configuration for SIH26108 Standards Recommendation Engine

# -------------------------------------------------------------
# DENSE EMBEDDING RETRIEVAL CONFIGURATION (Phase 4B)
# -------------------------------------------------------------
# Default Production Model: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions, 50+ languages, fast & lightweight)
# Primary Heavy Multilingual Candidate: BAAI/bge-m3 (1024 dimensions, 100+ languages)
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
DEFAULT_EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))

MULTILINGUAL_FALLBACK_MODELS = [
    "intfloat/multilingual-e5-small",
    "paraphrase-multilingual-MiniLM-L12-v2",
    "all-MiniLM-L6-v2",
    "BAAI/bge-m3"
]


# -------------------------------------------------------------
# SECOND-STAGE CROSS-ENCODER RERANKING CONFIGURATION (Phase 4C)
# -------------------------------------------------------------
# Configurable Cross-Encoder model name (default lightweight: cross-encoder/ms-marco-MiniLM-L-6-v2)
# Configurable candidate pool size N to rerank (default: 10 candidates)
# Configurable reranking feature flag (default: True)
# Configurable score fusion weight beta (default: 0.5 - 50% CrossEncoder + 50% Hybrid)
DEFAULT_CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANK_CANDIDATE_COUNT = int(os.getenv("RERANK_CANDIDATE_COUNT", "10"))
RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() in ("true", "1", "yes")
RERANK_WEIGHT_BETA = float(os.getenv("RERANK_WEIGHT_BETA", "0.5"))

# -------------------------------------------------------------
# POSTGRESQL DATABASE CONFIGURATION (Phase 10A)
# -------------------------------------------------------------
# Default database connection string (environment-driven, fallback for local development)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/sih26108_standards")

# Database connection pool settings
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "30.0"))
DB_ECHO = os.getenv("DB_ECHO", "false").lower() in ("true", "1", "yes")
DB_AUTO_CREATE_TABLES = os.getenv("DB_AUTO_CREATE_TABLES", "false").lower() in ("true", "1", "yes")

# Repository selection flag ("json" or "postgres", defaults to "json" baseline)
REPOSITORY_TYPE = os.getenv("REPOSITORY_TYPE", "json").lower()

# Vector store selection flag ("faiss" or "pgvector", defaults to "faiss" baseline - Phase 10B)
VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "faiss").lower()


