"""
tests/test_engine.py
Tests for all 5 engine stages + contraindication rules.
Each contraindication rule is tested independently.
"""
import pytest
from engine.biomarker_algorithm import (
    ClinicalInput, classify_subtype, genomic_risk_modifiers,
    immune_mutation_flags, generate_treatment_pathways, run_pipeline,
)
from engine.contraindication_checker import (
    check_lvef, check_ecog, check_brca_platinum_sensitivity,
    check_renal, check_hepatic, check_allergy, run_all_checks,
)
from engine.nlp_extractor import extract_from_text, map_to_clinical_fields


# ─── Stage 1: Subtype classification ─────────────────────────────────────────

@pytest.mark.parametrize("er,pr,her2,ki67,expected", [
    ("Positive", "Positive", "Negative", 10.0, "Luminal A"),
    ("Positive", "Negative", "Negative", 25.0, "Luminal B (HER2-)"),
    ("Positive", "Positive", "Positive", 20.0, "Luminal B (HER2+)"),
    ("Negative", "Negative", "Positive", 40.0, "HER2-Enriched"),
    ("Negative", "Negative", "Negative", 55.0, "Triple-Negative"),
])
def test_classify_subtype(er, pr, her2, ki67, expected):
    c = ClinicalInput(er_status=er, pr_status=pr, her2_status=her2, ki67_percent=ki67)
    subtype, confidence, trace = classify_subtype(c)
    assert subtype == expected
    assert 0 < confidence <= 1.0
    assert len(trace) > 0


def test_pam50_override():
    c = ClinicalInput(
        er_status="Negative", pr_status="Negative", her2_status="Negative",
        ki67_percent=30.0, pam50="Luminal A"
    )
    subtype, confidence, _ = classify_subtype(c)
    assert subtype == "Luminal A"  # PAM50 overrides IHC


def test_high_confidence_clear_markers():
    c = ClinicalInput(er_status="Positive", pr_status="Positive", her2_status="Negative", ki67_percent=10.0)
    _, confidence, _ = classify_subtype(c)
    assert confidence >= 0.85


def test_medium_confidence_equivocal_her2():
    c = ClinicalInput(er_status="Positive", pr_status="Positive", her2_status="Equivocal", ki67_percent=14.0)
    _, confidence, _ = classify_subtype(c)
    assert confidence < 0.85


def test_low_confidence_unknown_markers():
    c = ClinicalInput(er_status="Unknown", pr_status="Unknown", her2_status="Unknown")
    _, confidence, _ = classify_subtype(c)
    assert confidence < 0.60


# ─── Stage 2: Genomic modifiers ──────────────────────────────────────────────

def test_oncotype_dx_low():
    c = ClinicalInput(oncotype_dx_score=20.0)
    mods = genomic_risk_modifiers(c)
    low = [m for m in mods if m["source"] == "OncotypeDX" and m["risk"] == "low"]
    assert len(low) == 1


def test_oncotype_dx_high():
    c = ClinicalInput(oncotype_dx_score=35.0)
    mods = genomic_risk_modifiers(c)
    high = [m for m in mods if m["source"] == "OncotypeDX" and m["risk"] == "high"]
    assert len(high) == 1


def test_brca1_mutation_flag():
    c = ClinicalInput(brca1_status="Positive")
    mods = genomic_risk_modifiers(c)
    brca = [m for m in mods if "BRCA" in m["source"]]
    assert len(brca) == 1
    assert "Olaparib" in brca[0]["implication"]


def test_mammaprint_low():
    c = ClinicalInput(mammaprint="Low Risk")
    mods = genomic_risk_modifiers(c)
    mp = [m for m in mods if m["source"] == "MammaPrint"]
    assert mp[0]["risk"] == "low"


# ─── Stage 3: Immune & mutation flags ────────────────────────────────────────

def test_pdl1_positive_flag():
    c = ClinicalInput(pdl1_status="Positive")
    flags = immune_mutation_flags(c)
    pdl1 = [f for f in flags if f["source"] == "PD-L1"]
    assert len(pdl1) == 1
    assert "Pembrolizumab" in pdl1[0].get("drug_flag", "")


def test_high_tils():
    c = ClinicalInput(tils_percent=45.0)
    flags = immune_mutation_flags(c)
    tils = [f for f in flags if f["source"] == "TILs"]
    assert len(tils) == 1


def test_pik3ca_mutation():
    c = ClinicalInput(pik3ca_status="Positive", er_status="Positive")
    flags = immune_mutation_flags(c)
    pik = [f for f in flags if f["source"] == "PIK3CA"]
    assert len(pik) == 1
    assert "Alpelisib" in pik[0]["drug_flag"]


def test_cyclin_d1_amplification():
    c = ClinicalInput(cyclin_d1="Positive")
    flags = immune_mutation_flags(c)
    cdk = [f for f in flags if f["source"] == "Cyclin D1"]
    assert len(cdk) == 1
    assert "Palbociclib" in cdk[0]["drug_flag"]


# ─── Stage 4: Treatment pathways ─────────────────────────────────────────────

def test_luminal_a_protocol():
    c = ClinicalInput(er_status="Positive", pr_status="Positive", her2_status="Negative", ki67_percent=10.0)
    _, _, trace = classify_subtype(c)
    protocols = generate_treatment_pathways("Luminal A", c, [], [])
    assert len(protocols) >= 1
    assert protocols[0]["rank"] == 1
    assert "Endocrine" in protocols[0]["protocol_name"]


def test_tnbc_adds_pembrolizumab_when_pdl1_positive():
    c = ClinicalInput(er_status="Negative", pr_status="Negative", her2_status="Negative", pdl1_status="Positive")
    flags = immune_mutation_flags(c)
    protocols = generate_treatment_pathways("Triple-Negative", c, [], flags)
    names = " ".join(p["protocol_name"] for p in protocols)
    assert "Pembrolizumab" in names


def test_her2_enriched_dual_blockade():
    c = ClinicalInput(er_status="Negative", pr_status="Negative", her2_status="Positive")
    protocols = generate_treatment_pathways("HER2-Enriched", c, [], [])
    drugs = " ".join(" ".join(p.get("drug_names", [])) for p in protocols)
    assert "Trastuzumab" in drugs


# ─── Stage 5 / Contraindications ─────────────────────────────────────────────

def test_lvef_below_55_triggers_alert():
    alerts = check_lvef(50.0, [])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "HIGH"


def test_lvef_critical_below_40():
    alerts = check_lvef(35.0, [])
    assert "critically low" in alerts[0]["trigger"]


def test_lvef_normal_no_alert():
    alerts = check_lvef(65.0, [])
    assert alerts == []


def test_ecog_3_triggers_alert():
    alerts = check_ecog(3, [])
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "HIGH"


def test_ecog_2_is_medium():
    alerts = check_ecog(2, [])
    assert alerts[0]["severity"] == "MEDIUM"


def test_ecog_0_no_alert():
    alerts = check_ecog(0, [])
    assert alerts == []


def test_renal_with_platinum():
    protocols = [{"drug_names": ["Carboplatin", "Paclitaxel"]}]
    alerts = check_renal({"CKD Grade 3": True}, protocols)
    assert len(alerts) == 1
    assert "Platinum" in alerts[0]["alert_type"]


def test_renal_no_platinum_no_alert():
    protocols = [{"drug_names": ["Tamoxifen"]}]
    alerts = check_renal({"CKD Grade 3": True}, protocols)
    assert alerts == []


def test_hepatic_metabolised_drug_alert():
    protocols = [{"drug_names": ["Tamoxifen", "Letrozole"]}]
    alerts = check_hepatic({"Liver cirrhosis": True}, None, protocols)
    assert len(alerts) == 1


def test_allergy_alert():
    protocols = [{"drug_names": ["Tamoxifen"]}]
    alerts = check_allergy("Tamoxifen allergy documented", protocols)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "HIGH"


def test_brca_anthracycline_note():
    protocols = [{"drug_names": ["Doxorubicin"], "treatment_components": ["Anthracycline Chemotherapy"]}]
    alerts = check_brca_platinum_sensitivity("Positive", "Negative", protocols)
    assert len(alerts) == 1
    assert alerts[0]["severity"] == "LOW"


# ─── Full pipeline integration ────────────────────────────────────────────────

def test_full_pipeline_luminal_a():
    c = ClinicalInput(
        er_status="Positive", pr_status="Positive", her2_status="Negative",
        ki67_percent=10.0, stage="II", grade=2, ecog_score=0, lvef_percent=65.0
    )
    result = run_pipeline(c)
    assert result.molecular_subtype == "Luminal A"
    assert len(result.recommendations) >= 1
    assert isinstance(result.alerts, list)


def test_full_pipeline_tnbc_with_alerts():
    c = ClinicalInput(
        er_status="Negative", pr_status="Negative", her2_status="Negative",
        lvef_percent=45.0, ecog_score=0
    )
    result = run_pipeline(c)
    assert result.molecular_subtype == "Triple-Negative"
    lvef_alerts = [a for a in result.alerts if "Cardiac" in a.get("alert_type", "")]
    assert len(lvef_alerts) >= 1


# ─── NLP Extractor ───────────────────────────────────────────────────────────

SAMPLE_REPORT = """
Histopathology Report — Biopsy Left Breast

Patient: Jane Doe, Age 52
Histological Type: Invasive Ductal Carcinoma
Tumour Size: 2.3 cm
TNM Staging: T2N1M0, Stage IIB
Grade: Grade 2 (Moderately differentiated)

Immunohistochemistry:
  ER: Positive (Allred Score 7)
  PR: Positive
  HER2: Negative (1+)
  Ki-67: 14%
  PD-L1 CPS 5

Lymph Nodes: 2/15 nodes positive
BRCA1: Not detected
BRCA2: Not detected
TILs: 20%
Oncotype DX score: 18
"""


def test_nlp_extracts_er_status():
    result = extract_from_text(SAMPLE_REPORT)
    assert "ER_STATUS" in result["extracted"]
    assert result["extracted"]["ER_STATUS"]["value"] in ("Positive", "positive", "+")


def test_nlp_extracts_tumour_size():
    result = extract_from_text(SAMPLE_REPORT)
    assert "TUMOUR_SIZE" in result["extracted"]


def test_nlp_extracts_ki67():
    result = extract_from_text(SAMPLE_REPORT)
    assert "KI67_VALUE" in result["extracted"]
    assert "14" in result["extracted"]["KI67_VALUE"]["value"]


def test_nlp_extracts_stage():
    result = extract_from_text(SAMPLE_REPORT)
    assert "TNM_STAGE" in result["extracted"]


def test_nlp_extracts_oncotype_score():
    result = extract_from_text(SAMPLE_REPORT)
    assert "ONCOTYPE_SCORE" in result["extracted"]
    assert "18" in result["extracted"]["ONCOTYPE_SCORE"]["value"]


def test_nlp_overall_confidence():
    result = extract_from_text(SAMPLE_REPORT)
    assert result["overall_confidence"] > 0.5


def test_nlp_map_to_clinical_fields():
    result = extract_from_text(SAMPLE_REPORT)
    fields = map_to_clinical_fields(result)
    assert "ki67_percent" in fields
    assert isinstance(fields["ki67_percent"], float)
