from typing import List, Dict, Any, Optional
from backend.retrieval.text_prep import tokenize_text, normalize_text
from backend.intelligence.version_intelligence import VersionAmendmentAnalyzer
from backend.utils.logger import get_logger

logger = get_logger("RankingEngine")

class CandidateRanker:
    """
    Ranks candidate documents and generates deterministic rule-based justification reasons.
    Modular design integrates first-stage hybrid scores, second-stage Cross-Encoder scores,
    deterministic Version & Amendment Intelligence, Knowledge Graph Relationships,
    and Certification Rule Assessments.
    """
    def __init__(
        self,
        standards: List[Dict[str, Any]],
        graph_builder: Optional[Any] = None,
        rule_engine: Optional[Any] = None
    ):
        self.standards = standards
        self.version_analyzer = VersionAmendmentAnalyzer()
        self.graph_builder = graph_builder
        self.rule_engine = rule_engine

    def rerank_and_explain(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Sorts candidates by final relevance_score, selects top_k, adds deterministic metadata reasons,
        attaches version & amendment intelligence, graph relationships, and certification assessments.
        """
        # Validate/clamp top_k
        clamped_top_k = max(1, min(int(top_k or 5), len(self.standards)))

        # Sort candidates descending by final relevance score
        sorted_candidates = sorted(candidates, key=lambda x: x["relevance_score"], reverse=True)
        top_candidates = sorted_candidates[:clamped_top_k]
        
        max_raw_score = top_candidates[0]["relevance_score"] if top_candidates else 0.0

        query_tokens = set(tokenize_text(query))
        query_norm = normalize_text(query)
        
        results = []
        for item in top_candidates:
            doc_idx = item["doc_index"]
            std = self.standards[doc_idx]
            raw_score = float(item["relevance_score"])

            if max_raw_score > 1e-9:
                rel_score = round((raw_score / max_raw_score) * 100.0)
            else:
                rel_score = 0.0

            # Analyze version, revision, and amendment intelligence
            version_intel = self.version_analyzer.analyze(std)
            
            # Query knowledge graph neighbors if graph_builder available
            graph_rels = []
            if self.graph_builder and std.get("id"):
                graph_rels = self.graph_builder.get_standard_neighbors(std["id"])

            # Query certification rule engine if rule_engine available
            cert_assessment = None
            if self.rule_engine:
                cert_assessment = self.rule_engine.assess_standard(std)
            
            reasons = self._generate_deterministic_reasons(
                query_tokens=query_tokens,
                query_norm=query_norm,
                standard=std,
                bm25_norm=item.get("bm25_norm", 0.0),
                semantic_raw=item.get("semantic_raw", 0.0),
                item=item,
                version_intel=version_intel,
                cert_assessment=cert_assessment
            )
            
            recommendation_item = {
                "id": std.get("id"),
                "is_number": std["is_number"],
                "title": std["title"],
                "scope": std["scope"],
                "sector": std["sector"],
                "product_category": std["product_category"],
                "keywords": std["keywords"],
                "revision_year": std.get("revision_year"),
                "status": std.get("status", "Active (DEMO / SAMPLE DATA)"),
                "source_url": std.get("source_url"),
                "description": std.get("description"),
                "amendments": std.get("amendments", []),
                "related_standards": std.get("related_standards", []),
                "relevance_score": raw_score,
                "relative_match_score": float(rel_score),
                "hybrid_score": item.get("hybrid_score"),
                "cross_encoder_score": item.get("cross_encoder_norm"),
                "reasons": reasons,
                "version_intelligence": version_intel,
                "graph_relationships": graph_rels,
                "certification_assessment": cert_assessment
            }
            results.append(recommendation_item)
            
        return results



    def _generate_deterministic_reasons(
        self,
        query_tokens: set,
        query_norm: str,
        standard: Dict[str, Any],
        bm25_norm: float,
        semantic_raw: float,
        item: Optional[Dict[str, Any]] = None,
        version_intel: Optional[Dict[str, Any]] = None,
        cert_assessment: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generates clear, deterministic metadata-driven explanations for procurement users."""
        reasons = []
        
        # 1. Product Category or Sector Overlap
        cat_norm = normalize_text(standard.get("product_category", ""))
        sec_norm = normalize_text(standard.get("sector", ""))
        
        cat_tokens = set(tokenize_text(cat_norm))
        sec_tokens = set(tokenize_text(sec_norm))
        
        if cat_tokens and (query_tokens & cat_tokens):
            matched = ", ".join(query_tokens & cat_tokens)
            reasons.append(f"Product category match: '{standard.get('product_category')}' (matched '{matched}')")
        elif sec_tokens and (query_tokens & sec_tokens):
            reasons.append(f"Engineering sector alignment: '{standard.get('sector')}'")
            
        # 2. Keyword Overlap
        kw_list = [k.lower() for k in standard.get("keywords", [])]
        matched_kws = [kw for kw in kw_list if kw in query_norm or any(t in kw for t in query_tokens)]
        if matched_kws:
            reasons.append(f"Matched standard keywords: {', '.join(matched_kws[:3])}")
            
        # 3. Scope Relevance
        scope_norm = normalize_text(standard.get("scope", ""))
        scope_tokens = set(tokenize_text(scope_norm))
        common_scope_tokens = query_tokens & scope_tokens
        if len(common_scope_tokens) >= 2:
            sample_terms = ", ".join(list(common_scope_tokens)[:3])
            reasons.append(f"High technical scope overlap on terms: {sample_terms}")
            
        # 4. Hybrid & Reranker Search Signals
        if item and item.get("reranked") is True and item.get("cross_encoder_norm") is not None:
            ce_score = item["cross_encoder_norm"]
            reasons.append(f"Cross-encoder deep relevance score: {ce_score:.2f}")
        elif semantic_raw >= 0.5:
            reasons.append(f"Strong semantic vector contextual similarity ({int(semantic_raw * 100)}%)")
        elif bm25_norm >= 0.5:
            reasons.append(f"Strong lexical keyword match density (BM25 normalized score: {bm25_norm})")

        # 5. Version & Amendment Intelligence Signal
        if version_intel:
            if version_intel.get("has_amendments"):
                reasons.append(
                    f"Version status: {version_intel.get('version_status')} "
                    f"(Latest: Amd #{version_intel.get('latest_known_amendment_number')}, {version_intel.get('latest_known_amendment_year')})"
                )
            elif version_intel.get("revision_year"):
                reasons.append(f"Revision year: {version_intel.get('revision_year')} ({version_intel.get('version_status')})")

        # 6. Certification Rule Indication Signal
        if cert_assessment:
            indication = getattr(cert_assessment, "indication", None)
            if isinstance(cert_assessment, dict):
                indication = cert_assessment.get("indication")

            if indication == "candidate certification requirement":
                scheme = getattr(cert_assessment, "certification_scheme", "BIS Certification")
                if isinstance(cert_assessment, dict):
                    scheme = cert_assessment.get("certification_scheme", "BIS Certification")
                reasons.append(f"Certification scheme: {scheme} (candidate requirement in prototype rules)")
            
        if not reasons:
            reasons.append("General semantic & technical scope relevance match")
            
        return reasons


