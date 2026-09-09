"""
Procurement Requirement Gap Analysis Engine.

Compares extracted procurement requirements (product type, technical attributes,
keywords, safety clauses, and environmental conditions) against evidence represented
in recommended Indian Standards.

STRICT DATA HONESTY GUARDRAIL:
Gap analysis must NEVER claim or state "No Indian Standard exists" or "No BIS standard covers X".
When evidence is missing in the prototype corpus, the engine reports:
"Not evidenced in current prototype corpus".
"""

import re
import logging
from typing import List, Dict, Any, Optional

from backend.models.schemas import (
    CoverageStatus,
    RequirementCoverage,
    GapAnalysisResponse,
    RecommendationItem,
    RequirementExtractionResponse,
    TechnicalAttribute,
    EvidencePackage
)
from backend.processing.requirement_extractor import extract_requirements

logger = logging.getLogger(__name__)


class GapAnalysisEngine:
    """
    Deterministic Gap Analysis Engine for comparing procurement requirements
    against evidence in recommended Indian Standards.
    """

    def __init__(self, extractor_func=None):
        self.extractor_func = extractor_func or extract_requirements

    def analyze_gaps(
        self,
        query: str,
        recommendations: List[RecommendationItem],
        requirements: Optional[RequirementExtractionResponse] = None
    ) -> GapAnalysisResponse:
        """
        Analyze coverage gaps between procurement requirements and top recommended standards.
        """
        # 1. Obtain structured requirements
        if not requirements:
            requirements = self.extractor_func(query)

        # 2. Extract granular requirement items
        req_items = self._build_granular_requirements(query, requirements)

        # 3. Assess evidence coverage for each requirement item
        coverage_results: List[RequirementCoverage] = []
        for req_id, text, category, norm_value, raw_attr in req_items:
            cov = self._evaluate_single_requirement(
                req_id=req_id,
                req_text=text,
                category=category,
                norm_value=norm_value,
                raw_attr=raw_attr,
                recommendations=recommendations
            )
            coverage_results.append(cov)

        # 4. Compute counts & summary statistics
        covered = sum(1 for c in coverage_results if c.status == CoverageStatus.COVERED)
        partially = sum(1 for c in coverage_results if c.status == CoverageStatus.PARTIALLY_COVERED)
        not_evidenced = sum(1 for c in coverage_results if c.status == CoverageStatus.NOT_EVIDENCED)
        requires_verif = sum(1 for c in coverage_results if c.status == CoverageStatus.REQUIRES_VERIFICATION)
        total = len(coverage_results)

        if total > 0:
            summary = (
                f"{covered} of {total} extracted procurement requirements have direct supporting evidence "
                f"in the current prototype corpus. {partially} requirement(s) are partially supported, "
                f"and {not_evidenced} requirement(s) were not evidenced in the prototype corpus."
            )
        else:
            summary = "No granular procurement requirements extracted for gap analysis."

        return GapAnalysisResponse(
            query=query or "Structured Requirements Input",
            total_requirements=total,
            covered_count=covered,
            partially_covered_count=partially,
            not_evidenced_count=not_evidenced,
            requires_verification_count=requires_verif,
            coverage_summary=summary,
            requirements=coverage_results,
            verification_required=True,
            limitations=[
                "Assessment is strictly based on evidence available in the local prototype corpus (14 demo standards).",
                "'Not evidenced' means no evidence was found in this prototype corpus; it does NOT imply that no applicable Indian Standard exists in official BIS records."
            ],
            disclaimer=(
                "DISCLAIMER: Gap analysis compares extracted requirements against available prototype corpus evidence. "
                "'Not evidenced' means no evidence was found in this demo corpus; it does NOT imply that no applicable "
                "Indian Standard exists in the official BIS library."
            )
        )

    def _build_granular_requirements(
        self,
        query: str,
        requirements: RequirementExtractionResponse
    ) -> List[tuple]:
        """
        Build a list of tuples: (req_id, display_text, category, normalized_value, raw_obj)
        """
        items = []
        counter = 1

        # A. Product Identification
        if requirements.product and requirements.product.name:
            items.append((
                f"REQ-{counter:03d}",
                f"Product Type: {requirements.product.name}",
                "product_type",
                requirements.product.name.lower(),
                requirements.product
            ))
            counter += 1
        elif query:
            items.append((
                f"REQ-{counter:03d}",
                f"Query Specification: '{query}'",
                "product_type",
                query.lower(),
                None
            ))
            counter += 1

        # B. Technical Attributes
        for tech in requirements.technical_requirements:
            display = f"{tech.attribute.title()}: {tech.value}"
            if tech.unit:
                display += f" {tech.unit}"
            items.append((
                f"REQ-{counter:03d}",
                display,
                tech.attribute.lower(),
                f"{tech.value} {tech.unit or ''}".strip().lower(),
                tech
            ))
            counter += 1

        # C. Safety & Protection Requirements
        for safety in requirements.safety_requirements:
            items.append((
                f"REQ-{counter:03d}",
                f"Safety Requirement: {safety}",
                "safety",
                safety.lower(),
                safety
            ))
            counter += 1

        # D. Installation & Environmental Requirements
        for env in requirements.installation_requirements:
            items.append((
                f"REQ-{counter:03d}",
                f"Installation/Environment: {env}",
                "installation",
                env.lower(),
                env
            ))
            counter += 1

        # E. Explicit Standard Mentions
        for std in requirements.standards_mentions:
            items.append((
                f"REQ-{counter:03d}",
                f"Specified Standard: {std}",
                "explicit_standard",
                std.lower(),
                std
            ))
            counter += 1

        # F. Fallback Keywords if no technical attributes extracted
        if len(items) <= 1 and requirements.keywords:
            for kw in requirements.keywords:
                # Avoid duplicate keyword items
                if not any(kw.lower() in it[3] for it in items):
                    items.append((
                        f"REQ-{counter:03d}",
                        f"Technical Keyword: '{kw}'",
                        "keyword",
                        kw.lower(),
                        kw
                    ))
                    counter += 1

        return items

    def _evaluate_single_requirement(
        self,
        req_id: str,
        req_text: str,
        category: str,
        norm_value: str,
        raw_attr: Any,
        recommendations: List[RecommendationItem]
    ) -> RequirementCoverage:
        """
        Evaluate a single requirement against the list of recommended standards.
        """
        supporting_stds: List[str] = []
        evidence_list: List[str] = []
        missing_aspects: List[str] = []

        is_explicit_tech = category not in ("product_type", "keyword", "safety", "installation", "explicit_standard")
        
        # Collect all standards evidence
        for rec in recommendations:
            std_code = rec.is_number
            scope_lower = (rec.scope or "").lower()
            title_lower = (rec.title or "").lower()
            desc_lower = (rec.description or "").lower()
            keywords_lower = [k.lower() for k in rec.keywords]
            prod_cat_lower = (rec.product_category or "").lower()
            reasons_lower = " ".join(rec.reasons or []).lower()

            # 1. Check direct string match in scope/title/description/keywords
            found_in_scope = norm_value in scope_lower or norm_value in desc_lower
            found_in_title = norm_value in title_lower
            found_in_keywords = any(norm_value in k or k in norm_value for k in keywords_lower)
            found_in_reasons = norm_value in reasons_lower

            # 2. Token and domain synonym matching
            val_tokens = [t for t in re.split(r'[\s,/:()\'"]+', norm_value) if len(t) >= 2 and t not in ("product", "type", "query", "specification", "for", "with", "and", "the", "in", "of")]
            
            # Domain synonyms
            expanded_tokens = set(val_tokens)
            if "hdpe" in val_tokens:
                expanded_tokens.update(["polyethylene", "pe", "hdpe"])
            if "xlpe" in val_tokens:
                expanded_tokens.update(["crosslinked", "polyethylene", "xlpe"])
            if "pv" in val_tokens or "photovoltaic" in val_tokens:
                expanded_tokens.update(["photovoltaic", "pv", "solar"])

            matched_count = 0
            for t in expanded_tokens:
                if t in scope_lower or t in title_lower or t in prod_cat_lower or t in desc_lower or any(t in k for k in keywords_lower):
                    matched_count += 1

            token_ratio = (matched_count / len(val_tokens)) if len(val_tokens) > 0 else 0.0

            if found_in_scope or found_in_title:
                evidence_list.append(f"Explicit evidence in {std_code}: Scope/title directly specifies or covers '{norm_value}'.")
                supporting_stds.append(std_code)
            elif token_ratio >= 0.75 or (category == "product_type" and token_ratio >= 0.5):
                evidence_list.append(f"Technical & domain alignment in {std_code}: Scope/keywords cover product parameters '{norm_value}'.")
                supporting_stds.append(std_code)
            elif is_explicit_tech and len(val_tokens) > 0 and matched_count == len(val_tokens):
                evidence_list.append(f"Technical parameter match in {std_code}: Corpus metadata aligns with '{norm_value}'.")
                supporting_stds.append(std_code)
            elif found_in_keywords or found_in_reasons or token_ratio >= 0.4:
                evidence_list.append(f"Keyword/retrieval alignment in {std_code}: Corpus signals match requirement '{norm_value}'.")
                supporting_stds.append(std_code)

        # Remove duplicate standard IDs
        supporting_stds = list(dict.fromkeys(supporting_stds))

        # Determine status and score based on transparent hierarchy
        if len(supporting_stds) > 0 and any("Explicit evidence" in e or "Technical parameter match" in e or "Technical & domain alignment" in e for e in evidence_list):
            status = CoverageStatus.COVERED
            coverage_score = 1.0
        elif len(supporting_stds) > 0:
            status = CoverageStatus.PARTIALLY_COVERED
            coverage_score = 0.6
            missing_aspects.append(f"Requirement '{req_text}' has partial keyword or category alignment, but exact parameter scope requires verification.")
        elif category in ("safety", "installation"):
            status = CoverageStatus.REQUIRES_VERIFICATION
            coverage_score = 0.4
            missing_aspects.append(f"General clause '{req_text}' requires detailed clause verification in full IS standards documents.")
        else:
            status = CoverageStatus.NOT_EVIDENCED
            coverage_score = 0.0
            # GUARANTEED PHRASING RULE: "Not evidenced in current prototype corpus"
            missing_aspects.append("Not evidenced in current prototype corpus.")

        return RequirementCoverage(
            requirement_id=req_id,
            requirement_text=req_text,
            category=category,
            status=status,
            coverage_score=coverage_score,
            supporting_standard_ids=supporting_stds,
            evidence=evidence_list,
            missing_aspects=missing_aspects,
            verification_required=True,
            limitations=[
                "Evaluation strictly based on 14 demo standards in prototype corpus.",
                "Does NOT constitute statutory or legal compliance assessment."
            ]
        )
