import math
from typing import List, Dict, Any, Tuple
from backend.retrieval.text_prep import tokenize_text, prepare_document_text
from backend.utils.logger import get_logger

logger = get_logger("BM25Engine")

try:
    from rank_bm25 import BM25Okapi
    HAS_RANK_BM25 = True
except ImportError:
    HAS_RANK_BM25 = False
    logger.warning("rank_bm25 package not found. Using built-in lightweight BM25 implementation.")


class LightweightBM25:
    """Lightweight pure Python BM25 implementation as fallback."""
    def __init__(self, corpus_tokens: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus_tokens)
        self.avgdl = sum(len(doc) for doc in corpus_tokens) / max(self.corpus_size, 1)
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = [len(doc) for doc in corpus_tokens]
        self.corpus_tokens = corpus_tokens
        self._calc_idf()

    def _calc_idf(self):
        df_counts = {}
        for doc in self.corpus_tokens:
            for token in set(doc):
                df_counts[token] = df_counts.get(token, 0) + 1
        for token, freq in df_counts.items():
            # Standard BM25 IDF formula
            self.idf[token] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1)

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        scores = [0.0] * self.corpus_size
        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for doc_idx, doc in enumerate(self.corpus_tokens):
                freq = doc.count(token)
                if freq == 0:
                    continue
                num = freq * (self.k1 + 1)
                den = freq + self.k1 * (1 - self.b + self.b * (self.doc_len[doc_idx] / max(self.avgdl, 1)))
                scores[doc_idx] += idf_val * (num / den)
        return scores


class BM25SearchEngine:
    """
    BM25 Search Engine module for indexing standard documents and executing lexical retrieval queries.
    """
    def __init__(self, standards: List[Dict[str, Any]]):
        self.standards = standards
        self.corpus_tokens = [tokenize_text(prepare_document_text(std)) for std in standards]
        
        if HAS_RANK_BM25:
            self.bm25 = BM25Okapi(self.corpus_tokens)
        else:
            self.bm25 = LightweightBM25(self.corpus_tokens)
        
        logger.info(f"BM25 index built for {len(standards)} standards documents.")

    def search(self, query: str) -> List[Tuple[int, float]]:
        """
        Executes BM25 search for the given query string.
        Returns list of tuples (doc_index, raw_bm25_score).
        """
        query_tokens = tokenize_text(query)
        if not query_tokens:
            return [(idx, 0.0) for idx in range(len(self.standards))]

        raw_scores = self.bm25.get_scores(query_tokens)
        results = [(idx, float(score)) for idx, score in enumerate(raw_scores)]
        return results
