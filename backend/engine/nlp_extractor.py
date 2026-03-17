"""
engine/nlp_extractor.py
spaCy-based NLP extraction for clinical reports.
Extracts 13 target entities with confidence scoring.
"""
from __future__ import annotations

import re
from typing import Any

try:
    import spacy
    from spacy.matcher import Matcher
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    _nlp = None  # Graceful fallback if model not installed


# ─── Regex patterns ──────────────────────────────────────────────────────────
PATTERNS: dict[str, list[str]] = {
    "TUMOUR_SIZE": [
        r"\b(\d+\.?\d*)\s*(cm|mm)\b",
        r"tumou?r size[:\s]*(\d+\.?\d*)\s*(cm|mm)",
        r"measuring\s+(\d+\.?\d*)\s*(cm|mm)",
    ],
    "TNM_STAGE": [
        r"\b(T[0-4][a-z]?N[0-3][a-z]?M[0-1])\b",
        r"\bStage\s+([IVX]+[A-C]?)\b",
        r"\b(stage\s+[1-4][abc]?)\b",
    ],
    "ER_STATUS": [
        r"\bER[\s:]*([Pp]ositive|[Nn]egative|[Pp]os|[Nn]eg|\+|-)\b",
        r"[Ee]strogen [Rr]eceptor[\s:]*([Pp]ositive|[Nn]egative|[Pp]os|[Nn]eg)",
        r"\bER[\s:]*([\d]+%?)\b",
    ],
    "PR_STATUS": [
        r"\bPR[\s:]*([Pp]ositive|[Nn]egative|[Pp]os|[Nn]eg|\+|-)\b",
        r"[Pp]rogesterone [Rr]eceptor[\s:]*([Pp]ositive|[Nn]egative)",
    ],
    "HER2_STATUS": [
        r"\bHER[2-]?[\s:]*([Pp]ositive|[Nn]egative|equivocal|[0-3]\+)\b",
        r"HER2 protein expression[\s:]*([0-3]\+)",
        r"FISH[\s:]*(amplified|not amplified|negative|positive)",
    ],
    "KI67_VALUE": [
        r"\bKi[\s-]?67[\s:]*(\d+\.?\d*)%?\b",
        r"proliferation index[\s:]*(\d+\.?\d*)%?",
        r"MIB[\s-]?1[\s:]*(\d+\.?\d*)%?",
    ],
    "GRADE": [
        r"\b[Gg]rade[\s:]*([1-3]|I{1,3})\b",
        r"\b([Ww]ell|[Mm]oderately|[Pp]oorly)\s+differentiated\b",
        r"\bBR\s+[Gg]rade[\s:]*([1-3])\b",
    ],
    "LYMPH_NODES": [
        r"(\d+)\s*/\s*(\d+)\s+(?:lymph\s+)?nodes?\s+(?:were\s+)?positive",
        r"(\d+)\s+(?:of|out of)\s+(\d+)\s+(?:axillary\s+)?nodes?\s+(?:involved|positive)",
        r"lymph node[s]?\s+(?:involvement|status)[\s:]*([Pp]ositive|[Nn]egative)",
    ],
    "HISTOLOGY": [
        r"(?:invasive\s+|infiltrating\s+)?([Dd]uctal|[Ll]obular|[Mm]ucinous|[Mm]edullary|[Mm]etaplastic)\s+carcinoma",
        r"[Hh]istological type[\s:]*(.{5,50})",
    ],
    "PD_L1": [
        r"PD[\s-]?L1[\s:CPS]*(\d+\.?\d*)\b",
        r"PD[\s-]?L1\s+(?:expression\s+)?([Pp]ositive|[Nn]egative)",
    ],
    "BRCA_STATUS": [
        r"(BRCA[12])[\s:]*(?:mutation)?\s+([Dd]etected|[Pp]ositive|[Nn]ot detected|[Nn]egative|[Pp]athogenic)",
        r"(BRCA[12])\s+(?:germline\s+)?(?:mutation|variant)[\s:]*([Pp]ositive|[Nn]egative|[Dd]etected)",
    ],
    "TILS": [
        r"\bTIL[s]?[\s:]*(\d+\.?\d*)%?\b",
        r"[Tt]umour[\s-]?[Ii]nfiltrating [Ll]ymphocytes?[\s:]*(\d+\.?\d*)%?",
        r"stromal TILs?[\s:]*(\d+\.?\d*)%?",
    ],
    "ONCOTYPE_SCORE": [
        r"[Oo]ncotype\s+DX[\s:]*(\d+)\b",
        r"[Rr]ecurrence [Ss]core[\s:]*(\d+)\b",
    ],
}

# Normalisation mappings
_NORM: dict[str, str] = {
    "positive": "Positive", "pos": "Positive", "+": "Positive",
    "negative": "Negative", "neg": "Negative", "-": "Negative",
    "equivocal": "Equivocal", "amplified": "Positive",
    "not amplified": "Negative", "not detected": "Negative",
    "detected": "Positive", "pathogenic": "Positive",
}


def _normalise(val: str) -> str:
    return _NORM.get(val.strip().lower(), val.strip())


def _extract_field(field: str, text: str) -> list[dict[str, Any]]:
    results = []
    for pattern in PATTERNS.get(field, []):
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = " ".join(g for g in match.groups() if g)
            value = _normalise(raw)
            # Source sentence
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            source = text[start:end].strip().replace("\n", " ")

            # Confidence based on specificity of pattern
            confidence = 0.95 if field in ("TUMOUR_SIZE", "KI67_VALUE", "ONCOTYPE_SCORE") else 0.85
            if "%" in pattern or "Score" in pattern:
                confidence = 0.90

            results.append({
                "field": field,
                "value": value,
                "confidence": confidence,
                "source_text": source,
            })
            break  # First match per pattern

    return results


def extract_from_text(text: str, confidence_threshold: float = 0.75) -> dict[str, Any]:
    """
    Main extraction entry point.
    Returns:
        {
          "extracted": {field: {value, confidence, source_text}},
          "needs_review": [field names below threshold],
          "overall_confidence": float
        }
    """
    extracted: dict[str, dict] = {}
    needs_review: list[str] = []

    for field in PATTERNS:
        candidates = _extract_field(field, text)
        if candidates:
            # Take highest confidence candidate
            best = max(candidates, key=lambda x: x["confidence"])
            extracted[field] = {
                "value": best["value"],
                "confidence": best["confidence"],
                "source_text": best["source_text"],
            }
            if best["confidence"] < confidence_threshold:
                needs_review.append(field)

    overall = (
        sum(v["confidence"] for v in extracted.values()) / len(extracted)
        if extracted else 0.0
    )

    return {
        "extracted": extracted,
        "needs_review": needs_review,
        "overall_confidence": round(overall, 3),
    }


def map_to_clinical_fields(extraction: dict) -> dict[str, Any]:
    """
    Maps extracted NLP entities back to ClinicalData field names.
    """
    ex = extraction.get("extracted", {})
    mapped: dict[str, Any] = {}

    def val(field: str) -> str | None:
        return ex[field]["value"] if field in ex else None

    if v := val("ER_STATUS"):
        mapped["er_status"] = v
    if v := val("PR_STATUS"):
        mapped["pr_status"] = v
    if v := val("HER2_STATUS"):
        mapped["her2_status"] = v
    if v := val("KI67_VALUE"):
        try:
            mapped["ki67_percent"] = float(re.sub(r"[^0-9.]", "", v))
        except ValueError:
            pass
    if v := val("TUMOUR_SIZE"):
        try:
            # Normalise mm to cm
            parts = v.split()
            num = float(parts[0])
            unit = parts[1].lower() if len(parts) > 1 else "cm"
            mapped["tumour_size"] = round(num / 10 if unit == "mm" else num, 2)
        except (ValueError, IndexError):
            pass
    if v := val("TNM_STAGE"):
        mapped["stage"] = v
    if v := val("GRADE"):
        grade_map = {"well differentiated": 1, "moderately differentiated": 2, "poorly differentiated": 3}
        mapped["grade"] = grade_map.get(v.lower(), v)
    if v := val("HISTOLOGY"):
        mapped["histological_type"] = v
    if v := val("PD_L1"):
        mapped["pdl1_status"] = v
    if v := val("BRCA_STATUS"):
        # Try to identify BRCA1 vs BRCA2
        if "BRCA1" in ex.get("BRCA_STATUS", {}).get("source_text", ""):
            mapped["brca1_status"] = v
        elif "BRCA2" in ex.get("BRCA_STATUS", {}).get("source_text", ""):
            mapped["brca2_status"] = v
    if v := val("TILS"):
        try:
            mapped["tils_percent"] = float(re.sub(r"[^0-9.]", "", v))
        except ValueError:
            pass
    if v := val("ONCOTYPE_SCORE"):
        try:
            mapped["oncotype_dx_score"] = float(v)
        except ValueError:
            pass
    if v := val("LYMPH_NODES"):
        mapped["lymph_nodes_involved"] = "positive" in v.lower()

    return mapped
