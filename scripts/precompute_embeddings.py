import os
import sys
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.retrieval.loader import get_default_repository
from backend.retrieval.text_prep import prepare_document_text
from backend.utils.logger import get_logger

logger = get_logger("PrecomputeEmbeddings")


def precompute_embeddings(model_name: str = "intfloat/multilingual-e5-small", output_filename: str = "doc_embeddings_e5_small.npy"):
    """
    Precomputes dense vector embeddings for all standard records in the corpus
    and saves the normalized numpy array to backend/data/<output_filename>.
    """
    from sentence_transformers import SentenceTransformer

    logger.info(f"Loading standards corpus from default repository...")
    repo = get_default_repository()
    standards = repo.get_all_standards()
    logger.info(f"Loaded {len(standards)} standards records.")

    is_e5 = "e5" in model_name.lower()
    prefix = "passage: " if is_e5 else ""
    doc_texts = [f"{prefix}{prepare_document_text(std)}" for std in standards]

    logger.info(f"Loading SentenceTransformer model '{model_name}'...")
    model = SentenceTransformer(model_name, device="cpu")

    logger.info(f"Encoding {len(doc_texts)} document texts into dense embeddings...")
    embeddings = model.encode(doc_texts, show_progress_bar=True, convert_to_numpy=True)

    # Normalize vectors
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    normalized_embeddings = (embeddings / norms).astype(np.float32)

    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "data", output_filename))
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    np.save(output_path, normalized_embeddings)

    logger.info(
        f"Successfully precomputed document embeddings! "
        f"Saved to: {output_path} (Shape: {normalized_embeddings.shape}, Size: {os.path.getsize(output_path) / 1024:.2f} KB)"
    )
    return output_path


if __name__ == "__main__":
    print("Precomputing document embeddings for intfloat/multilingual-e5-small...")
    precompute_embeddings("intfloat/multilingual-e5-small", "doc_embeddings_e5_small.npy")
    print("Precomputing document embeddings for paraphrase-multilingual-MiniLM-L12-v2...")
    precompute_embeddings("paraphrase-multilingual-MiniLM-L12-v2", "doc_embeddings_l12.npy")
    print("Precomputation complete!")
