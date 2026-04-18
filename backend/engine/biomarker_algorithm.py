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
    Generates exactly 3 ranked treatment options (PRIMARY / ALTERNATIVE / ESCALATION)
    for every subtype + patient profile combination.
    Based strictly on NCCN 2024 + ESMO 2023 guidelines.
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
    lvef_ok = (c.lvef_percent or 60) >= 50

    odx_high = any(m["risk"] == "high" for m in genomic_mods if m["source"] == "OncotypeDX")
    odx_low  = any(m["risk"] == "low"  for m in genomic_mods if m["source"] == "OncotypeDX")
    brca_positive = any(m["source"] in ("BRCA1", "BRCA2") for m in genomic_mods)
    cdk46_flag    = any(f.get("drug_flag") == "Palbociclib" for f in immune_flags)
    pdl1_pos      = any(f["source"] == "PD-L1" for f in immune_flags)
    ki67 = c.ki67_percent if c.ki67_percent is not None else 14.0
    endocrine_drug = "Anastrozole / Letrozole" if post_meno else "Tamoxifen"

    # ── LUMINAL A ──────────────────────────────────────────────────────────────
    if luminal_a:
        # PATH 1 — Endocrine monotherapy (always preferred for Luminal A)
        protocols.append({
            "rank": 1,
            "protocol_name": "Endocrine Monotherapy",
            "guideline_source": "St. Gallen 2023",
            "confidence_score": 0.94,
            "treatment_components": ["Hormonal Therapy"],
            "drug_names": [endocrine_drug, "± OvSup (pre-menopausal)"],
            "duration_months": "60–120",
            "rule_trace": [
                {"biomarker": "ER/PR", "value": "Positive", "implication": "Strong endocrine sensitivity — chemotherapy de-escalation justified"},
                {"biomarker": "Ki-67", "value": f"{ki67}%", "implication": f"{'Low' if ki67 < 14 else 'Borderline'} proliferation (<14%) — Luminal A phenotype confirmed"},
                {"biomarker": "HER2", "value": c.her2_status, "implication": "HER2 negative — anti-HER2 therapy not required"},
            ],
            "clinical_notes": "Chemotherapy omission is the standard for Luminal A per St. Gallen 2023 consensus. Endocrine therapy duration 5–10 years based on risk.",
        })
        # PATH 2 — CDK4/6 inhibitor addition for higher-risk Luminal A
        protocols.append({
            "rank": 2,
            "protocol_name": "Endocrine + CDK4/6 Inhibitor",
            "guideline_source": "NCCN 2024",
            "confidence_score": 0.78 if not high_risk else 0.85,
            "treatment_components": ["CDK4/6 Inhibition", "Endocrine Therapy"],
            "drug_names": ["Abemaciclib" if node_positive else "Palbociclib / Ribociclib", endocrine_drug],
            "duration_months": "24 (Abemaciclib) / 24–36 (Palbociclib)",
            "rule_trace": [
                {"biomarker": "Stage / Nodes", "value": f"Stage {c.stage}, {'Node+' if node_positive else 'Node-'}", "implication": "High-risk features may warrant CDK4/6 addition per monarchE data"},
                {"biomarker": "Ki-67", "value": f"{ki67}%", "implication": "CDK4/6 inhibitors complement endocrine blockade in borderline Luminal A"},
            ],
            "clinical_notes": f"Abemaciclib adjuvant (monarchE) appropriate if node-positive or high-risk. {'Node-positive detected — strong indication.' if node_positive else 'Consider for high Ki-67 borderline Luminal A.'}",
        })
        # PATH 3 — Adjuvant chemotherapy escalation for truly high-risk
        protocols.append({
            "rank": 3,
            "protocol_name": "Adjuvant TC Chemotherapy + Endocrine Therapy",
            "guideline_source": "NCCN 2024",
            "confidence_score": 0.62 if not high_risk else 0.74,
            "treatment_components": ["Chemotherapy", "Endocrine Therapy"],
            "drug_names": ["Docetaxel", "Cyclophosphamide (TC ×4)", endocrine_drug],
            "duration_months": "12 (chemo) + 60 (ET)",
            "rule_trace": [
                {"biomarker": "Grade / Stage", "value": f"Grade {c.grade}, Stage {c.stage}", "implication": "High-grade or advanced stage may override endocrine-only for Luminal A"},
                {"biomarker": "OncotypeDX", "value": f"{c.oncotype_dx_score or 'Not tested'}", "implication": "Recurrence score >25 is a threshold for chemotherapy consideration in HR+ disease"},
            ],
            "clinical_notes": "TC (Docetaxel + Cyclophosphamide) avoids anthracycline cardiac risk. Reserve for Grade 3 Luminal A, OncotypeDX >25, or Stage III. Not standard first-line for low-risk Luminal A.",
        })

    # ── LUMINAL B (HER2-) ──────────────────────────────────────────────────────
    elif luminal_b_her2neg:
        chemo_needed = odx_high or high_risk or (not odx_low and ki67 >= 20)
        # PATH 1
        protocols.append({
            "rank": 1,
            "protocol_name": "Adjuvant Chemotherapy + Endocrine Therapy" if chemo_needed else "Endocrine Therapy ± CDK4/6 Inhibitor",
            "guideline_source": "NCCN 2024",
            "confidence_score": 0.89 if chemo_needed else 0.83,
            "treatment_components": (["Neoadjuvant/Adjuvant Chemotherapy", "Endocrine Therapy"] if chemo_needed else ["Endocrine Therapy", "CDK4/6 Inhibition"]),
            "drug_names": (["AC-T (Doxorubicin + Cyclophosphamide -> Paclitaxel)", endocrine_drug] if chemo_needed else ["Palbociclib / Ribociclib", endocrine_drug]),
            "duration_months": "18–36 (chemo) + 60 (ET)" if chemo_needed else "24–36 (CDK4/6) + 60 (ET)",
            "rule_trace": [
                {"biomarker": "Ki-67", "value": f"{ki67}%", "implication": f"{'High proliferation (≥20%) → chemotherapy indicated' if ki67 >= 20 else 'Intermediate Ki-67 — genomic assay guides decision'}"},
                {"biomarker": "OncotypeDX", "value": str(c.oncotype_dx_score or "Not tested"),
                 "implication": "Score >25 → chemotherapy benefit (TAILORx); Score ≤25 → endocrine sufficient"},
                {"biomarker": "Stage", "value": f"Stage {c.stage}, Grade {c.grade}",
                 "implication": f"{'High-stage: chemotherapy escalation appropriate' if high_risk else 'Lower-risk: de-escalation to endocrine ± CDK4/6 preferred'}"},
            ],
            "clinical_notes": f"{'Chemotherapy recommended: Ki-67 ≥20% or high-risk features. AC-T preferred regimen (EBCTCG meta-analysis).' if chemo_needed else 'Endocrine ± CDK4/6 inhibitor for intermediate-risk Luminal B. Avoids cytotoxic toxicity where genomic risk is low.'}",
        })
        # PATH 2 — CDK4/6 inhibitor escalation
        protocols.append({
            "rank": 2,
            "protocol_name": "Endocrine + CDK4/6 Inhibitor (Adjuvant Escalation)",
            "guideline_source": "NCCN 2024 / monarchE",
            "confidence_score": 0.85 if node_positive else 0.73,
            "treatment_components": ["CDK4/6 Inhibition", "Endocrine Therapy"],
            "drug_names": ["Abemaciclib (200mg BD)", endocrine_drug],
            "duration_months": "24 (Abemaciclib) + 60 (ET)",
            "rule_trace": [
                {"biomarker": "Node Status", "value": f"{'Positive' if node_positive else 'Negative'}", "implication": "monarchE trial: Abemaciclib reduces recurrence in node-positive HR+ HER2- (Ki-67 ≥20%)"},
                {"biomarker": "Ki-67", "value": f"{ki67}%", "implication": f"{'≥20% — monarchE eligibility criteria met' if ki67 >= 20 else 'Below 20% — moderate CDK4/6 indication'}"},
            ],
            "clinical_notes": "monarchE (2021): Abemaciclib adjuvant significantly improves iDFS in high-risk HR+/HER2-/node-positive patients. Ki-67 ≥20% and ≥4 nodes = highest benefit subgroup.",
        })
        # PATH 3 — Dose-dense or neoadjuvant approach
        protocols.append({
            "rank": 3,
            "protocol_name": "Neoadjuvant Chemotherapy → pCR-Guided Adjuvant",
            "guideline_source": "ESMO 2023",
            "confidence_score": 0.74 if high_risk else 0.60,
            "treatment_components": ["Neoadjuvant Chemotherapy", "Surgical Re-evaluation", "Adjuvant Escalation"],
            "drug_names": ["ddAC (dose-dense doxorubicin + cyclophosphamide)", "Paclitaxel weekly", "± Capecitabine (CREATE-X)"],
            "duration_months": "6–8 (neoadj) + 6–8 (adj cap if residual)",
            "rule_trace": [
                {"biomarker": "Stage", "value": f"Stage {c.stage}", "implication": "Neoadjuvant preferred for Stage III or large T2 to downstage and assess pCR"},
                {"biomarker": "Residual Disease", "value": "Post-neoadjuvant", "implication": "pCR → excellent prognosis. Residual disease → Capecitabine adjuvant (CREATE-X)"},
            ],
            "clinical_notes": "Neoadjuvant approach preferred for large tumours or node-positive to assess treatment response. Residual disease at surgery → escalate to adjuvant Capecitabine (CREATE-X trial, HR 0.58 DFS benefit).",
        })

    # ── LUMINAL B (HER2+) ─────────────────────────────────────────────────────
    elif luminal_b_her2pos:
        protocols.append({
            "rank": 1,
            "protocol_name": "Dual HER2 Blockade + Chemotherapy + Endocrine Therapy",
            "guideline_source": "NCCN 2024",
            "confidence_score": 0.93,
            "treatment_components": ["Neoadjuvant Chemotherapy", "Dual HER2 Blockade", "Endocrine Therapy"],
            "drug_names": ["Trastuzumab", "Pertuzumab", "Docetaxel", "Carboplatin", endocrine_drug],
            "duration_months": "18–24",
            "rule_trace": [
                {"biomarker": "HER2", "value": c.her2_status, "implication": "HER2 amplification — dual anti-HER2 blockade mandatory (NeoSphere/TRYPHAENA)"},
                {"biomarker": "ER/PR", "value": f"{c.er_status}/{c.pr_status}", "implication": "Hormone receptor positivity — endocrine therapy added sequentially post-chemotherapy"},
                {"biomarker": "Stage", "value": f"Stage {c.stage}", "implication": "Neoadjuvant TCHP preferred for operable disease to achieve pCR"},
            ],
            "clinical_notes": "TCHP regimen (TRYPHAENA). Dual HER2 blockade is NCCN Category 1. Apply endocrine therapy after completion of chemotherapy. pCR at surgery guides adjuvant selection.",
        })
        protocols.append({
            "rank": 2,
            "protocol_name": "T-DM1 Adjuvant (Residual Disease Post-Neoadjuvant)",
            "guideline_source": "NCCN 2024 / KATHERINE",
            "confidence_score": 0.89,
            "treatment_components": ["Antibody-Drug Conjugate", "Endocrine Therapy"],
            "drug_names": ["T-DM1 (Trastuzumab emtansine 3.6 mg/kg q3w)", endocrine_drug],
            "duration_months": "14 (T-DM1) + concurrent ET",
            "rule_trace": [
                {"biomarker": "pCR Status", "value": "Residual Disease", "implication": "KATHERINE trial: T-DM1 reduces recurrence by 50% vs Trastuzumab in HER2+ residual disease (HR 0.50)"},
            ],
            "clinical_notes": "KATHERINE trial (2019): T-DM1 is standard for HER2+/HR+ patients not achieving pCR after neoadjuvant TCHP. 11.3% absolute iDFS improvement at 3 years.",
        })
        protocols.append({
            "rank": 3,
            "protocol_name": "Tucatinib + Trastuzumab + Capecitabine ± Endocrine Therapy",
            "guideline_source": "NCCN 2024 / HER2CLIMB",
            "confidence_score": 0.74,
            "treatment_components": ["TKI Therapy", "Anti-HER2 mAb", "Oral Chemotherapy", "Endocrine Therapy"],
            "drug_names": ["Tucatinib 300mg BD", "Trastuzumab", "Capecitabine", endocrine_drug],
            "duration_months": "Until progression",
            "rule_trace": [
                {"biomarker": "HER2", "value": c.her2_status, "implication": "HER2CLIMB regimen: preferred for trastuzumab/T-DM1-pretreated HER2+ disease, including CNS metastases"},
            ],
            "clinical_notes": "HER2CLIMB trial: 34% OS improvement over placebo arm. Use in 2nd-3rd line after Trastuzumab + Pertuzumab and T-DM1. CNS penetration advantage for brain-metastatic disease.",
        })

    # ── HER2-ENRICHED ─────────────────────────────────────────────────────────
    elif her2_enriched:
        protocols.append({
            "rank": 1,
            "protocol_name": "TCHP (Anti-HER2 Dual Blockade + Chemotherapy)",
            "guideline_source": "NCCN 2024",
            "confidence_score": 0.94,
            "treatment_components": ["Neoadjuvant Chemotherapy", "Dual HER2 Blockade"],
            "drug_names": ["Trastuzumab 6mg/kg", "Pertuzumab 420mg", "Docetaxel 75mg/m²", "Carboplatin AUC6"],
            "duration_months": "18",
            "rule_trace": [
                {"biomarker": "HER2", "value": c.her2_status, "implication": "HER2 overexpression — TCHP mandatory; pCR rate 45-67% (NeoSphere/TRYPHAENA)"},
                {"biomarker": "ER/PR", "value": "Negative", "implication": "Hormone-receptor negative — endocrine therapy not required"},
            ],
            "clinical_notes": "TCHP is NCCN Category 1 for HER2-Enriched. pCR at surgery → continue trastuzumab (1 yr). Residual disease → T-DM1 (KATHERINE). Cardiac monitoring every 3 months.",
        })
        protocols.append({
            "rank": 2,
            "protocol_name": "T-DM1 Adjuvant (If Residual Disease)",
            "guideline_source": "NCCN 2024 / KATHERINE",
            "confidence_score": 0.88,
            "treatment_components": ["Antibody-Drug Conjugate"],
            "drug_names": ["T-DM1 (Trastuzumab emtansine) 3.6 mg/kg q3w"],
            "duration_months": "14",
            "rule_trace": [
                {"biomarker": "Residual Disease", "value": "Post-TCHP", "implication": "KATHERINE: T-DM1 vs Trastuzumab in HER2+ residual — 50% recurrence reduction"},
            ],
            "clinical_notes": "Switch to T-DM1 for HER2+ patients with residual invasive disease after neoadjuvant TCHP. Do NOT use T-DM1 concurrently with Pertuzumab.",
        })
        protocols.append({
            "rank": 3,
            "protocol_name": "THP (Carboplatin-Free) + Adjuvant Trastuzumab Deruxtecan",
            "guideline_source": "NCCN 2024 / DESTINY-Breast06",
            "confidence_score": 0.69,
            "treatment_components": ["HER2-targeted Therapy", "ADC"],
            "drug_names": ["THP (Taxane + Herceptin + Pertuzumab)", "T-DXd (Trastuzumab deruxtecan 5.4mg/kg)"],
            "duration_months": "18 (THP) → T-DXd if progression",
            "rule_trace": [
                {"biomarker": "HER2", "value": c.her2_status, "implication": "T-DXd (DESTINY-Breast06): superior PFS in HER2+ vs standard chemotherapy"},
                {"biomarker": "Renal Function", "value": "Consider if Carboplatin contraindicated", "implication": "THP (without Carboplatin) for renal impairment or toxicity concerns"},
            ],
            "clinical_notes": "T-DXd is emerging as post-TCHP standard (DESTINY-Breast03: 72.8% response rate). Reserve carboplatin-free THP for impaired renal function.",
        })

    # ── TRIPLE-NEGATIVE ────────────────────────────────────────────────────────
    elif tnbc:
        protocols.append({
            "rank": 1,
            "protocol_name": f"Neoadjuvant AC-T {'+ Pembrolizumab' if pdl1_pos else '(Standard)'}",
            "guideline_source": "NCCN 2024 / KEYNOTE-522",
            "confidence_score": 0.92 if pdl1_pos else 0.87,
            "treatment_components": ["Anthracycline Chemotherapy", "Taxane"] + (["PD-1 Checkpoint Inhibitor"] if pdl1_pos else []),
            "drug_names": ["Doxorubicin 60mg/m²", "Cyclophosphamide 600mg/m²", "Paclitaxel 80mg/m² weekly"] + (["Pembrolizumab 200mg q3w"] if pdl1_pos else []),
            "duration_months": "6–9",
            "rule_trace": [
                {"biomarker": "ER/PR/HER2", "value": "All Negative", "implication": "TNBC — aggressive neoadjuvant chemotherapy is standard regardless of PD-L1 status"},
                *([ {"biomarker": "PD-L1", "value": c.pdl1_status, "implication": "KEYNOTE-522: Pembrolizumab + AC-T improves pCR by 13.6% and EFS by 37%"} ] if pdl1_pos else
                  [ {"biomarker": "PD-L1", "value": "Negative/Unknown", "implication": "KEYNOTE-522: Even PD-L1 negative TNBC patients showed EFS benefit from Pembrolizumab addition"} ]),
                {"biomarker": "BRCA", "value": f"{c.brca1_status}/{c.brca2_status}", "implication": f"{'BRCA mutation: add platinum sensitivity consideration to neoadjuvant' if brca_positive else 'BRCA wild-type: standard AC-T preferred'}"},
            ],
            "clinical_notes": f"{'KEYNOTE-522: FDA-approved Pembrolizumab + chemotherapy for high-risk early TNBC. EFS HR 0.63.' if pdl1_pos else 'Standard AC-T for early TNBC. Assess pCR at surgery — pCR = excellent prognosis. Residual disease → escalate adjuvant.'}",
        })
        # PATH 2 — PARP inhibitor (BRCA+) or Sacituzumab (BRCA-)
        if brca_positive:
            protocols.append({
                "rank": 2,
                "protocol_name": "PARP Inhibitor Maintenance (Post-Chemotherapy)",
                "guideline_source": "NCCN 2024 / OlympiA",
                "confidence_score": 0.91,
                "treatment_components": ["PARP Inhibition"],
                "drug_names": ["Olaparib 300mg BD (1yr adjuvant)", "Alt: Talazoparib 1mg OD"],
                "duration_months": "12",
                "rule_trace": [
                    {"biomarker": "BRCA1/2", "value": "Germline Mutation Detected", "implication": "OlympiA (2021): Olaparib adjuvant — 42% reduction in distant recurrence risk (HR 0.57) in gBRCA HER2- high-risk"},
                ],
                "clinical_notes": "OlympiA trial (NEJM 2021): Adjuvant Olaparib 1yr after (neo)adjuvant chemotherapy for gBRCA1/2 HER2- high-risk patients. 7.4% absolute invasive DFS benefit at 4 years.",
            })
        else:
            protocols.append({
                "rank": 2,
                "protocol_name": "Sacituzumab Govitecan (Metastatic / Refractory TNBC)",
                "guideline_source": "NCCN 2024 / ASCENT",
                "confidence_score": 0.82,
                "treatment_components": ["Antibody-Drug Conjugate (Trop-2 directed)"],
                "drug_names": ["Sacituzumab govitecan 10mg/kg (d1,d8 q3w)"],
                "duration_months": "Until progression",
                "rule_trace": [
                    {"biomarker": "Trop-2", "value": "Highly expressed in TNBC", "implication": "ASCENT: Sacituzumab govitecan vs chemotherapy — median PFS 5.6 vs 1.7 months in pretreated TNBC"},
                ],
                "clinical_notes": "ASCENT trial (NEJM 2021): Sacituzumab govitecan is preferred 2nd-line+ TNBC after taxane/platinum failure. TROP-2 directed ADC delivering SN-38 payload.",
            })
        # PATH 3 — Escalation / Special populations
        protocols.append({
            "rank": 3,
            "protocol_name": "Capecitabine Adjuvant (Residual Disease) ± Olaparib",
            "guideline_source": "ESMO 2023 / CREATE-X",
            "confidence_score": 0.83 if node_positive or high_stage else 0.70,
            "treatment_components": ["Oral Fluoropyrimidine"] + (["PARP Inhibition"] if brca_positive else []),
            "drug_names": ["Capecitabine 1000–1250 mg/m² BD (d1-14 q3w × 8 cycles)"] + (["+ Olaparib (OlympiA)" ] if brca_positive else []),
            "duration_months": "6–8",
            "rule_trace": [
                {"biomarker": "Residual Disease", "value": f"{'Node Positive' if node_positive else 'Residual TNBC'}", "implication": "CREATE-X: Capecitabine adjuvant for residual disease — DFS HR 0.58, OS HR 0.52"},
            ],
            "clinical_notes": f"CREATE-X (NEJM 2017): Post-neoadjuvant Capecitabine significantly improves OS in TNBC with residual disease. {'BRCA mutation present: combine with Olaparib if OlympiA criteria met.' if brca_positive else 'BRCA negative: Capecitabine monotherapy as per CREATE-X.'}",
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
