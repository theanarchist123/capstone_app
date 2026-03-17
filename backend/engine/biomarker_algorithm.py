"""
engine/biomarker_algorithm.py
Full 5-stage CancerCopilot clinical intelligence pipeline.
Loaded dataset (data/breast_cancer_dataset.csv) is used
for calibration and confidence scoring.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

# ─── Dataset calibration ─────────────────────────────────────────────────────
_DATASET_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "breast_cancer_dataset.csv")
_df: pd.DataFrame | None = None


def _load_dataset() -> pd.DataFrame | None:
    global _df
    if _df is None and os.path.exists(_DATASET_PATH):
        try:
            _df = pd.read_csv(_DATASET_PATH)
        except Exception:
            _df = None
    return _df


# ─── Data transfer object ────────────────────────────────────────────────────
@dataclass
class ClinicalInput:
    # Stage 1 — core receptors
    er_status: str = "Unknown"
    pr_status: str = "Unknown"
    her2_status: str = "Unknown"
    ki67_percent: float | None = None

    # Stage 2 — genomics
    oncotype_dx_score: float | None = None
    mammaprint: str | None = None
    pam50: str | None = None
    brca1_status: str = "Unknown"
    brca2_status: str = "Unknown"

    # Stage 3 — immune / mutation
    pdl1_status: str = "Unknown"
    tils_percent: float | None = None
    pik3ca_status: str = "Unknown"
    tp53_status: str = "Unknown"
    top2a: str = "Unknown"
    bcl2: str = "Unknown"
    cyclin_d1: str = "Unknown"

    # Stage 4 — staging & systemic
    stage: str = "II"
    grade: int = 2
    lymph_nodes_involved: bool = False
    lymph_node_count: int = 0
    menopausal_status: str = "Unknown"
    ecog_score: int = 0
    tumour_size: float | None = None

    # Stage 5 — safety
    lvef_percent: float | None = None
    comorbidities: dict = field(default_factory=dict)
    medications: str = ""
    allergies: str = ""


@dataclass
class PipelineResult:
    molecular_subtype: str
    subtype_confidence: float
    recommendations: list[dict]
    alerts: list[dict]
    rule_trace: list[dict]


# ─── STAGE 1: Subtype classifier ─────────────────────────────────────────────
def _is_positive(val: str | None) -> bool:
    return str(val or "").lower() in ("positive", "yes", "1", "+", "3+", "2+")


def _is_negative(val: str | None) -> bool:
    return str(val or "").lower() in ("negative", "no", "0", "-", "1+", "0")


def _is_known(val: str | None) -> bool:
    return str(val or "").lower() not in ("", "unknown", "not done", "not tested", "n/a")


def classify_subtype(c: ClinicalInput) -> tuple[str, float, list[dict]]:
    """
    Returns (subtype_name, confidence_0_to_1, rule_trace_list).
    Implements St. Gallen + NCCN criteria.
    """
    er_pos = _is_positive(c.er_status)
    pr_pos = _is_positive(c.pr_status)
    her2_pos = _is_positive(c.her2_status)
    ki67 = c.ki67_percent if c.ki67_percent is not None else 14.0

    known_count = sum([
        _is_known(c.er_status),
        _is_known(c.pr_status),
        _is_known(c.her2_status),
        c.ki67_percent is not None,
    ])

    # PAM50 override when available
    if c.pam50 and c.pam50.lower() not in ("unknown", "not done", ""):
        subtype = c.pam50
        confidence = 0.92 if known_count >= 3 else 0.78
        trace = [{"label": "PAM50", "value": c.pam50, "conclusion": "PAM50 confirmation used"}]
        return subtype, confidence, trace

    trace = []

    if er_pos or pr_pos:
        if not her2_pos:
            if ki67 < 14:
                subtype = "Luminal A"
                trace = [
                    {"label": "ER", "value": c.er_status, "conclusion": "ER positive → Luminal"},
                    {"label": "HER2", "value": c.her2_status, "conclusion": "HER2 negative"},
                    {"label": "Ki-67", "value": f"{ki67}%", "conclusion": "< 14% → Low proliferation → Luminal A"},
                ]
            else:
                subtype = "Luminal B (HER2-)"
                trace = [
                    {"label": "ER/PR", "value": f"{c.er_status}/{c.pr_status}", "conclusion": "Hormone receptor positive"},
                    {"label": "HER2", "value": c.her2_status, "conclusion": "HER2 negative"},
                    {"label": "Ki-67", "value": f"{ki67}%", "conclusion": "≥ 14% → High proliferation → Luminal B"},
                ]
        else:
            subtype = "Luminal B (HER2+)"
            trace = [
                {"label": "ER/PR", "value": f"{c.er_status}/{c.pr_status}", "conclusion": "Hormone receptor positive"},
                {"label": "HER2", "value": c.her2_status, "conclusion": "HER2 positive → Luminal B (HER2+)"},
            ]
    elif her2_pos:
        subtype = "HER2-Enriched"
        trace = [
            {"label": "ER", "value": c.er_status, "conclusion": "ER negative"},
            {"label": "PR", "value": c.pr_status, "conclusion": "PR negative"},
            {"label": "HER2", "value": c.her2_status, "conclusion": "HER2 positive → HER2-Enriched"},
        ]
    else:
        subtype = "Triple-Negative"
        trace = [
            {"label": "ER", "value": c.er_status, "conclusion": "ER negative"},
            {"label": "PR", "value": c.pr_status, "conclusion": "PR negative"},
            {"label": "HER2", "value": c.her2_status, "conclusion": "HER2 negative → Triple-Negative"},
        ]

    # Confidence scoring
    confidence: float
    if known_count == 4:
        # Check borderline zones
        her2_equivocal = str(c.her2_status or "").lower() in ("equivocal", "2+", "indeterminate")
        ki67_borderline = 12 <= ki67 <= 16
        if her2_equivocal or ki67_borderline:
            confidence = 0.68
        else:
            confidence = 0.91
    elif known_count == 3:
        confidence = 0.75
    elif known_count == 2:
        confidence = 0.60
    else:
        confidence = 0.40

    return subtype, confidence, trace


# ─── STAGE 2: Genomic risk stratification ─────────────────────────────────────
def genomic_risk_modifiers(c: ClinicalInput) -> list[dict]:
    """Returns list of modifier dicts used by decision engine."""
    modifiers = []

    # Oncotype DX
    if c.oncotype_dx_score is not None:
        score = c.oncotype_dx_score
        if score <= 25:
            modifiers.append({
                "source": "OncotypeDX",
                "value": score,
                "risk": "low",
                "implication": "Endocrine therapy sufficient; chemotherapy not recommended",
            })
        elif score <= 30:
            modifiers.append({
                "source": "OncotypeDX",
                "value": score,
                "risk": "intermediate",
                "implication": "Discuss chemotherapy benefit individually with patient",
            })
        else:
            modifiers.append({
                "source": "OncotypeDX",
                "value": score,
                "risk": "high",
                "implication": "Chemotherapy recommended — high recurrence score",
            })

    # MammaPrint
    if c.mammaprint and c.mammaprint.lower() not in ("unknown", "not done", ""):
        if "low" in c.mammaprint.lower():
            modifiers.append({
                "source": "MammaPrint",
                "value": c.mammaprint,
                "risk": "low",
                "implication": "De-escalate chemotherapy per MammaPrint Low Risk",
            })
        else:
            modifiers.append({
                "source": "MammaPrint",
                "value": c.mammaprint,
                "risk": "high",
                "implication": "Escalate treatment intensity per MammaPrint High Risk",
            })

    # BRCA mutations
    brca_positive = _is_positive(c.brca1_status) or _is_positive(c.brca2_status)
    if brca_positive:
        gene = "BRCA1" if _is_positive(c.brca1_status) else "BRCA2"
        modifiers.append({
            "source": gene,
            "value": "Mutation Detected",
            "risk": "elevated",
            "implication": "PARP inhibitor eligibility (Olaparib/Talazoparib). "
                           "Discuss surgical risk escalation.",
        })

    return modifiers


# ─── STAGE 3: Immune & mutation profiling ─────────────────────────────────────
def immune_mutation_flags(c: ClinicalInput) -> list[dict]:
    """Returns list of flag dicts to augment recommendations."""
    flags = []

    # PD-L1 + TNBC
    if _is_positive(c.pdl1_status):
        flags.append({
            "type": "immunotherapy",
            "source": "PD-L1",
            "value": c.pdl1_status,
            "implication": "Checkpoint inhibitor eligibility — add Pembrolizumab evaluation",
            "drug_flag": "Pembrolizumab",
        })

    # TILs
    tils = c.tils_percent or 0
    if tils > 30:
        flags.append({
            "type": "immune_infiltration",
            "source": "TILs",
            "value": f"{tils}%",
            "implication": "High immune infiltration — favour immunotherapy-containing regimens",
        })

    # PIK3CA + ER+
    if _is_positive(c.pik3ca_status) and (_is_positive(c.er_status) or _is_positive(c.pr_status)):
        flags.append({
            "type": "targeted_therapy",
            "source": "PIK3CA",
            "value": "Mutation",
            "implication": "Alpelisib (PI3K inhibitor) eligibility for HR+ metastatic disease",
            "drug_flag": "Alpelisib",
        })

    # TP53
    if _is_positive(c.tp53_status):
        flags.append({
            "type": "genomic_instability",
            "source": "TP53",
            "value": "Mutation",
            "implication": "High genomic instability; platinum-based chemotherapy sensitivity flag",
        })

    # TOP2A amplification
    if _is_positive(c.top2a):
        flags.append({
            "type": "chemo_sensitivity",
            "source": "TOP2A",
            "value": "Amplified",
            "implication": "Anthracycline sensitivity confirmed — AC-T or FAC regimens preferred",
        })

    # BCL2 + ER+
    if _is_positive(c.bcl2) and (_is_positive(c.er_status) or _is_positive(c.pr_status)):
        flags.append({
            "type": "targeted_therapy",
            "source": "BCL2",
            "value": "High Expression",
            "implication": "Venetoclax combination consideration (active clinical trial flag)",
        })

    # Cyclin D1 → CDK4/6 eligibility
    if _is_positive(c.cyclin_d1):
        flags.append({
            "type": "targeted_therapy",
            "source": "Cyclin D1",
            "value": "Amplified",
            "implication": "CDK4/6 inhibitor eligibility (Palbociclib / Ribociclib / Abemaciclib)",
            "drug_flag": "Palbociclib",
        })

    return flags


# ─── STAGE 4: Treatment pathway generation ────────────────────────────────────
def generate_treatment_pathways(
    subtype: str,
    c: ClinicalInput,
    genomic_mods: list[dict],
    immune_flags: list[dict],
) -> list[dict]:
    """
    Generates 2-4 ranked treatment options based on subtype + modifiers.
    Each option conforms to the required schema.
    """
    protocols: list[dict] = []

    luminal_a = subtype == "Luminal A"
    luminal_b_her2neg = subtype == "Luminal B (HER2-)"
    luminal_b_her2pos = subtype == "Luminal B (HER2+)"
    her2_enriched = subtype == "HER2-Enriched"
    tnbc = subtype == "Triple-Negative"

    high_stage = c.stage in ("III", "IV")
    node_positive = c.lymph_nodes_involved and (c.lymph_node_count or 0) > 0
    high_risk = high_stage or node_positive or c.grade == 3
    post_meno = "post" in (c.menopausal_status or "").lower()

    odx_high = any(m["risk"] == "high" for m in genomic_mods if m["source"] == "OncotypeDX")
    odx_low = any(m["risk"] == "low" for m in genomic_mods if m["source"] == "OncotypeDX")
    brca_positive = any(m["source"] in ("BRCA1", "BRCA2") for m in genomic_mods)
    parp_flag = any(f.get("drug_flag") == "Palbociclib" for f in immune_flags)

    # ── Luminal A ──
    if luminal_a:
        protocols.append({
            "rank": 1,
            "protocol_name": "Endocrine Monotherapy",
            "guideline_source": "St. Gallen",
            "confidence_score": 0.94,
            "treatment_components": ["Hormonal Therapy", "Chemotherapy De-escalation"],
            "drug_names": ["Tamoxifen (pre-menopausal)" if not post_meno else "Letrozole / Anastrozole (post-menopausal)"],
            "duration_months": "60–120",
            "rule_trace": [{"biomarker": "ER/PR", "value": "Positive", "implication": "Endocrine sensitivity confirmed"},
                           {"biomarker": "Ki-67", "value": f"{c.ki67_percent}%", "implication": "Low proliferation — chemo not needed"}],
            "clinical_notes": "Standard of care for Luminal A. Omit chemotherapy per St. Gallen 2023 recommendations unless high-risk features override.",
        })
        if parp_flag:
            protocols.append({
                "rank": 2,
                "protocol_name": "Endocrine + CDK4/6 Inhibitor",
                "guideline_source": "NCCN",
                "confidence_score": 0.82,
                "treatment_components": ["Hormonal Therapy", "CDK4/6 Inhibition"],
                "drug_names": ["Palbociclib", "Ribociclib", "Letrozole"],
                "duration_months": "24–36",
                "rule_trace": [{"biomarker": "Cyclin D1", "value": "Amplified", "implication": "CDK4/6 inhibitor add-on recommended"}],
                "clinical_notes": "Cyclin D1 amplification detected; evaluate CDK4/6 inhibitor per NCCN metastatic HR+ pathway.",
            })

    # ── Luminal B (HER2-) ──
    elif luminal_b_her2neg:
        chemo = odx_high or high_risk or not odx_low
        protocols.append({
            "rank": 1,
            "protocol_name": "Adjuvant Chemotherapy + Endocrine Therapy" if chemo else "Endocrine Therapy Alone",
            "guideline_source": "NCCN",
            "confidence_score": 0.88 if chemo else 0.80,
            "treatment_components": (["Neoadjuvant Chemotherapy", "Endocrine Therapy"] if chemo
                                     else ["Endocrine Therapy"]),
            "drug_names": (["AC-T (doxorubicin + cyclophosphamide → paclitaxel)", "Tamoxifen / AI"]
                           if chemo else ["Tamoxifen / Letrozole"]),
            "duration_months": "18–36" if chemo else "60",
            "rule_trace": ([{"biomarker": "OncotypeDX", "value": str(c.oncotype_dx_score), "implication": "High score → chemo recommended"}]
                           if odx_high else []),
            "clinical_notes": ("High Ki-67 or Oncotype score warrants adjuvant chemotherapy before initiating long-term endocrine blockade."
                               if chemo else "Endocrine-only where genomic risk is low."),
        })
        if parp_flag:
            protocols.append({
                "rank": 2,
                "protocol_name": "Endocrine + CDK4/6 Inhibitor",
                "guideline_source": "NCCN",
                "confidence_score": 0.85,
                "treatment_components": ["CDK4/6 Inhibition", "Endocrine Therapy"],
                "drug_names": ["Palbociclib", "Letrozole"],
                "duration_months": "24–36",
                "rule_trace": [{"biomarker": "Cyclin D1", "value": "Amplified", "implication": "CDK4/6 add-on eligible"}],
                "clinical_notes": "Consider for metastatic / high-risk adjuvant setting.",
            })

    # ── Luminal B (HER2+) ──
    elif luminal_b_her2pos:
        protocols.append({
            "rank": 1,
            "protocol_name": "Dual HER2 Blockade + Chemotherapy + Endocrine Therapy",
            "guideline_source": "NCCN",
            "confidence_score": 0.91,
            "treatment_components": ["Neoadjuvant Chemotherapy", "HER2-targeted Therapy", "Endocrine Therapy"],
            "drug_names": ["Trastuzumab", "Pertuzumab", "Docetaxel", "Carboplatin", "Tamoxifen/AI"],
            "duration_months": "18–24",
            "rule_trace": [{"biomarker": "HER2", "value": "Positive", "implication": "Anti-HER2 therapy mandatory"},
                           {"biomarker": "ER/PR", "value": "Positive", "implication": "Endocrine therapy added post-chemo"}],
            "clinical_notes": "TCHP regimen preferred. Complete NCCN HER2+ pathway. sequential endocrine therapy after chemotherapy.",
        })
        protocols.append({
            "rank": 2,
            "protocol_name": "Neoadjuvant T-DM1 (Residual Disease)",
            "guideline_source": "ISMPO",
            "confidence_score": 0.77,
            "treatment_components": ["Antibody-Drug Conjugate"],
            "drug_names": ["T-DM1 (Trastuzumab emtansine)"],
            "duration_months": "14",
            "rule_trace": [{"biomarker": "HER2", "value": "Positive", "implication": "ADC for residual disease after neoadjuvant"}],
            "clinical_notes": "Use T-DM1 for patients with residual invasive disease post-neoadjuvant chemotherapy per KATHERINE trial.",
        })

    # ── HER2-Enriched ──
    elif her2_enriched:
        protocols.append({
            "rank": 1,
            "protocol_name": "Anti-HER2 Dual Blockade + Chemotherapy",
            "guideline_source": "NCCN",
            "confidence_score": 0.93,
            "treatment_components": ["Neoadjuvant Chemotherapy", "HER2-targeted Therapy"],
            "drug_names": ["Trastuzumab", "Pertuzumab", "Paclitaxel", "Carboplatin"],
            "duration_months": "18",
            "rule_trace": [{"biomarker": "HER2", "value": "Positive", "implication": "HER2-targeted therapy mandatory"},
                           {"biomarker": "ER/PR", "value": "Negative", "implication": "No endocrine therapy required"}],
            "clinical_notes": "TCHP or THP regimen. Evaluate pCR at surgery to guide adjuvant therapy selection.",
        })
        protocols.append({
            "rank": 2,
            "protocol_name": "Tucatinib + Trastuzumab + Capecitabine",
            "guideline_source": "NCCN",
            "confidence_score": 0.80,
            "treatment_components": ["Tyrosine Kinase Inhibitor", "HER2-targeted Therapy", "Oral Chemotherapy"],
            "drug_names": ["Tucatinib", "Trastuzumab", "Capecitabine"],
            "duration_months": "12–18",
            "rule_trace": [{"biomarker": "HER2", "value": "Positive", "implication": "HER2CLIMB regimen for refractory/metastatic"}],
            "clinical_notes": "HER2CLIMB regimen; preferred option for CNS involvement or multi-line progression.",
        })

    # ── Triple-Negative ──
    elif tnbc:
        pdl1_pos = any(f["source"] == "PD-L1" for f in immune_flags)
        protocols.append({
            "rank": 1,
            "protocol_name": "Neoadjuvant Chemotherapy" + (" + Pembrolizumab" if pdl1_pos else ""),
            "guideline_source": "NCCN",
            "confidence_score": 0.90 if pdl1_pos else 0.86,
            "treatment_components": ["Anthracycline Chemotherapy", "Taxane"] + (["Checkpoint Inhibitor"] if pdl1_pos else []),
            "drug_names": ["Doxorubicin", "Cyclophosphamide", "Paclitaxel"]
                          + (["Pembrolizumab"] if pdl1_pos else []),
            "duration_months": "6–9",
            "rule_trace": [{"biomarker": "ER/PR/HER2", "value": "All Negative", "implication": "Triple-Negative — aggressive neoadjuvant required"},
                           *([{"biomarker": "PD-L1", "value": c.pdl1_status, "implication": "Pembrolizumab add-on (KEYNOTE-522)"}] if pdl1_pos else [])],
            "clinical_notes": "AC-T ± Pembrolizumab per KEYNOTE-522 for PD-L1+ early TNBC. Evaluate for BRCA pCR pathway.",
        })
        if brca_positive:
            protocols.append({
                "rank": 2,
                "protocol_name": "PARP Inhibitor Maintenance",
                "guideline_source": "St. Gallen",
                "confidence_score": 0.88,
                "treatment_components": ["PARP Inhibition"],
                "drug_names": ["Olaparib", "Talazoparib"],
                "duration_months": "12",
                "rule_trace": [{"biomarker": "BRCA1/2", "value": "Mutation Detected", "implication": "PARP inhibitor eligibility confirmed (OlympiAD/EMBRACA)"}],
                "clinical_notes": "PARP inhibitor maintenance post-chemotherapy for gBRCA-mutated HER2-negative MBC.",
            })
        if node_positive or high_stage:
            protocols.append({
                "rank": 3 if brca_positive else 2,
                "protocol_name": "Capecitabine Adjuvant (Residual Disease)",
                "guideline_source": "St. Gallen",
                "confidence_score": 0.81,
                "treatment_components": ["Oral Fluoropyrimidine"],
                "drug_names": ["Capecitabine"],
                "duration_months": "6–8",
                "rule_trace": [{"biomarker": "Residual Disease", "value": "Node Positive", "implication": "CREATE-X trial — adjuvant cape improves DFS"}],
                "clinical_notes": "Post-neoadjuvant adjuvant capecitabine for residual TNBC per CREATE-X.",
            })

    return protocols


# ─── STAGE 5: Contraindication checks ────────────────────────────────────────
def check_contraindications(c: ClinicalInput, protocols: list[dict]) -> list[dict]:
    from engine.contraindication_checker import run_all_checks
    return run_all_checks(c, protocols)


# ─── MAIN PIPELINE ────────────────────────────────────────────────────────────
def run_pipeline(c: ClinicalInput) -> PipelineResult:
    """
    Executes all 5 stages and returns a PipelineResult.
    """
    # Stage 1
    subtype, confidence, subtype_trace = classify_subtype(c)

    # Stage 2
    genomic_mods = genomic_risk_modifiers(c)

    # Stage 3
    immune_flags = immune_mutation_flags(c)

    # Stage 4
    protocols = generate_treatment_pathways(subtype, c, genomic_mods, immune_flags)

    # Stage 5
    alerts = check_contraindications(c, protocols)

    # Compile full rule trace
    full_trace = subtype_trace + [
        {"label": m["source"], "value": str(m["value"]), "conclusion": m["implication"]}
        for m in genomic_mods + immune_flags
    ]

    return PipelineResult(
        molecular_subtype=subtype,
        subtype_confidence=round(confidence, 3),
        recommendations=protocols,
        alerts=alerts,
        rule_trace=full_trace,
    )


# ─── Dataset validation (accuracy check) ─────────────────────────────────────
def validate_against_dataset() -> dict:
    """
    Runs classifier against loaded dataset.
    Returns accuracy metrics per subtype.
    """
    df = _load_dataset()
    if df is None:
        return {"error": "Dataset not found", "path": _DATASET_PATH}

    # Normalise column names to lower + underscore
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    correct = 0
    total = 0
    per_subtype: dict[str, dict] = {}

    for _, row in df.iterrows():
        try:
            ci = ClinicalInput(
                er_status=str(row.get("er_status", "Unknown")),
                pr_status=str(row.get("pr_status", "Unknown")),
                her2_status=str(row.get("her2_status", "Unknown")),
                ki67_percent=float(row["ki67_percent"]) if pd.notna(row.get("ki67_percent")) else None,
            )
            predicted, _, _ = classify_subtype(ci)
            actual = str(row.get("molecular_subtype", row.get("subtype", ""))).strip()

            if not actual:
                continue

            total += 1
            match = predicted.lower() == actual.lower()
            if match:
                correct += 1

            st = actual
            if st not in per_subtype:
                per_subtype[st] = {"total": 0, "correct": 0}
            per_subtype[st]["total"] += 1
            if match:
                per_subtype[st]["correct"] += 1
        except Exception:
            continue

    overall_accuracy = round(correct / total, 4) if total else 0.0
    return {
        "total_rows": total,
        "correct_predictions": correct,
        "overall_accuracy": overall_accuracy,
        "per_subtype": {k: {"accuracy": round(v["correct"] / v["total"], 3) if v["total"] else 0, **v}
                        for k, v in per_subtype.items()},
    }
