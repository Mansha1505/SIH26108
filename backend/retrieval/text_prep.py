import re
from typing import List, Dict, Any

# Common english stopwords to exclude from BM25 indexing
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
    "should", "now", "use", "used", "using", "for", "per"
}

def normalize_text(text: str) -> str:
    """Lowercases text and strips non-alphanumeric characters except spaces and hyphen."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize_text(text: str) -> List[str]:
    """Tokenizes normalized text into words, removing short stopwords."""
    normalized = normalize_text(text)
    tokens = normalized.split()
    cleaned = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    return cleaned

def prepare_document_text(standard: Dict[str, Any]) -> str:
    """
    Concatenates fields of a standard into a unified text representation for retrieval.
    Fields weighted implicitly by repetition if needed.
    """
    is_num = standard.get("is_number", "")
    title = standard.get("title", "")
    category = standard.get("product_category", "")
    sector = standard.get("sector", "")
    keywords = " ".join(standard.get("keywords", []))
    scope = standard.get("scope", "")

    # Combine all metadata fields
    full_text = f"{is_num} {title} {category} {sector} {keywords} {scope}"
    return full_text
