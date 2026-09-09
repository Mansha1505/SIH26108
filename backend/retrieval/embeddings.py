import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

try:
    import torch
    torch.set_num_threads(1)
except Exception:
    pass


import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from backend.config import DEFAULT_EMBEDDING_MODEL, MULTILINGUAL_FALLBACK_MODELS
from backend.retrieval.text_prep import prepare_document_text, normalize_text
from backend.utils.logger import get_logger


logger = get_logger("EmbeddingEngine")


class SemanticEmbeddingEngine:
    """
    Multilingual Semantic Embedding Retrieval Engine using Sentence Transformers.
    Computes vector embeddings for standard documents and query vector cosine similarities.
    Supports configurable models (e.g. BAAI/bge-m3, paraphrase-multilingual-MiniLM-L12-v2),
    dynamic vector dimensionality detection, and graceful fallbacks.
    """
    def __init__(self, standards: List[Dict[str, Any]], model_name: Optional[str] = None):
        self.standards = standards
        self.model_name = model_name or DEFAULT_EMBEDDING_MODEL
        self.model = None
        self.doc_embeddings = None
        self.vector_dimension: int = 0
        self.active_model_name: str = self.model_name
        self.is_fallback: bool = False
        self._init_embeddings()

    def _init_embeddings(self):
        """Initializes dense sentence transformer embeddings with multi-tier fallback strategy."""
        from sentence_transformers import SentenceTransformer

        candidates = [self.model_name]
        for fallback in MULTILINGUAL_FALLBACK_MODELS:
            if fallback not in candidates:
                candidates.append(fallback)

        loaded_success = False

        for candidate in candidates:
            try:
                logger.info(f"Attempting to load SentenceTransformer embedding model: '{candidate}'...")
                model = SentenceTransformer(candidate)
                
                doc_texts = [prepare_document_text(std) for std in self.standards]
                logger.info(f"Encoding {len(doc_texts)} standard documents into dense embeddings with '{candidate}'...")
                embeddings = model.encode(doc_texts, show_progress_bar=False, convert_to_numpy=True)
                
                # Normalize doc embeddings for fast cosine similarity via dot product
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                normalized_embeddings = embeddings / norms
                
                self.model = model
                self.doc_embeddings = normalized_embeddings
                self.active_model_name = candidate
                self.vector_dimension = int(normalized_embeddings.shape[1])
                self.is_fallback = (candidate != self.model_name)
                loaded_success = True
                
                logger.info(
                    f"Semantic doc embeddings initialized successfully using '{candidate}'. "
                    f"Vector Dimension={self.vector_dimension}, IsFallback={self.is_fallback}"
                )
                break
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer candidate '{candidate}': {e}")

        if not loaded_success:
            logger.warning("All SentenceTransformer models failed. Falling back to TF-IDF vector similarity.")
            self._init_tfidf_fallback()

    def _init_tfidf_fallback(self):
        """Fallback TF-IDF vector encoder if SentenceTransformers cannot be loaded."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        doc_texts = [prepare_document_text(std) for std in self.standards]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.doc_embeddings = self.vectorizer.fit_transform(doc_texts).toarray()
        self.vector_dimension = int(self.doc_embeddings.shape[1])
        self.active_model_name = "TF-IDF Fallback"
        self.is_fallback = True
        logger.info(f"Initialized TF-IDF fallback vectorizer with dimension={self.vector_dimension}.")

    def search(self, query: str) -> List[Tuple[int, float]]:
        """
        Computes cosine similarity of query embedding against document embeddings.
        Supports multilingual queries in English, Hindi (Devanagari), and Hinglish.
        Returns list of (doc_index, similarity_score) where similarity is in [0.0, 1.0].
        """
        if not query or not query.strip():
            return [(idx, 0.0) for idx in range(len(self.standards))]

        if self.model is not None and self.doc_embeddings is not None:
            query_emb = self.model.encode([query], convert_to_numpy=True)
            norm = np.linalg.norm(query_emb)
            if norm > 0:
                query_emb = query_emb / norm
            
            # Cosine similarity matrix multiplication
            sims = np.dot(self.doc_embeddings, query_emb.T).flatten()
            
            # Clip similarities to [0.0, 1.0] range
            sims = np.clip(sims, 0.0, 1.0)
            return [(idx, float(sims[idx])) for idx in range(len(self.standards))]
        elif hasattr(self, "vectorizer") and self.doc_embeddings is not None:
            query_vec = self.vectorizer.transform([query]).toarray()
            q_norm = np.linalg.norm(query_vec)
            if q_norm > 0:
                query_vec = query_vec / q_norm
            d_norms = np.linalg.norm(self.doc_embeddings, axis=1)
            d_norms[d_norms == 0] = 1.0
            sims = np.dot(self.doc_embeddings, query_vec.T).flatten() / d_norms
            sims = np.clip(sims, 0.0, 1.0)
            return [(idx, float(sims[idx])) for idx in range(len(self.standards))]
        else:
            return [(idx, 0.0) for idx in range(len(self.standards))]


def get_default_embedding_engine(
    standards: List[Dict[str, Any]],
    vector_backend: Optional[str] = None,
    model_name: Optional[str] = None
):
    """
    Factory function returning the active dense vector search engine based on configuration or explicit override.

    Defaults to SemanticEmbeddingEngine (FAISS / in-memory cosine similarity baseline).
    If VECTOR_BACKEND="pgvector" or explicit override is passed, returns PgVectorSearchEngine.
    """
    from backend.config import VECTOR_BACKEND
    target_backend = vector_backend or os.getenv("VECTOR_BACKEND", VECTOR_BACKEND)
    target_backend = str(target_backend).strip().lower()

    if target_backend == "pgvector":
        from backend.retrieval.pgvector_search import PgVectorSearchEngine
        logger.info("Initializing PgVectorSearchEngine for dense retrieval...")
        return PgVectorSearchEngine(standards, model_name=model_name)
    else:
        logger.info("Initializing SemanticEmbeddingEngine (FAISS baseline) for dense retrieval...")
        return SemanticEmbeddingEngine(standards, model_name=model_name)

