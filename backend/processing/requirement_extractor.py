import re
from typing import List, Dict, Any, Optional, Set
from backend.models.schemas import (
    TechnicalAttribute,
    ProductInfo,
    RequirementExtractionResponse
)
from backend.retrieval.text_prep import STOP_WORDS
from backend.utils.logger import get_logger

logger = get_logger("RequirementExtractor")

# Known product domain mapping
PRODUCT_DOMAINS = [
    ("Transformers", ["distribution transformer", "power transformer", "oil immersed transformer", "transformer", "substation"]),
    ("Lighting & Luminaires", ["street light", "led luminaire", "led street light", "luminaire", "led lamp", "led bulb", "fixture"]),
    ("Cables & Wiring", ["xlpe cable", "armored cable", "power cable", "pvc cable", "building wire", "electrical cable", "cable"]),
    ("Cement & Building Materials", ["portland slag cement", "portland pozzolana cement", "cement", "concrete", "mortar"]),
    ("Pumps & Turbines", ["submersible pump", "water pump", "pump set", "borewell pump", "centrifugal pump"]),
    ("Solar Energy", ["solar panel", "pv module", "photovoltaic", "crystalline silicon"]),
    ("Pipes & Fittings", ["hdpe pipe", "polyethylene pipe", "water pipe", "pipeline"]),
    ("Fire Safety", ["fire extinguisher", "portable extinguisher", "co2 extinguisher"]),
    ("Structural Steel", ["structural steel", "steel beam", "hot rolled steel"])
]

def extract_is_mentions(text: str) -> List[str]:
    """
    Extracts explicitly mentioned IS/Indian Standard codes from text.
    Matches variations such as 'IS 10322', 'IS 10322 (Part 5/Sec 3) : 2012', 'IS 7098 (Part 1) : 1988'.
    """
    pattern = r"\bIS\s*:?\s*\d+(?:\s*\([^)]+\))?(?:\s*:\s*\d{4})?\b"
    matches = re.findall(pattern, text, flags=re.IGNORECASE)
    
    seen = set()
    cleaned_matches = []
    for match in matches:
        # Standardize spacing
        norm = re.sub(r"\s+", " ", match.strip())
        if norm.upper() not in seen:
            seen.add(norm.upper())
            cleaned_matches.append(norm)
            
    return cleaned_matches


def extract_technical_attributes(text: str) -> List[TechnicalAttribute]:
    """
    Extracts numeric technical attributes, values, units, and source snippets.
    Supports power, capacity, voltage, current, frequency, efficiency, dimensions, and IP ratings.
    """
    attributes: List[TechnicalAttribute] = []
    seen_sources: Set[str] = set()

    def add_attribute(attr: str, val: str, unit: Optional[str], src: str):
        src_clean = src.strip()
        if src_clean in seen_sources:
            return
        seen_sources.add(src_clean)
        attributes.append(TechnicalAttribute(
            attribute=attr,
            value=val,
            unit=unit,
            source_text=src_clean
        ))

    # 1. Ingress Protection (IP Rating e.g. IP66, IP65, IP 67)
    ip_matches = re.finditer(r"\b(IP\s*\d{2})\b", text, re.IGNORECASE)
    for m in ip_matches:
        full_match = m.group(1).replace(" ", "").upper()
        add_attribute("ingress_protection", full_match, None, m.group(0))

    # 2. Power & Capacity (e.g. 50W, 100 kVA, 2500 kVA, 5 kW, 2 MW)
    power_matches = re.finditer(r"\b(\d+(?:\.\d+)?)\s*(W|kW|MW|kVA|MVA|VA|HP)\b", text)
    for m in power_matches:
        val, unit = m.group(1), m.group(2)
        add_attribute("capacity", val, unit, m.group(0))

    # 3. Voltage (e.g. 240V, 1100V, 11 kV, 33 kV, 433 V AC)
    voltage_matches = re.finditer(r"\b(\d+(?:\.\d+)?)\s*(V|kV|mV)\b", text, re.IGNORECASE)
    for m in voltage_matches:
        val, unit = m.group(1), m.group(2)
        # Avoid matching kVA or MW accidentally
        if unit.upper() in ["V", "KV", "MV"]:
            add_attribute("voltage", val, unit, m.group(0))

    # 4. Current (e.g. 10 A, 250 A, 50 mA)
    current_matches = re.finditer(r"\b(\d+(?:\.\d+)?)\s*(A|mA|kA)\b", text)
    for m in current_matches:
        val, unit = m.group(1), m.group(2)
        add_attribute("current", val, unit, m.group(0))

    # 5. Frequency (e.g. 50 Hz, 60Hz)
    freq_matches = re.finditer(r"\b(\d+(?:\.\d+)?)\s*(Hz|kHz)\b", text, re.IGNORECASE)
    for m in freq_matches:
        val, unit = m.group(1), m.group(2)
        add_attribute("frequency", val, unit, m.group(0))

    # 6. Efficiency / Percentage (e.g. 98%, 85 percent)
    pct_matches = re.finditer(r"\b(\d+(?:\.\d+)?)\s*(%|percent|pct)", text, re.IGNORECASE)
    for m in pct_matches:
        val, unit = m.group(1), "%"
        add_attribute("efficiency", val, unit, m.group(0))

    # 7. Dimensions / Outer Diameter / Size (e.g. 100 mm, 16 mm, 2.5 mm)
    dim_matches = re.finditer(r"\b(\d+(?:\.\d+)?)\s*(mm|cm|m|inch)\b", text, re.IGNORECASE)
    for m in dim_matches:
        val, unit = m.group(1), m.group(2)
        add_attribute("dimension", val, unit, m.group(0))

    # 8. Surge Protection (e.g. 10 kV surge)
    surge_matches = re.finditer(r"\b(\d+(?:\.\d+)?)\s*(kV\s*surge|surge)\b", text, re.IGNORECASE)
    for m in surge_matches:
        val = m.group(1) if m.group(1) else "1"
        add_attribute("surge_protection", val, "kV", m.group(0))

    return attributes


def extract_safety_clauses(text: str) -> List[str]:
    """Extracts lines/clauses relating to safety, protection ratings, earthing, or insulation."""
    safety_terms = {
        "safety", "protection", "surge", "fire", "flame", "grounding",
        "earthing", "insulation", "dielectric", "overload", "ip66", "ip65"
    }
    
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    clauses = []
    seen = set()
    
    for line in lines:
        line_lower = line.lower()
        if any(term in line_lower for term in safety_terms):
            if line not in seen and len(line) < 300:
                seen.add(line)
                clauses.append(line)
                
    return clauses[:5]  # Top 5 clauses


def extract_installation_clauses(text: str) -> List[str]:
    """Extracts lines/clauses relating to installation environments, operating conditions, or mounting."""
    install_terms = {
        "outdoor", "indoor", "municipal", "underground", "ambient",
        "temperature", "humidity", "installation", "mounting", "pole",
        "submersible", "borewell", "marine", "highway"
    }
    
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    clauses = []
    seen = set()
    
    for line in lines:
        line_lower = line.lower()
        if any(term in line_lower for term in install_terms):
            if line not in seen and len(line) < 300:
                seen.add(line)
                clauses.append(line)
                
    return clauses[:5]


def identify_product(text: str) -> ProductInfo:
    """
    Deterministic product identification strategy using domain keyword matching
    and headline phrase extraction.
    """
    text_lower = text.lower()
    
    detected_cat = None
    detected_name = None
    
    for cat, keywords in PRODUCT_DOMAINS:
        for kw in keywords:
            if kw in text_lower:
                detected_cat = cat
                detected_name = kw.title()
                break
        if detected_cat:
            break
            
    if not detected_name:
        # Fallback: check first meaningful line
        lines = [l.strip() for l in text.split("\n") if l.strip() and not l.startswith("---")]
        if lines:
            first_line = lines[0]
            if len(first_line) < 100:
                detected_name = first_line

    return ProductInfo(
        name=detected_name,
        category=detected_cat
    )


def extract_keywords(text: str) -> List[str]:
    """Extracts key technical tokens and terms from text."""
    clean = re.sub(r"[^\w\s\-]", " ", text.lower())
    tokens = clean.split()
    
    freq = {}
    for t in tokens:
        if t not in STOP_WORDS and len(t) > 2 and not t.isdigit():
            freq[t] = freq.get(t, 0) + 1
            
    sorted_tokens = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [t[0] for t in sorted_tokens[:10]]


def extract_requirements(text: str, filename: Optional[str] = None) -> RequirementExtractionResponse:
    """
    Main orchestrator converting document text into a structured RequirementExtractionResponse.
    Fully deterministic, auditable, and non-hallucinating.
    """
    if not text or not text.strip():
        return RequirementExtractionResponse(
            product=ProductInfo(),
            technical_requirements=[],
            standards_mentions=[],
            safety_requirements=[],
            installation_requirements=[],
            keywords=[],
            raw_text=text or ""
        )

    product = identify_product(text)
    tech_reqs = extract_technical_attributes(text)
    is_mentions = extract_is_mentions(text)
    safety_clauses = extract_safety_clauses(text)
    install_clauses = extract_installation_clauses(text)
    keywords = extract_keywords(text)

    logger.info(
        f"Extracted requirements for '{filename or 'text'}': "
        f"Product='{product.name}', Category='{product.category}', "
        f"TechAttrs={len(tech_reqs)}, ISMentions={len(is_mentions)}"
    )

    return RequirementExtractionResponse(
        product=product,
        technical_requirements=tech_reqs,
        standards_mentions=is_mentions,
        safety_requirements=safety_clauses,
        installation_requirements=install_clauses,
        keywords=keywords,
        raw_text=text
    )
