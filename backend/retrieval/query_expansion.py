"""
Deterministic Hindi Procurement Query Expansion Layer.
Provides lightweight, zero-ML keyword expansion for Devanagari/Hindi procurement terms
to ensure high BM25 keyword recall when matching against English Indian Standard records.
"""

from typing import Dict, List
import re

PROCUREMENT_HINDI_DICTIONARY: Dict[str, List[str]] = {
    "कृषि": ["agriculture", "agricultural", "farming"],
    "खेती": ["agriculture", "agricultural", "farming"],
    "पानी": ["water"],
    "जल": ["water"],
    "पंप": ["pump", "pumpset"],
    "पम्प": ["pump", "pumpset"],
    "सबमर्सिबल": ["submersible"],
    "मोटर": ["motor"],
    "सड़क": ["road"],
    "सड़क": ["road"],
    "रोशनी": ["light", "lighting"],
    "प्रकाश": ["light", "lighting"],
    "सीमेंट": ["cement"],
    "संरचनात्मक": ["structural"],
    "स्लैग": ["slag"],
    "पोर्टलैंड": ["portland"],
    "ट्रांसफॉर्मर": ["transformer"],
    "ट्रांसफार्मर": ["transformer"],
    "एलईडी": ["LED", "led"],
    "स्ट्रीट": ["street"],
    "लाइट": ["light", "lighting"],
    "बिजली": ["electrical", "electricity"],
    "केबल": ["cable"],
    "पाइप": ["pipe"],
    "अग्नि": ["fire"],
    "सुरक्षा": ["safety"],
}


def expand_procurement_query(query: str) -> str:
    """
    Expands Devanagari/Hindi procurement terms in the query with their corresponding
    English domain keywords. Preserves the original query text.
    
    Example:
        Input: "कृषि के लिए सबमर्सिबल पानी का पंप"
        Output: "कृषि के लिए सबमर्सिबल पानी का पंप agriculture agricultural farming submersible water pump pumpset"
    """
    if not query or not query.strip():
        return query

    original_query = query.strip()
    expanded_terms: List[str] = []

    for term, english_kws in PROCUREMENT_HINDI_DICTIONARY.items():
        if term in original_query:
            for kw in english_kws:
                if kw not in expanded_terms:
                    expanded_terms.append(kw)

    if not expanded_terms:
        return original_query

    return f"{original_query} {' '.join(expanded_terms)}"
