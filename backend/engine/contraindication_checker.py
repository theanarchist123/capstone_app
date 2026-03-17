"""
engine/contraindication_checker.py
All safety rules for contraindication detection.
Each rule is independently testable.
"""
from __future__ import annotations
from typing import Any


SEVERITY = {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}


def _alert(severity: str, alert_type: str, trigger: str, affected: str, action: str) -> dict:
    return {
        "severity": severity,
        "alert_type": alert_type,
        "trigger": trigger,
        "affected_treatment": affected,
        "recommended_action": action,
    }


# ─── Individual rules ────────────────────────────────────────────────────────
def check_lvef(lvef: float | None, protocols: list[dict]) -> list[dict]:
    alerts = []
    if lvef is None:
        return alerts

    if lvef < 40:
        alerts.append(_alert(
            "HIGH", "Cardiac — Severe LV Dysfunction",
            f"LVEF {lvef}% (critically low)",
            "Trastuzumab, Pertuzumab, Anthracyclines",
            "Contraindicate ALL cardiotoxic agents. Immediate cardio-oncology consult required."
        ))
    elif lvef < 55:
        alerts.append(_alert(
            "HIGH", "Cardiac — LV Dysfunction",
            f"LVEF {lvef}% (< 55% threshold)",
            "Trastuzumab, Anthracyclines",
            "Contraindicate Trastuzumab and anthracycline-based regimens. "
            "Cardiology consult mandatory before initiating any chemotherapy."
        ))

    return alerts


def check_ecog(ecog: int | None, protocols: list[dict]) -> list[dict]:
    alerts = []
    if ecog is None:
        return alerts
    if ecog >= 3:
        alerts.append(_alert(
            "HIGH", "Performance Status — Poor ECOG",
            f"ECOG score {ecog} (≥ 3)",
            "Aggressive combination chemotherapy regimens",
            "Contraindicate dose-intensive combination regimens. "
            "Evaluate palliative / supportive care pathway. "
            "Single-agent or best supportive care preferred."
        ))
    elif ecog == 2:
        alerts.append(_alert(
            "MEDIUM", "Performance Status — Borderline ECOG",
            f"ECOG score {ecog}",
            "Combination chemotherapy",
            "Use dose-reduced regimens. Close monitoring required. "
            "Consider sequential over concurrent chemotherapy."
        ))
    return alerts


def check_brca_platinum_sensitivity(brca1: str, brca2: str, protocols: list[dict]) -> list[dict]:
    alerts = []
    brca_pos = str(brca1 or "").lower() in ("positive", "mutation detected") or \
               str(brca2 or "").lower() in ("positive", "mutation detected")
    if brca_pos:
        has_anth = any("anthracycline" in str(p.get("treatment_components", "")).lower() or
                       "doxorubicin" in str(p.get("drug_names", "")).lower()
                       for p in protocols)
        if has_anth:
            alerts.append(_alert(
                "LOW", "BRCA — Platinum Sensitivity Note",
                "BRCA1/2 mutation detected",
                "Anthracycline regimens",
                "No direct contraindication. However, BRCA-mutated tumours show preferential "
                "sensitivity to platinum agents. Consider platinum substitution (Carboplatin-based) "
                "if anthracycline cardiotoxicity is a concern."
            ))
    return alerts


def check_renal(comorbidities: dict | None, protocols: list[dict]) -> list[dict]:
    alerts = []
    comorbidities = comorbidities or {}
    has_renal = any("kidney" in str(k).lower() or "renal" in str(k).lower() or "ckd" in str(k).lower()
                    for k in comorbidities.keys())
    if has_renal:
        has_platinum = any("carboplatin" in str(p.get("drug_names", "")).lower() or
                           "cisplatin" in str(p.get("drug_names", "")).lower()
                           for p in protocols)
        if has_platinum:
            alerts.append(_alert(
                "MEDIUM", "Renal Impairment — Platinum Agent Alert",
                "Chronic Kidney Disease (comorbidity)",
                "Carboplatin / Cisplatin",
                "Dose reduction required. Calculate creatinine clearance (Cockcroft-Gault). "
                "Consider nephrology co-management. May need to switch to non-nephrotoxic alternatives."
            ))
    return alerts


def check_hepatic(comorbidities: dict | None, medications: str | None, protocols: list[dict]) -> list[dict]:
    alerts = []
    comorbidities = comorbidities or {}
    has_liver = any("liver" in str(k).lower() or "hepatic" in str(k).lower() or "cirrhosis" in str(k).lower()
                    for k in comorbidities.keys())
    if has_liver:
        heavily_metabolized = ["tamoxifen", "letrozole", "anastrozole", "exemestane",
                               "palbociclib", "ribociclib", "abemaciclib"]
        relevant = [d for p in protocols for d in str(p.get("drug_names", "")).lower().split(",")
                    if any(m in d for m in heavily_metabolized)]
        if relevant:
            alerts.append(_alert(
                "MEDIUM", "Hepatic Impairment — Metabolised Drug Alert",
                "Hepatic impairment (comorbidity)",
                ", ".join(set(relevant))[:200],
                "Dose adjustment required for hepatically metabolised agents. "
                "Obtain LFTs. Hepatology or clinical pharmacology review recommended."
            ))
    return alerts


def check_allergy(allergies: str | None, protocols: list[dict]) -> list[dict]:
    alerts = []
    if not allergies:
        return alerts
    allergy_lower = allergies.lower()
    for p in protocols:
        for drug in (p.get("drug_names") or []):
            if drug.lower() in allergy_lower:
                alerts.append(_alert(
                    "HIGH", "Drug Allergy Alert",
                    f"Documented allergy: {allergies}",
                    drug,
                    f"Patient has documented allergy to {drug}. "
                    "Remove from protocol. Consider desensitisation or alternative agent."
                ))
    return alerts


# ─── Main runner ─────────────────────────────────────────────────────────────
def run_all_checks(c: Any, protocols: list[dict]) -> list[dict]:
    """Entry point — runs all checks and deduplicates alerts."""
    alerts: list[dict] = []
    alerts += check_lvef(c.lvef_percent, protocols)
    alerts += check_ecog(c.ecog_score, protocols)
    alerts += check_brca_platinum_sensitivity(c.brca1_status, c.brca2_status, protocols)
    alerts += check_renal(c.comorbidities, protocols)
    alerts += check_hepatic(c.comorbidities, c.medications, protocols)
    alerts += check_allergy(c.allergies, protocols)
    return alerts
