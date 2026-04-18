"""
engine/ai_reasoning.py
Enhances deterministic pipeline output with Ollama cloud AI reasoning.
Uses the Ollama cloud API (https://ollama.com/api) with llama3.1 for clinical narratives.
"""
from __future__ import annotations

import os
import json
import httpx
from .biomarker_algorithm import PipelineResult, ClinicalInput

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "3eeb9d3cc3464bd9bdaa4ca5131b1d02.6C54tCVm4GBCs42Al7vnC2iJ")
OLLAMA_BASE_URL = "https://ollama.com/api"
OLLAMA_MODEL = "llama3.1:70b"  # Best for clinical reasoning on Ollama cloud


def _build_clinical_prompt(clinical: ClinicalInput, result: PipelineResult) -> str:
    """Build a structured clinical reasoning prompt for the AI."""
    recs_text = "\n".join(
        f"  - {r.get('protocol_name', 'Protocol')} (confidence: {int((r.get('confidence_score',0))*100)}%): {r.get('clinical_notes', '')}"
        for r in result.recommendations[:3]
    )
    alerts_text = "\n".join(
        f"  - {a.get('contraindication_type', 'Alert')}: {a.get('reason', '')}"
        for a in result.alerts
    ) or "  None identified."
    
    return f"""You are an expert oncologist specializing in breast cancer treatment. 
Analyze this patient's molecular profile and provide a concise, evidence-based clinical reasoning narrative.

PATIENT MOLECULAR PROFILE:
- ER Status: {clinical.er_status}
- PR Status: {clinical.pr_status}
- HER2 Status: {clinical.her2_status}
- Ki-67: {clinical.ki67_percent}%
- Stage: {clinical.stage}
- Grade: {clinical.grade}
- BRCA1: {clinical.brca1_status}
- BRCA2: {clinical.brca2_status}
- Tumour Size: {clinical.tumour_size} cm
- Lymph Nodes: {"Positive" if clinical.lymph_nodes_involved else "Negative"}
- LVEF: {clinical.lvef_percent}%
- Menopausal Status: {clinical.menopausal_status}

ALGORITHMIC CLASSIFICATION:
- Molecular Subtype: {result.molecular_subtype}
- Confidence Score: {int(result.subtype_confidence * 100)}%

TOP TREATMENT RECOMMENDATIONS:
{recs_text or "  None generated."}

SAFETY ALERTS:
{alerts_text}

Provide a structured clinical reasoning summary in exactly this JSON format:
{{
  "subtype_rationale": "2-3 sentences explaining WHY this molecular subtype was determined based on the specific biomarkers",
  "treatment_rationale": "2-3 sentences explaining why the recommended treatment pathway is appropriate for this patient",
  "key_biomarkers": ["list", "of", "3-5", "most", "important", "biomarker", "findings"],
  "clinical_considerations": "1-2 sentences on special considerations or monitoring needed",
  "prognosis_summary": "1 sentence on expected clinical outlook with recommended treatment",
  "confidence_explanation": "1 sentence on what additional tests could improve classification confidence"
}}

Respond ONLY with valid JSON. No extra text."""


async def enhance_with_ai(clinical: ClinicalInput, result: PipelineResult) -> dict:
    """
    Call Ollama cloud to generate clinical reasoning narrative.
    Falls back gracefully if the API call fails.
    """
    try:
        prompt = _build_clinical_prompt(clinical, result)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/chat",
                headers={
                    "Authorization": f"Bearer {OLLAMA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # Low temp for clinical accuracy
                        "top_p": 0.9,
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                # Parse the JSON response
                reasoning = json.loads(content)
                return reasoning
            else:
                return _fallback_reasoning(clinical, result)
                
    except Exception as e:
        print(f"[AI Reasoning] Ollama cloud call failed: {e}. Using deterministic fallback.")
        return _fallback_reasoning(clinical, result)


def _fallback_reasoning(clinical: ClinicalInput, result: PipelineResult) -> dict:
    """Generate deterministic reasoning when AI is unavailable."""
    subtype = result.molecular_subtype
    
    rationale_map = {
        "Luminal A": f"ER+/PR+ receptor positivity with HER2-negativity and low Ki-67 ({clinical.ki67_percent}%) places this tumour in the Luminal A category, indicating a hormone-driven, low-proliferating phenotype.",
        "Luminal B (HER2-)": f"Despite hormone receptor positivity, the elevated Ki-67 of {clinical.ki67_percent}% indicates high proliferative activity, driving a Luminal B (HER2-) classification per NCCN/St. Gallen criteria.",
        "Luminal B (HER2+)": f"Concurrent hormone receptor positivity and HER2 amplification defines Luminal B (HER2+) subtype, requiring dual-targeting strategy.",
        "HER2-Enriched": f"HER2 overexpression in the absence of hormone receptor positivity classifies this as HER2-Enriched, mandating anti-HER2 therapy.",
        "Triple-Negative": f"Absence of ER, PR, and HER2 expression defines Triple-Negative Breast Cancer (TNBC), necessitating platinum-based or immunotherapy regimens.",
    }
    
    treatment = result.recommendations[0] if result.recommendations else {}
    
    return {
        "subtype_rationale": rationale_map.get(subtype, f"Based on the biomarker profile, {subtype} classification was determined per international guidelines."),
        "treatment_rationale": f"{treatment.get('protocol_name', 'Standard of care')} is recommended per {treatment.get('guideline_source', 'NCCN')} guidelines with {int((treatment.get('confidence_score', 0.7)) * 100)}% protocol confidence.",
        "key_biomarkers": [
            f"ER: {clinical.er_status}",
            f"PR: {clinical.pr_status}",
            f"HER2: {clinical.her2_status}",
            f"Ki-67: {clinical.ki67_percent}%",
            f"Stage: {clinical.stage}",
        ],
        "clinical_considerations": f"Patient's LVEF of {clinical.lvef_percent}% {'may limit anthracycline use' if clinical.lvef_percent and clinical.lvef_percent < 55 else 'is within acceptable range for standard chemotherapy protocols'}.",
        "prognosis_summary": f"With standard-of-care treatment for {subtype}, 5-year survival outcomes align with published {clinical.stage}-stage cohort data.",
        "confidence_explanation": f"Current classification confidence is {int(result.subtype_confidence * 100)}%; additional genomic assay (Oncotype DX or PAM50) would further refine treatment decisions.",
    }


# ─── Per-pathway NCCN/ESMO explainability ─────────────────────────────────────

def _build_pathway_prompt(clinical: ClinicalInput, protocols: list[dict]) -> str:
    paths_text = "\n".join(
        f"PATH {i+1} — {p.get('protocol_name')} ({p.get('guideline_source')}, {int(p.get('confidence_score',0)*100)}% confidence):\n"
        f"  Drugs: {', '.join(p.get('drug_names') or p.get('drugs') or [])}\n"
        f"  Notes: {p.get('clinical_notes','')}"
        for i, p in enumerate(protocols)
    )
    return f"""You are an expert oncologist. For each treatment path below, provide NCCN and ESMO guideline explainability.

PATIENT PROFILE:
- Molecular Subtype: derived from ER={clinical.er_status}, PR={clinical.pr_status}, HER2={clinical.her2_status}, Ki-67={clinical.ki67_percent}%
- Stage: {clinical.stage}, Grade: {clinical.grade}
- BRCA1/2: {clinical.brca1_status}/{clinical.brca2_status}
- Menopausal: {clinical.menopausal_status}
- Nodes: {"Positive" if clinical.lymph_nodes_involved else "Negative"}

TREATMENT PATHS:
{paths_text}

For EACH path, return a JSON array (same order as input) where each element has:
{{
  "nccn_category": "NCCN Category 1/2A/2B/3 with one-line explanation",
  "esmo_grade": "ESMO Grade A/B/C with one-line explanation",
  "trial_evidence": "Key clinical trial(s) supporting this path (e.g. KEYNOTE-522, KATHERINE, OlympiAD)",
  "mechanism": "1-2 sentences on drug mechanism and why it targets this subtype specifically",
  "who_benefits_most": "1 sentence on which patient subgroup benefits most from this path",
  "monitoring": "Key monitoring parameters (e.g. cardiac function, liver enzymes, CBC)",
  "alternative_if_intolerant": "What to switch to if patient is intolerant"
}}

Return ONLY a valid JSON array with exactly {len(protocols)} elements. No extra text."""


async def enhance_pathways_with_ai(clinical: ClinicalInput, protocols: list[dict]) -> list[dict]:
    """
    Adds NCCN/ESMO per-pathway explainability to each treatment protocol.
    Falls back to deterministic library if Ollama call fails.
    """
    if not protocols:
        return []

    try:
        prompt = _build_pathway_prompt(clinical, protocols)
        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/chat",
                headers={
                    "Authorization": f"Bearer {OLLAMA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.15, "top_p": 0.9},
                }
            )
            if response.status_code == 200:
                content = response.json().get("message", {}).get("content", "")
                explainability = json.loads(content)
                # Merge back into protocols
                return [
                    {**p, "guideline_explainability": explainability[i] if i < len(explainability) else {}}
                    for i, p in enumerate(protocols)
                ]
    except Exception as e:
        print(f"[AI Pathways] Ollama call failed: {e}. Using deterministic fallback.")

    return _fallback_pathway_explainability(clinical, protocols)


# ─── Deterministic per-pathway library ───────────────────────────────────────
_PATHWAY_LIBRARY: dict[str, dict] = {
    "Endocrine Monotherapy": {
        "nccn_category": "Category 1 — Strongly preferred for Luminal A based on multiple phase III trials",
        "esmo_grade": "Grade A — Highest level of evidence; supported by SOFT/TEXT and ATAC trials",
        "trial_evidence": "SOFT, TEXT (Tamoxifen); ATAC, BIG 1-98 (Aromatase Inhibitors); monarchE (Abemaciclib adjuvant)",
        "mechanism": "Tamoxifen competitively blocks ER-alpha in tumour cells, blocking oestrogen-driven proliferation. Aromatase inhibitors suppress peripheral oestrogen synthesis in post-menopausal patients.",
        "who_benefits_most": "Post-menopausal patients with ER+/PR+, HER2-, Ki-67 <14%, Grade 1-2 tumours who have the greatest benefit and lowest chemotherapy risk.",
        "monitoring": "Annual bone density (DEXA) for AI users, endometrial surveillance for tamoxifen users, liver function tests, lipid panel",
        "alternative_if_intolerant": "Switch AI class (e.g. exemestane if letrozole intolerant); tamoxifen for AI-intolerant; consider fulvestrant",
    },
    "Endocrine + CDK4/6 Inhibitor": {
        "nccn_category": "Category 1 — Standard for HR+/HER2- metastatic or high-risk adjuvant setting",
        "esmo_grade": "Grade A — monarchE, PALOMA-2, MONALEESA-2 all show significant DFS/PFS benefit",
        "trial_evidence": "monarchE (Abemaciclib adjuvant), PALOMA-2/3 (Palbociclib), MONALEESA-2/3/7 (Ribociclib)",
        "mechanism": "CDK4/6 inhibitors block cyclin D1-CDK4/6 complex, arresting cells in G1 phase and preventing S-phase entry. Synergistic with oestrogen deprivation.",
        "who_benefits_most": "High Ki-67, node-positive, or high-risk stage II-III HR+ patients where CDK4/6 inhibition significantly reduces recurrence risk.",
        "monitoring": "CBC every 2 weeks (first 2 cycles), liver function monthly, QTc interval for Ribociclib, diarrhoea management for Abemaciclib",
        "alternative_if_intolerant": "Switch CDK4/6 agent; consider Alpelisib + fulvestrant if PIK3CA mutated; mTOR inhibitor (Everolimus) as alternative pathway",
    },
    "Adjuvant Chemotherapy + Endocrine Therapy": {
        "nccn_category": "Category 1 — Indicated for Luminal B with high genomic risk score or node-positive disease",
        "esmo_grade": "Grade A — Meta-analysis (EBCTCG) confirms absolute benefit of polychemotherapy in high-risk HR+ disease",
        "trial_evidence": "EBCTCG Meta-analysis, TAILORx (OncotypeDX >25 → chemo benefit), WSG Plan B, ABC trials",
        "mechanism": "Anthracyclines intercalate DNA and inhibit topoisomerase II; taxanes stabilise microtubules. Combined regimens address heterogeneous tumour cell populations in high-proliferating HR+ disease.",
        "who_benefits_most": "Luminal B patients with Ki-67 >30%, Oncotype DX >25, node-positive disease, or Grade 3 histology — where endocrine therapy alone is insufficient.",
        "monitoring": "Cardiac function (ECHO) before and after anthracyclines, CBC with differential, neuropathy assessment for taxanes, fertility counselling before initiation",
        "alternative_if_intolerant": "TC (docetaxel + cyclophosphamide) if anthracycline contraindicated; consider neoadjuvant approach to assess pCR",
    },
    "Dual HER2 Blockade + Chemotherapy + Endocrine Therapy": {
        "nccn_category": "Category 1 — Standard for HER2+/HR+ early and metastatic breast cancer",
        "esmo_grade": "Grade A — NeoSphere and TRYPHAENA demonstrate pCR improvement with dual blockade",
        "trial_evidence": "NeoSphere (Pertuzumab + Trastuzumab neoadjuvant), TRYPHAENA, CLEOPATRA (metastatic), APHINITY (adjuvant)",
        "mechanism": "Trastuzumab binds HER2 domain IV blocking PI3K/AKT signalling; Pertuzumab blocks domain II preventing HER2-HER3 heterodimerisation. Together they achieve more complete HER2 pathway suppression.",
        "who_benefits_most": "HER2+ patients with concurrent hormone receptor positivity (Luminal B HER2+) requiring both anti-HER2 and endocrine strategies for full receptor blockade.",
        "monitoring": "ECHO/MUGA every 3 months (cardiac monitoring for trastuzumab-related cardiomyopathy), infusion reactions, diarrhoea with Pertuzumab",
        "alternative_if_intolerant": "Trastuzumab monotherapy if Pertuzumab intolerant; T-DM1 for HER2+ residual disease; Lapatinib + Capecitabine as TKI alternative",
    },
    "Anti-HER2 Dual Blockade + Chemotherapy": {
        "nccn_category": "Category 1 — Preferred neoadjuvant regimen for HER2-Enriched",
        "esmo_grade": "Grade A — pCR rates of 45-67% documented in multiple trials with TCHP",
        "trial_evidence": "NeoSphere, TRYPHAENA, NOAH trial; HERA (adjuvant trastuzumab); ExteNET (Neratinib extended therapy)",
        "mechanism": "TCHP regimen combines microtubule stabilisation (Docetaxel), platinum cross-linking (Carboplatin), and dual HER2 domain blockade (Trastuzumab + Pertuzumab) for synergistic tumour cell kill.",
        "who_benefits_most": "HR-/HER2+ patients with high-risk features where maximum upfront HER2 pathway suppression is the therapeutic goal.",
        "monitoring": "ECHO every 3 months, renal function for carboplatin, peripheral neuropathy assessment, CBC weekly",
        "alternative_if_intolerant": "THP (without Carboplatin) if renal impairment; T-DM1 + Pertuzumab; Pyrotinib-based regimens in Asian-approved settings",
    },
    "Tucatinib + Trastuzumab + Capecitabine": {
        "nccn_category": "Category 1 — Preferred for HER2+ with prior taxane and trastuzumab exposure",
        "esmo_grade": "Grade A — HER2CLIMB trial: 34% reduction in death vs placebo-arm",
        "trial_evidence": "HER2CLIMB (Tucker NEJM 2020): OS benefit maintained including CNS metastases subgroup",
        "mechanism": "Tucatinib is a highly selective HER2 TKI (minimal EGFR inhibition), reducing GI toxicity vs Lapatinib. Capecitabine provides intracellular 5-FU delivery; Trastuzumab maintains HER2 blockade.",
        "who_benefits_most": "Patients with HER2+ disease who have progressed on Trastuzumab/Pertuzumab and T-DM1, especially those with brain metastases where CNS penetration is critical.",
        "monitoring": "Liver function (hepatotoxicity risk with Tucatinib), diarrhoea management (Tucatinib + Capecitabine synergy), hand-foot syndrome",
        "alternative_if_intolerant": "T-DXd (Trastuzumab deruxtecan) for heavily pre-treated HER2+; Lapatinib + Capecitabine; Neratinib + Capecitabine",
    },
    "Neoadjuvant Chemotherapy": {
        "nccn_category": "Category 1 — Anthracycline/taxane-based neoadjuvant is standard for TNBC",
        "esmo_grade": "Grade A — pCR is a validated surrogate for improved EFS in TNBC",
        "trial_evidence": "KEYNOTE-522 (Pembrolizumab + chemo), GeparSixto, BrighTNess, CREATE-X",
        "mechanism": "Anthracyclines (DNA intercalation + topoisomerase II inhibition) and taxanes (microtubule stabilisation) target the high proliferative fraction of TNBC. Pembrolizumab restores immune surveillance via PD-1/PD-L1 checkpoint blockade.",
        "who_benefits_most": "All early TNBC patients should receive neoadjuvant chemotherapy to assess pCR and guide adjuvant therapy; PD-L1+ patients have greatest benefit from Pembrolizumab addition.",
        "monitoring": "CBC weekly, cardiac function (ECHO) for anthracycline, immune-related adverse events (irAE) with Pembrolizumab — thyroid, adrenal, hepatic panel",
        "alternative_if_intolerant": "Carboplatin-based regimen (GeparSixto data); sacituzumab govitecan for metastatic TNBC; olaparib if BRCA mutated",
    },
    "Neoadjuvant Chemotherapy + Pembrolizumab": {
        "nccn_category": "Category 1 — First-line for PD-L1+ TNBC based on KEYNOTE-522",
        "esmo_grade": "Grade A — Statistically significant EFS improvement; approved by FDA/EMA",
        "trial_evidence": "KEYNOTE-522: Pembrolizumab + chemo improved pCR by 13.6% and EFS by 37% vs chemo alone (HR 0.63)",
        "mechanism": "PD-1 blockade by Pembrolizumab prevents PD-L1/PD-1 interaction, restoring cytotoxic T-cell activity against tumour cells. Synergistic with chemotherapy-induced immunogenic cell death.",
        "who_benefits_most": "Stage II-III TNBC patients with PD-L1 CPS ≥10 — highest pCR rates and EFS benefit. Even PD-L1 negative patients show benefit from neoadjuvant Pembrolizumab.",
        "monitoring": "irAE monitoring: thyroiditis, pneumonitis, colitis, adrenal insufficiency; baseline TSH + cortisol; LFTs; infusion reactions",
        "alternative_if_intolerant": "Atezolizumab + nab-Paclitaxel (IMpassion130); standard AC-T without immunotherapy; sacituzumab govitecan for metastatic",
    },
    "PARP Inhibitor Maintenance": {
        "nccn_category": "Category 1 — Standard for gBRCA1/2-mutated HER2- breast cancer adjuvant or metastatic",
        "esmo_grade": "Grade A — OlympiAD (Olaparib) and EMBRACA (Talazoparib) show PFS benefit; OlympiA shows invasive DFS benefit",
        "trial_evidence": "OlympiAD (Olaparib, NEJM 2017), EMBRACA (Talazoparib, NEJM 2018), OlympiA (adjuvant Olaparib, NEJM 2021)",
        "mechanism": "PARP inhibitors trap PARP-DNA complexes at single-strand breaks, causing double-strand breaks that BRCA-deficient cells cannot repair via homologous recombination — synthetic lethality.",
        "who_benefits_most": "Germline BRCA1/2-mutated HER2- breast cancer patients; especially TNBC with residual disease post-chemotherapy where platinum sensitivity correlates with PARP inhibitor benefit.",
        "monitoring": "CBC monthly (myelosuppression risk), fatigue management, MDS/AML monitoring for long-term users, creatinine (renal dosing adjustment)",
        "alternative_if_intolerant": "Talazoparib for Olaparib-intolerant patients; platinum-based chemotherapy exploits same HRD pathway; veliparib in clinical trial setting",
    },
    "Capecitabine Adjuvant (Residual Disease)": {
        "nccn_category": "Category 1 — Post-neoadjuvant adjuvant in TNBC with residual disease (CREATE-X)",
        "esmo_grade": "Grade A — CREATE-X trial: 42% improvement in DFS in Asian TNBC cohort; validated in non-Asian populations",
        "trial_evidence": "CREATE-X (Masuda NEJM 2017): 8 cycles of Capecitabine improved DFS (HR 0.58) and OS (HR 0.52) in TNBC with residual disease post-neoadjuvant",
        "mechanism": "Capecitabine is a prodrug converted to 5-FU preferentially in tumour tissue by thymidine phosphorylase. Targets residual, chemotherapy-resistant clones with different metabolic profile.",
        "who_benefits_most": "TNBC patients with substantial residual disease (ypT1+ or ypN+) post-neoadjuvant chemotherapy — the group with poorest prognosis without adjuvant escalation.",
        "monitoring": "Hand-foot syndrome (dose-reduction grading), diarrhoea management, CBC, liver function, DPD deficiency testing before initiation to avoid toxicity",
        "alternative_if_intolerant": "Olaparib (if BRCA mutated, OlympiA); pembrolizumab continuation per KEYNOTE-522 protocol; sacituzumab govitecan for metastatic TNBC",
    },
    "Neoadjuvant T-DM1 (Residual Disease)": {
        "nccn_category": "Category 1 — Post-neoadjuvant adjuvant for HER2+ with residual disease",
        "esmo_grade": "Grade A — KATHERINE trial showed 50% reduction in recurrence risk vs trastuzumab continuation",
        "trial_evidence": "KATHERINE (von Minckwitz NEJM 2019): T-DM1 vs Trastuzumab adjuvant — 11.3% absolute improvement in iDFS at 3 years (HR 0.50)",
        "mechanism": "T-DM1 is an antibody-drug conjugate linking Trastuzumab to DM1 (microtubule inhibitor). HER2-targeted delivery ensures selective tumour cell kill with reduced systemic toxicity vs standard cytotoxics.",
        "who_benefits_most": "HER2+ patients with residual invasive disease post-neoadjuvant TCHP/THP — the group not achieving pCR who have the highest recurrence risk.",
        "monitoring": "Thrombocytopenia (dose-limiting), peripheral neuropathy, liver function (hepatotoxicity), ECHO for cardiac function, interstitial lung disease",
        "alternative_if_intolerant": "Continue Trastuzumab + Pertuzumab; Trastuzumab deruxtecan (T-DXd) for HER2+ metastatic; Neratinib extended adjuvant (ExteNET data)",
    },
}


def _fallback_pathway_explainability(clinical: ClinicalInput, protocols: list[dict]) -> list[dict]:
    """Deterministic NCCN/ESMO explainability from static library."""
    result = []
    for p in protocols:
        name = p.get("protocol_name", "")
        # Try exact match, then partial match
        explain = _PATHWAY_LIBRARY.get(name)
        if not explain:
            for key in _PATHWAY_LIBRARY:
                if key.lower() in name.lower() or name.lower() in key.lower():
                    explain = _PATHWAY_LIBRARY[key]
                    break
        if not explain:
            explain = {
                "nccn_category": f"Category 2A — {p.get('guideline_source', 'NCCN')} recommended protocol for this subtype",
                "esmo_grade": "Grade B — Evidence from well-conducted clinical trials",
                "trial_evidence": "Multiple phase II/III trials in this indication",
                "mechanism": "Multi-agent regimen targeting tumour-specific molecular vulnerabilities identified in this patient's biomarker profile.",
                "who_benefits_most": f"Patients with {p.get('guideline_source', 'this')} guideline-aligned indications for this protocol.",
                "monitoring": "CBC, liver function, cardiac function, clinical toxicity assessment per institutional protocol",
                "alternative_if_intolerant": "Please refer to the full NCCN or ESMO guideline table for alternative regimens",
            }
        result.append({**p, "guideline_explainability": explain})
    return result

