import json
import os
from typing import Dict, Any, List, Optional, Union
from backend.models.schemas import CertificationAssessment, CertificationSummary
from backend.utils.logger import get_logger

logger = get_logger("CertificationRuleEngine")

DEFAULT_RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "certification_rules.json"
)


class CertificationRuleEngine:
    """
    Deterministic Certification Rule Engine.
    Operates purely on explicit rule datasets without LLM inference or semantic vectors.
    
    IMPORTANT POSITIONING DISCLAIMER:
    - This is NOT a legal compliance or statutory enforcement engine.
    - Does NOT claim legal compliance or mandatory BIS certification guarantees.
    - All outputs use cautious terminology ("candidate certification requirement identified from prototype rule dataset").
    - Always requires authoritative verification against official BIS records.
    """

    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = rules_path or DEFAULT_RULES_PATH
        self.rules: List[Dict[str, Any]] = []
        self.standard_id_rule_map: Dict[str, Dict[str, Any]] = {}
        self.category_rule_map: Dict[str, Dict[str, Any]] = {}
        self._load_rules()

    def _load_rules(self):
        """Loads and indexes certification rules from JSON dataset."""
        self.rules.clear()
        self.standard_id_rule_map.clear()
        self.category_rule_map.clear()

        if not os.path.exists(self.rules_path):
            logger.warning(f"Certification rules dataset file not found at: {self.rules_path}")
            return

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for rule in data:
                    if isinstance(rule, dict) and "rule_id" in rule:
                        self.rules.append(rule)
                        
                        # Index by standard_ids
                        std_ids = rule.get("standard_ids", [])
                        if isinstance(std_ids, list):
                            for std_id in std_ids:
                                if std_id and isinstance(std_id, str):
                                    self.standard_id_rule_map[std_id.strip().lower()] = rule

                        # Index by product_category
                        cat = rule.get("product_category")
                        if cat and isinstance(cat, str):
                            self.category_rule_map[cat.strip().lower()] = rule

            logger.info(f"Loaded {len(self.rules)} certification rules into engine.")
        except Exception as e:
            logger.error(f"Failed to load certification rules from {self.rules_path}: {e}", exc_info=True)

    def assess_standard(
        self,
        standard_or_id: Optional[Union[Dict[str, Any], str]] = None,
        product_category: Optional[str] = None
    ) -> CertificationAssessment:
        """
        Assesses a standard dictionary or standard_id/category pair against certification rules.
        Deterministic priority:
        1. Exact standard_id match
        2. Exact product_category match
        3. Fallback unmapped status
        """
        std_id = None
        cat = product_category

        if isinstance(standard_or_id, dict):
            std_id = standard_or_id.get("id") or standard_or_id.get("is_number")
            if not cat:
                cat = standard_or_id.get("product_category")
        elif isinstance(standard_or_id, str):
            std_id = standard_or_id

        std_id_clean = str(std_id).strip() if std_id else ""
        cat_clean = str(cat).strip() if cat else ""

        # Priority 1: Exact standard_id match
        if std_id_clean and std_id_clean.lower() in self.standard_id_rule_map:
            rule = self.standard_id_rule_map[std_id_clean.lower()]
            return self._build_assessment(
                rule=rule,
                matched_standard_id=std_id_clean,
                matched_product_category=cat_clean or None
            )

        # Priority 2: Exact product_category match
        if cat_clean and cat_clean.lower() in self.category_rule_map:
            rule = self.category_rule_map[cat_clean.lower()]
            return self._build_assessment(
                rule=rule,
                matched_standard_id=std_id_clean or None,
                matched_product_category=cat_clean
            )

        # Priority 3: Fallback unmapped status
        return CertificationAssessment(
            rule_id=None,
            certification_scheme="No certification mapping available",
            scheme_status="unmapped",
            indication="no certification mapping available",
            matched_standard_id=std_id_clean or None,
            matched_product_category=cat_clean or None,
            applicability_basis="No certification mapping is available in the current prototype rule dataset.",
            source_type="prototype_rule_dataset",
            source_reference="Local prototype certification rules",
            verification_required=True,
            notes="Certification applicability requires authoritative verification against official BIS / Ministry notifications."
        )

    def assess_requirements(
        self,
        standard_ids: Optional[List[str]] = None,
        product_category: Optional[str] = None
    ) -> CertificationSummary:
        """
        Runs certification rule assessment across multiple standard IDs and/or product categories.
        Returns a structured CertificationSummary.
        """
        standard_ids = standard_ids or []
        matched_rules: Dict[str, CertificationAssessment] = {}

        # 1. Match standard_ids
        for std_id in standard_ids:
            if not std_id or not isinstance(std_id, str):
                continue
            std_clean = std_id.strip().lower()
            if std_clean in self.standard_id_rule_map:
                rule = self.standard_id_rule_map[std_clean]
                rule_id = rule["rule_id"]
                if rule_id not in matched_rules:
                    matched_rules[rule_id] = self._build_assessment(
                        rule=rule,
                        matched_standard_id=std_id,
                        matched_product_category=product_category
                    )

        # 2. Match product_category if provided
        if product_category and isinstance(product_category, str) and product_category.strip():
            cat_clean = product_category.strip().lower()
            if cat_clean in self.category_rule_map:
                rule = self.category_rule_map[cat_clean]
                rule_id = rule["rule_id"]
                if rule_id not in matched_rules:
                    matched_rules[rule_id] = self._build_assessment(
                        rule=rule,
                        matched_standard_id=None,
                        matched_product_category=product_category
                    )

        assessments = list(matched_rules.values())
        has_candidate_reqs = any(
            a.indication == "candidate certification requirement" for a in assessments
        )

        return CertificationSummary(
            total_rules_matched=len(assessments),
            has_candidate_requirements=has_candidate_reqs,
            assessments=assessments,
            verification_required=True,
            disclaimer=(
                "DISCLAIMER: Certification indications are derived from a local prototype rule dataset. "
                "They do NOT constitute legal compliance advice or authoritative statutory determinations. "
                "Authoritative verification against official BIS records is required."
            )
        )

    def _build_assessment(
        self,
        rule: Dict[str, Any],
        matched_standard_id: Optional[str],
        matched_product_category: Optional[str]
    ) -> CertificationAssessment:
        """Constructs a clean CertificationAssessment object from a rule dictionary."""
        target_stds = rule.get("target_standard_ids") or rule.get("standard_ids") or []
        return CertificationAssessment(
            rule_id=rule.get("rule_id"),
            product_category=rule.get("product_category"),
            target_standard_ids=list(target_stds) if isinstance(target_stds, list) else [],
            certification_scheme=str(rule.get("certification_scheme") or "Unspecified Scheme"),
            scheme_status=str(rule.get("scheme_status") or "requires_authoritative_verification"),
            applicable_order=rule.get("applicable_order"),
            order_date=rule.get("order_date"),
            effective_date=rule.get("effective_date"),
            superseded_by=rule.get("superseded_by"),
            indication=str(rule.get("indication") or "candidate certification requirement"),
            matched_standard_id=matched_standard_id if matched_standard_id else None,
            matched_product_category=matched_product_category or rule.get("product_category"),
            applicability_basis=str(rule.get("applicability_basis") or "Prototype rule mapping"),
            source_type=str(rule.get("source_type") or "prototype_rule_dataset"),
            source_reference=str(rule.get("source_reference") or "Local prototype rule dataset"),
            source_url=rule.get("source_url"),
            verification_required=bool(rule.get("verification_required", True)),
            notes=str(rule.get("notes") or "Authoritative BIS verification required.")
        )

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """Returns all loaded rules."""
        return self.rules
