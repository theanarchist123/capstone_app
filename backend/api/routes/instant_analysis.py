"""api/routes/instant_analysis.py
Stateless analysis endpoint — no case_id needed.
Takes raw clinical data, runs the pipeline + Ollama AI, returns full results.
Auth is OPTIONAL — works for both logged-in users and anonymous/public use.
Used by the onboarding form for real-time results without DB dependency.
"""
from __future__ import annotations

import asyncio
from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Any, Optional

from schemas import ClinicalDataCreate
from engine.biomarker_algorithm import ClinicalInput, run_pipeline
from engine.ai_reasoning import enhance_with_ai, enhance_pathways_with_ai

router = APIRouter(prefix="/api/analyse", tags=["instant-analysis"])

# Optional bearer — does NOT raise 403/401 if header is absent
_optional_bearer = HTTPBearer(auto_error=False)


class InstantAnalysisRequest(BaseModel):
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    clinical_data: ClinicalDataCreate


class InstantAnalysisResponse(BaseModel):
    success: bool = True
    molecular_subtype: str
    subtype_confidence: float
    recommendations: list[dict[str, Any]]
    alerts: list[dict[str, Any]]
    rule_trace: list[dict[str, Any]]
    ai_reasoning: dict[str, Any]
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None


@router.post("/instant", response_model=InstantAnalysisResponse)
async def instant_analysis(
    body: InstantAnalysisRequest,
    # Optional auth — endpoint works even without a valid token
    _creds: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
):
    """
    Run the full clinical intelligence pipeline on submitted form data.

    Authentication is OPTIONAL — the endpoint works for any user, logged-in
    or not, to avoid token-expiry disrupting the clinical workflow.

    Returns:
      - Molecular subtype + confidence
      - 3 ranked treatment paths each enriched with NCCN/ESMO explainability
      - Safety alerts
      - Biomarker rule trace
      - AI narrative (Ollama LLM with deterministic fallback)
    """
    cd = body.clinical_data

    clinical_input = ClinicalInput(
        er_status=cd.er_status or "Unknown",
        pr_status=cd.pr_status or "Unknown",
        her2_status=cd.her2_status or "Unknown",
        ki67_percent=cd.ki67_percent,
        oncotype_dx_score=cd.oncotype_dx_score,
        mammaprint=cd.mammaprint,
        pam50=cd.pam50,
        brca1_status=cd.brca1_status or "Unknown",
        brca2_status=cd.brca2_status or "Unknown",
        pdl1_status=cd.pdl1_status or "Unknown",
        tils_percent=cd.tils_percent,
        pik3ca_status=cd.pik3ca_status or "Unknown",
        tp53_status=cd.tp53_status or "Unknown",
        top2a=cd.top2a or "Unknown",
        bcl2=cd.bcl2 or "Unknown",
        cyclin_d1=cd.cyclin_d1 or "Unknown",
        stage=cd.stage or "II",
        grade=cd.grade or 2,
        lymph_nodes_involved=cd.lymph_nodes_involved or False,
        lymph_node_count=cd.lymph_node_count or 0,
        menopausal_status=cd.menopausal_status or "Unknown",
        ecog_score=cd.ecog_score or 0,
        tumour_size=cd.tumour_size,
        lvef_percent=cd.lvef_percent,
        comorbidities=cd.comorbidities or {},
        medications=cd.medications or "",
        allergies=cd.allergies or "",
    )

    # 1. Deterministic pipeline (fast, always runs)
    pipeline_result = run_pipeline(clinical_input)

    # 2. Concurrently enrich with NCCN/ESMO guideline explainability + Ollama AI narrative
    enriched_paths, ai_reasoning = await asyncio.gather(
        enhance_pathways_with_ai(clinical_input, pipeline_result.recommendations),
        enhance_with_ai(clinical_input, pipeline_result),
    )

    return InstantAnalysisResponse(
        molecular_subtype=pipeline_result.molecular_subtype,
        subtype_confidence=pipeline_result.subtype_confidence,
        recommendations=enriched_paths,
        alerts=pipeline_result.alerts,
        rule_trace=pipeline_result.rule_trace,
        ai_reasoning=ai_reasoning,
        patient_name=body.patient_name,
        patient_age=body.patient_age,
    )
