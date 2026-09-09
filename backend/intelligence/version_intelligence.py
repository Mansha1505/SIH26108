from typing import Dict, Any, List, Optional
import copy
from backend.utils.logger import get_logger

logger = get_logger("VersionIntelligence")


class VersionAmendmentAnalyzer:
    """
    Deterministic Version & Amendment Intelligence Analyzer.
    Operates purely on structured standard metadata.
    
    IMPORTANT SYSTEM POSITIONING:
    - This is NOT a legal compliance engine.
    - All status descriptions qualify results as "in available corpus".
    - Always requires authoritative BIS verification.
    - Never uses external LLMs or semantic vectors.
    """

    def analyze(self, standard: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes revision year, amendment list, and status flags for an Indian Standard.
        Does NOT mutate the input standard dictionary.
        Handles missing, empty, or malformed fields safely.
        """
        if not isinstance(standard, dict):
            standard = {}

        standard_id = standard.get("id")
        is_number = str(standard.get("is_number") or "Unknown Designation")
        
        # 1. Parse revision year safely
        revision_year: Optional[int] = None
        raw_rev_year = standard.get("revision_year")
        if raw_rev_year is not None:
            try:
                revision_year = int(raw_rev_year)
            except (ValueError, TypeError):
                revision_year = None

        # 2. Parse & sanitize status
        status_str = str(standard.get("status") or "Active (DEMO / SAMPLE DATA)")
        status_lower = status_str.lower()

        # 3. Parse, sanitize, & sort amendments deterministically
        raw_amendments = standard.get("amendments")
        sanitized_amendments: List[Dict[str, Any]] = []

        if isinstance(raw_amendments, list):
            for item in raw_amendments:
                if isinstance(item, dict):
                    # Safely extract amendment fields
                    amd_num: Optional[int] = None
                    try:
                        if item.get("amendment_number") is not None:
                            amd_num = int(item["amendment_number"])
                    except (ValueError, TypeError):
                        amd_num = None

                    amd_year: Optional[int] = None
                    try:
                        if item.get("year") is not None:
                            amd_year = int(item["year"])
                    except (ValueError, TypeError):
                        amd_year = None

                    amd_title = str(item.get("title") or f"Amendment No. {amd_num or 'Unnumbered'}")

                    sanitized_amendments.append({
                        "amendment_number": amd_num,
                        "year": amd_year,
                        "title": amd_title
                    })

        # Deterministic sorting: sort by year (descending, treating None as 0), then amendment_number (descending, treating None as 0)
        sorted_amendments = sorted(
            sanitized_amendments,
            key=lambda x: (x["year"] or 0, x["amendment_number"] or 0),
            reverse=True
        )

        amendment_count = len(sorted_amendments)
        has_amendments = amendment_count > 0

        latest_known_amendment_year: Optional[int] = None
        latest_known_amendment_number: Optional[int] = None

        if has_amendments:
            latest_known_amendment_year = sorted_amendments[0]["year"]
            latest_known_amendment_number = sorted_amendments[0]["amendment_number"]

        # 4. Deterministic Version Status Rules
        if "superseded" in status_lower or "withdrawn" in status_lower:
            version_status = "Superseded"
        elif revision_year is not None and has_amendments:
            version_status = "Active — amendments recorded in corpus"
        elif revision_year is not None:
            version_status = "Active — latest known revision in corpus"
        else:
            version_status = "Revision information unavailable"

        # 5. Construct human-readable version summary
        if version_status == "Superseded":
            summary = f"{is_number} status is recorded as Superseded in the available corpus. Verification required."
        elif version_status == "Active — amendments recorded in corpus":
            latest_desc = ""
            if latest_known_amendment_number or latest_known_amendment_year:
                latest_desc = f" (Latest: Amd. #{latest_known_amendment_number or 'N/A'}, {latest_known_amendment_year or 'N/A'})"
            summary = (
                f"{revision_year} revision with {amendment_count} amendment(s) recorded in the available corpus{latest_desc}."
            )
        elif version_status == "Active — latest known revision in corpus":
            summary = f"{revision_year} revision with no active amendments recorded in the available demo corpus."
        else:
            summary = "Revision year metadata unavailable in the demo corpus. Authoritative verification required."

        source_url = standard.get("source_url")

        return {
            "standard_id": standard_id,
            "is_number": is_number,
            "revision_year": revision_year,
            "status": status_str,
            "latest_known_amendment_year": latest_known_amendment_year,
            "latest_known_amendment_number": latest_known_amendment_number,
            "amendment_count": amendment_count,
            "has_amendments": has_amendments,
            "version_status": version_status,
            "summary": summary,
            "verification_required": True,
            "source_url": source_url,
            "amendment_history": sorted_amendments
        }
