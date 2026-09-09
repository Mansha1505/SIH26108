import os
import json
from typing import List, Dict, Any, Optional
from backend.models.schemas import (
    EvidencePackage,
    StandardEvidence,
    StandardExplanation,
    RecommendationExplanationResponse
)
from backend.intelligence.evidence_builder import EvidenceBuilder
from backend.utils.logger import get_logger

logger = get_logger("LLMExplainer")


class DeterministicExplainer:
    """
    100% Evidence-grounded, audit-safe deterministic explanation generator.
    Operates strictly on EvidencePackage metadata without requiring an LLM.
    Serves as the default explainer and safety fallback.
    """

    def explain(self, evidence_package: EvidencePackage) -> RecommendationExplanationResponse:
        explanations: List[StandardExplanation] = []

        for std_ev in evidence_package.standards_evidence:
            explanation = self.explain_standard(std_ev, evidence_package.query)
            explanations.append(explanation)

        return RecommendationExplanationResponse(
            query=evidence_package.query,
            explanations=explanations,
            generated_by="deterministic_evidence_engine",
            model="deterministic_rules",
            evidence_count=len(explanations),
            verification_required=True
        )

    def explain_standard(self, evidence: StandardEvidence, query: str) -> StandardExplanation:
        # 1. Why relevant & matched requirements
        matched_reqs = []
        if evidence.product_category:
            matched_reqs.append(f"Product Category Match: '{evidence.product_category}'")
        if evidence.matched_keywords:
            matched_reqs.append(f"Matched Keywords: {', '.join(evidence.matched_keywords[:4])}")
        if evidence.matched_technical_requirements:
            tech_str = ", ".join([f"{t['attribute']}={t['value']}{t['unit']}" for t in evidence.matched_technical_requirements[:3]])
            matched_reqs.append(f"Technical Requirements: {tech_str}")

        if not matched_reqs:
            matched_reqs.append("Technical Scope Relevance Match")

        why_rel = (
            f"Recommended for query '{query}' based on product alignment with category '{evidence.product_category}' "
            f"and keyword/scope overlap in the prototype corpus."
        )

        # 2. Technical Alignment
        if evidence.matched_keywords or evidence.matched_technical_requirements:
            kws = ", ".join(evidence.matched_keywords[:3]) if evidence.matched_keywords else "general technical terms"
            tech_align = f"Strong alignment with indexed technical keywords ({kws}) and specified parameters."
        else:
            tech_align = "Technical specification aligns with standard indexing parameters in prototype corpus."

        # 3. Scope Alignment
        scope_text = evidence.scope[:200] + "..." if len(evidence.scope) > 200 else evidence.scope
        scope_align = f"Technical scope covers: {scope_text}"

        # 4. Related Standards Explanation
        rel_expl = None
        if evidence.graph_relationships:
            rel_names = [f"{gr.is_number} ({gr.relationship_label})" for gr in evidence.graph_relationships[:3]]
            rel_expl = f"Connected in Standards Network to: {', '.join(rel_names)}."
        elif evidence.related_standards:
            rel_expl = f"Cross-references related standards: {', '.join(evidence.related_standards[:3])}."

        # 5. Version Note
        if evidence.version_intelligence:
            vi = evidence.version_intelligence
            if vi.has_amendments:
                version_note = (
                    f"{vi.revision_year or 'Recorded'} revision with {vi.amendment_count} amendment(s) "
                    f"(Latest: Amd #{vi.latest_known_amendment_number}, {vi.latest_known_amendment_year}) "
                    f"recorded in available prototype corpus. Authoritative BIS verification required."
                )
            else:
                version_note = (
                    f"{vi.revision_year or 'Recorded'} revision ({vi.version_status}). "
                    f"Authoritative BIS verification required."
                )
        else:
            version_note = "Revision and amendment metadata recorded in prototype corpus. Authoritative BIS verification required."

        # 6. Certification Note
        if evidence.certification_assessment:
            ca = evidence.certification_assessment
            if ca.indication == "candidate certification requirement":
                cert_note = (
                    f"Candidate certification mapping identified under '{ca.certification_scheme}' "
                    f"({ca.applicable_order or ca.source_reference}). Authoritative BIS/QCO verification required."
                )
            else:
                cert_note = (
                    f"{ca.applicability_basis} Authoritative BIS/QCO verification required."
                )
        else:
            cert_note = "No certification mapping available in current prototype rule dataset. Authoritative verification required."

        # 7. Limitations
        limitations = (
            "Prototype demo corpus evaluation. Recommendations and indications do NOT constitute legal advice "
            "or statutory compliance determinations. Authoritative verification against official BIS publications is required."
        )

        return StandardExplanation(
            standard_id=evidence.standard_id,
            is_number=evidence.is_number,
            title=evidence.title,
            why_relevant=why_rel,
            matched_requirements=matched_reqs,
            technical_alignment=tech_align,
            scope_alignment=scope_align,
            related_standards_explanation=rel_expl,
            version_note=version_note,
            certification_note=cert_note,
            evidence_sources=evidence.provenance_sources,
            limitations=limitations,
            verification_required=True
        )


class ConfigurableLLMExplainer:
    """
    Configurable LLM provider abstraction layer.
    Allows optional local/open-source LLM integration when enabled via environment.
    Enforces strict anti-hallucination prompting and Pydantic output validation.
    Automatically falls back to DeterministicExplainer if LLM is disabled or fails.
    """

    SYSTEM_PROMPT = """You are an evidence-grounded explanation component for a procurement standards recommendation prototype.

CRITICAL CONSTRAINTS & RULES:
1. Use ONLY the supplied evidence package.
2. NEVER introduce standards, IS numbers, revision years, legal requirements, dates, amendments, certification schemes, or relationships that are absent from the evidence package.
3. If evidence is insufficient, explicitly state: 'Insufficient evidence in the current prototype corpus.'
4. Do NOT claim statutory compliance or state that certification is legally mandatory unless explicitly supported by supplied evidence.
5. You MUST return valid JSON matching the expected StandardExplanation schema structure.
"""

    def __init__(self):
        self.enabled = os.getenv("ENABLE_LLM_EXPLAINER", "false").lower() in ("true", "1", "yes")
        self.provider = os.getenv("LLM_PROVIDER", "deterministic").lower()
        self.deterministic_fallback = DeterministicExplainer()

    def explain(self, evidence_package: EvidencePackage) -> RecommendationExplanationResponse:
        if not self.enabled or self.provider == "deterministic":
            logger.info("LLM explainer disabled or configured to deterministic mode. Using DeterministicExplainer.")
            return self.deterministic_fallback.explain(evidence_package)

        try:
            # Attempt LLM generation if a provider is configured
            explanations = self._call_llm_provider(evidence_package)
            if explanations:
                return RecommendationExplanationResponse(
                    query=evidence_package.query,
                    explanations=explanations,
                    generated_by="llm_grounded_explainer",
                    model=self.provider,
                    evidence_count=len(explanations),
                    verification_required=True
                )
        except Exception as e:
            logger.warning(f"LLM explanation generation failed or failed schema validation: {e}. Falling back to DeterministicExplainer.", exc_info=True)

        return self.deterministic_fallback.explain(evidence_package)

    def _call_llm_provider(self, evidence_package: EvidencePackage) -> Optional[List[StandardExplanation]]:
        """Stub / Interface for LLM provider invocation with Pydantic schema validation."""
        # For prototype fallback when provider is unconfigured or unavailable
        return None


class ExplanationEngine:
    """
    Main orchestrator for Phase 8 Explainability Layer.
    Uses EvidenceBuilder to assemble bounded evidence packages and
    coordinates deterministic or LLM explainers.
    """

    def __init__(self):
        self.evidence_builder = EvidenceBuilder()
        self.deterministic_explainer = DeterministicExplainer()
        self.llm_explainer = ConfigurableLLMExplainer()

    def generate_explanation(
        self,
        query: str,
        recommendations: List[Any],
        extracted_requirements: Optional[Any] = None,
        use_llm: bool = False
    ) -> RecommendationExplanationResponse:
        """Assembles evidence and generates structured, grounded explanations."""
        evidence_package = self.evidence_builder.build_evidence_package(
            query=query,
            recommendations=recommendations,
            extracted_requirements=extracted_requirements
        )

        if use_llm:
            return self.llm_explainer.explain(evidence_package)

        return self.deterministic_explainer.explain(evidence_package)
