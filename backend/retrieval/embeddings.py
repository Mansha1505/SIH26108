import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import json
import time
import urllib.request
import urllib.error
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from backend.config import DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMENSION, MULTILINGUAL_FALLBACK_MODELS
from backend.retrieval.text_prep import prepare_document_text, normalize_text
from backend.utils.logger import get_logger


logger = get_logger("EmbeddingEngine")


class HFInferenceQueryEncoder:
    """
    Hugging Face Free Inference API query encoder for intfloat/multilingual-e5-small.
    Encodes query text into a 384-dimensional normalized vector via HTTP POST request.
    Does NOT import PyTorch, SentenceTransformers, Transformers, or ONNX Runtime.
    Uses active Hugging Face Router domain (router.huggingface.co).
    """
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small"):
        self.model_name = model_name
        self.hf_token = os.getenv("HF_TOKEN", "").strip()
        
        # Primary & fallback Hugging Face Router endpoints (router.huggingface.co is active; api-inference.huggingface.co is deprecated/unresolvable)
        env_url = os.getenv("HF_EMBEDDING_API_URL", "").strip()
        self.api_urls = []
        if env_url:
            self.api_urls.append(env_url)
        
        default_urls = [
            f"https://router.huggingface.co/hf-inference/models/{model_name}",
            f"https://router.huggingface.co/pipeline/feature-extraction/{model_name}",
            f"https://router.huggingface.co/models/{model_name}",
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model_name}"
        ]
        for u in default_urls:
            if u not in self.api_urls:
                self.api_urls.append(u)

        self._is_e5 = "e5" in model_name.lower()

    def encode_query(self, query_text: str, timeout: float = 5.0) -> np.ndarray:
        """
        Encodes query text into a 384-d normalized float32 array.
        Prefixes E5 queries with 'query: '.
        Raises RuntimeError on API failure, timeout, status error, or invalid payload.
        Never logs sensitive auth tokens.
        """
        if not query_text or not query_text.strip():
            return np.zeros(384, dtype=np.float32)

        q_str = f"query: {query_text.strip()}" if self._is_e5 else query_text.strip()
        payload_bytes = json.dumps({
            "inputs": q_str,
            "options": {"wait_for_model": True}
        }).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SIH26108-Standards-Engine/1.0"
        }
        if self.hf_token:
            headers["Authorization"] = f"Bearer {self.hf_token}"

        last_error = None
        has_token = bool(self.hf_token)
        
        for url in self.api_urls:
            host = url.split("/")[2] if "//" in url else url
            try:
                req = urllib.request.Request(url, data=payload_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status != 200:
                        logger.warning(f"HF API host '{host}' returned non-200 status {resp.status} (auth_present={has_token})")
                        raise urllib.error.HTTPError(url, resp.status, f"HTTP {resp.status}", resp.headers, None)

                    body_bytes = resp.read()
                    data = json.loads(body_bytes.decode("utf-8"))
                    
                    vec = None
                    if isinstance(data, list):
                        arr = np.array(data, dtype=np.float32)
                        if arr.ndim == 1:
                            vec = arr
                        elif arr.ndim == 2:
                            vec = arr[0]
                        elif arr.ndim == 3:
                            vec = np.mean(arr[0], axis=0)

                    if vec is None or len(vec) != 384:
                        shape_desc = arr.shape if 'arr' in locals() and vec is not None else type(data)
                        err_msg = f"Malformed HF response from '{host}': expected length 384, got {shape_desc}"
                        logger.warning(err_msg)
                        raise ValueError(err_msg)

                    vec = vec.astype(np.float32)
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm
                    logger.info(f"Successfully retrieved 384-d vector from HF API host '{host}' (auth_present={has_token}).")
                    return vec

            except urllib.error.HTTPError as he:
                last_error = f"HTTP {he.code} from '{host}'"
                logger.warning(f"HF API request to '{host}' failed: HTTP {he.code} (auth_present={has_token})")
                continue
            except urllib.error.URLError as ue:
                reason = getattr(ue, 'reason', str(ue))
                last_error = f"URLError from '{host}': {reason}"
                logger.warning(f"HF API request to '{host}' failed (DNS/network issue): {reason}")
                continue
            except Exception as e:
                last_error = f"{type(e).__name__} from '{host}': {e}"
                logger.warning(f"HF API request to '{host}' failed: {e}")
                continue

        raise RuntimeError(f"Hugging Face Inference API query encoding failed across endpoints: {last_error}")


class ONNXQueryEncoder:
    """
    Legacy/Offline ONNX Runtime query encoder for local testing.
    Loaded lazily only if onnxruntime is installed.
    """
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small"):
        self.model_name = model_name
        self.tokenizer = None
        self.session = None
        self._is_e5 = "e5" in model_name.lower()
        self._init_model()

    def _init_model(self):
        try:
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
            import onnxruntime as ort

            repo_id = "xenova/multilingual-e5-small"
            tokenizer_path = hf_hub_download(repo_id=repo_id, filename="tokenizer.json")

            try:
                model_path = hf_hub_download(repo_id=repo_id, filename="onnx/model_quantized.onnx")
            except Exception:
                model_path = hf_hub_download(repo_id=repo_id, filename="onnx/model.onnx")

            self.tokenizer = Tokenizer.from_file(tokenizer_path)
            opts = ort.SessionOptions()
            opts.intra_op_num_threads = 1
            opts.inter_op_num_threads = 1
            self.session = ort.InferenceSession(model_path, sess_options=opts, providers=["CPUExecutionProvider"])
            logger.info(f"Successfully initialized ONNXQueryEncoder for '{self.model_name}'.")
        except Exception as e:
            logger.error(f"Failed to initialize ONNXQueryEncoder for '{self.model_name}': {e}")
            raise RuntimeError(f"ONNX query engine initialization failed: {e}") from e

    def encode_query(self, query_text: str) -> np.ndarray:
        q_str = f"query: {query_text}" if self._is_e5 else query_text
        encoded = self.tokenizer.encode(q_str)
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)

        inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
        session_inputs = [i.name for i in self.session.get_inputs()]
        if "token_type_ids" in session_inputs:
            inputs["token_type_ids"] = np.array([encoded.type_ids], dtype=np.float64)

        outputs = self.session.run(None, inputs)
        last_hidden_state = outputs[0]

        mask_expanded = np.expand_dims(attention_mask, axis=-1)
        sum_embeddings = np.sum(last_hidden_state * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        vec = (sum_embeddings / sum_mask).astype(np.float32)
        norm = np.linalg.norm(vec, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        return (vec / norm).flatten()


class SemanticEmbeddingEngine:
    """
    Multilingual Semantic Embedding Retrieval Engine.
    Uses precomputed document embeddings (backend/data/doc_embeddings_e5_small.npy)
    and queries Hugging Face Free Inference API for query vector encoding.
    Falls back cleanly to BM25 keyword matching when HF API is unavailable, setting semantic_status="fallback_bm25".
    """
    def __init__(self, standards: List[Dict[str, Any]], model_name: Optional[str] = None):
        self.standards = standards
        self.model_name = model_name or DEFAULT_EMBEDDING_MODEL
        self._doc_embeddings: Optional[np.ndarray] = None
        self._hf_encoder: Optional[HFInferenceQueryEncoder] = None
        self._onnx_encoder: Optional[ONNXQueryEncoder] = None
        self._model = None
        self.vector_dimension: int = DEFAULT_EMBEDDING_DIMENSION
        self.active_model_name: str = self.model_name
        self.is_fallback: bool = False
        self.semantic_status: str = "hf_e5_small"
        self._is_initialized: bool = False
        self.use_onnx: bool = os.getenv("USE_ONNX", "").lower() in ("true", "1", "yes")

    @property
    def model(self):
        return self._hf_encoder or self._onnx_encoder or self._model

    @property
    def doc_embeddings(self):
        if not self._is_initialized:
            self.ensure_initialized()
        return self._doc_embeddings

    @doc_embeddings.setter
    def doc_embeddings(self, value):
        self._doc_embeddings = value

    def ensure_initialized(self):
        if self._is_initialized:
            return
        self._init_embeddings()
        if self._doc_embeddings is None and self.standards:
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                doc_texts = [prepare_document_text(std) for std in self.standards]
                vectorizer = TfidfVectorizer(ngram_range=(1, 2))
                raw_matrix = vectorizer.fit_transform(doc_texts).toarray().astype(np.float32)
                N, D = raw_matrix.shape
                padded = np.zeros((N, self.vector_dimension), dtype=np.float32)
                cols = min(D, self.vector_dimension)
                padded[:, :cols] = raw_matrix[:, :cols]
                norms = np.linalg.norm(padded, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self._doc_embeddings = (padded / norms).astype(np.float32)
            except Exception:
                N = len(self.standards)
                vecs = np.ones((N, self.vector_dimension), dtype=np.float32)
                norms = np.linalg.norm(vecs, axis=1, keepdims=True)
                self._doc_embeddings = (vecs / norms).astype(np.float32)
        self._is_initialized = True

    def _load_precomputed_embeddings(self) -> bool:
        artifact_filename = "doc_embeddings_e5_small.npy" if "e5" in self.active_model_name.lower() else "doc_embeddings_l12.npy"
        artifact_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", artifact_filename))

        if os.path.exists(artifact_path):
            try:
                embeddings = np.load(artifact_path)
                if embeddings.shape[0] == len(self.standards):
                    self._doc_embeddings = embeddings.astype(np.float32)
                    self.vector_dimension = int(embeddings.shape[1])
                    logger.info(f"Loaded precomputed document embeddings from {artifact_path} (shape={embeddings.shape}).")
                    return True
                else:
                    logger.warning(f"Precomputed artifact count mismatch ({embeddings.shape[0]} vs {len(self.standards)}).")
            except Exception as e:
                logger.warning(f"Failed to load precomputed embeddings from {artifact_path}: {e}")
        return False

    def _init_embeddings(self):
        precomputed = self._load_precomputed_embeddings()

        # Primary Production Path: Hugging Face Free Inference API
        if not self.use_onnx:
            self._hf_encoder = HFInferenceQueryEncoder(model_name=self.model_name)
            self.active_model_name = self.model_name
            self.vector_dimension = 384
            self.semantic_status = "hf_e5_small"
            self._is_initialized = True
            logger.info(f"Initialized HFInferenceQueryEncoder for '{self.model_name}'. Precomputed doc vectors ready={precomputed}.")
            return

        # Legacy / Constrained ONNX path (if USE_ONNX=true explicitly requested)
        if self.use_onnx:
            try:
                self._onnx_encoder = ONNXQueryEncoder(self.model_name)
                self.active_model_name = self.model_name
                self.vector_dimension = 384
                self.semantic_status = "onnx_e5_small"
                self._is_initialized = True
                return
            except Exception as e:
                logger.error(f"Explicit failure initializing ONNX engine: {e}")
                raise RuntimeError(f"ONNX initialization failed: {e}") from e

    def search(self, query: str) -> List[Tuple[int, float]]:
        """
        Computes cosine similarity of query vector against precomputed document embeddings.
        Uses Hugging Face Free Inference API by default.
        Falls back seamlessly to BM25 (semantic score = 0.0, status = 'fallback_bm25') on any API failure.
        """
        if not query or not query.strip():
            return [(idx, 0.0) for idx in range(len(self.standards))]

        self.ensure_initialized()

        if self._doc_embeddings is None:
            logger.warning("Precomputed document embeddings missing. Falling back to BM25 keyword matching.")
            self.semantic_status = "fallback_bm25"
            return [(idx, 0.0) for idx in range(len(self.standards))]

        # If ONNX explicitly enabled
        if self._onnx_encoder is not None:
            try:
                query_vec = self._onnx_encoder.encode_query(query)
                sims = np.dot(self._doc_embeddings, query_vec).flatten()
                sims = np.clip(sims, 0.0, 1.0)
                self.semantic_status = "onnx_e5_small"
                return [(idx, float(sims[idx])) for idx in range(len(self.standards))]
            except Exception as e:
                logger.warning(f"ONNX encoding failed ({e}). Falling back to BM25.")
                self.semantic_status = "fallback_bm25"
                return [(idx, 0.0) for idx in range(len(self.standards))]

        # Default Production HF Inference API path
        if self._hf_encoder is not None:
            try:
                query_vec = self._hf_encoder.encode_query(query)
                sims = np.dot(self._doc_embeddings, query_vec).flatten()
                sims = np.clip(sims, 0.0, 1.0)
                self.semantic_status = "hf_e5_small"
                return [(idx, float(sims[idx])) for idx in range(len(self.standards))]
            except Exception as e:
                logger.warning(f"Hugging Face Inference API encoding failed/offline: {e}. Falling back to BM25.")
                self.semantic_status = "fallback_bm25"
                return [(idx, 0.0) for idx in range(len(self.standards))]

        self.semantic_status = "fallback_bm25"
        return [(idx, 0.0) for idx in range(len(self.standards))]


def get_default_embedding_engine(
    standards: List[Dict[str, Any]],
    vector_backend: Optional[str] = None,
    model_name: Optional[str] = None
):
    from backend.config import VECTOR_BACKEND
    target_backend = vector_backend or os.getenv("VECTOR_BACKEND", VECTOR_BACKEND)
    target_backend = str(target_backend).strip().lower()

    if target_backend == "pgvector":
        from backend.retrieval.pgvector_search import PgVectorSearchEngine
        logger.info("Initializing PgVectorSearchEngine for dense retrieval...")
        return PgVectorSearchEngine(standards, model_name=model_name)
    else:
        logger.info("Initializing SemanticEmbeddingEngine (HF Inference API / precomputed doc vectors)...")
        return SemanticEmbeddingEngine(standards, model_name=model_name)
