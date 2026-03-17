"""api/routes/analysis.py"""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from schemas import AnalysisResult, SimulationRequest, SimulationResult, SuccessResponse
from services.case_service import (
    get_case, get_clinical_data, save_result, update_case, CaseUpdate
)
from engine.biomarker_algorithm import ClinicalInput, run_pipeline

router = APIRouter(prefix="/api/cases/{case_id}", tags=["analysis"])


def _clinical_to_input(cd) -> ClinicalInput:
    """Convert ClinicalData ORM object → ClinicalInput dataclass."""
    return ClinicalInput(
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


@router.post("/analyse", response_model=SuccessResponse)
async def run_analysis(
    case_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")

    cd = await get_clinical_data(db, case_id)
    if not cd:
        raise HTTPException(400, "Submit clinical data before running analysis")

    clinical_input = _clinical_to_input(cd)
    pipeline_result = run_pipeline(clinical_input)

    result = await save_result(db, case_id, pipeline_result, is_simulation=False, doctor_id=current_user.id)

    # Update case status
    from schemas import CaseUpdate as CU
    await update_case(db, case, CU(status="under_analysis"), current_user.id, request.client.host)

    await db.commit()

    return SuccessResponse(
        data=AnalysisResult(
            molecular_subtype=result.molecular_subtype,
            subtype_confidence=result.subtype_confidence,
            recommendations=result.recommendations,
            alerts=result.alerts,
            rule_trace=result.rule_trace,
            version=result.version,
        ),
        message="Analysis complete",
    )


@router.post("/analyse/simulate", response_model=SuccessResponse)
async def run_simulation(
    case_id: uuid.UUID,
    body: SimulationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")

    # Get baseline
    cd = await get_clinical_data(db, case_id)
    baseline_input = _clinical_to_input(cd) if cd else ClinicalInput()

    # Apply overrides from simulation request
    overrides = body.overrides.model_dump(exclude_none=True)
    sim_input_dict = {
        f: getattr(baseline_input, f, None)
        for f in ClinicalInput.__dataclass_fields__
    }
    sim_input_dict.update(overrides)
    sim_input = ClinicalInput(**{k: v for k, v in sim_input_dict.items() if k in ClinicalInput.__dataclass_fields__})

    # Run pipeline (not saved)
    sim_result = run_pipeline(sim_input)

    # Compute diff vs baseline
    diff: dict[str, Any] = {}
    if cd:
        baseline_result = run_pipeline(baseline_input)
        if baseline_result.molecular_subtype != sim_result.molecular_subtype:
            diff["molecular_subtype"] = {
                "baseline": baseline_result.molecular_subtype,
                "simulated": sim_result.molecular_subtype,
            }
        conf_change = round(sim_result.subtype_confidence - baseline_result.subtype_confidence, 3)
        if conf_change:
            diff["subtype_confidence_delta"] = conf_change
        base_recs = {r["protocol_name"] for r in baseline_result.recommendations}
        sim_recs = {r["protocol_name"] for r in sim_result.recommendations}
        if base_recs != sim_recs:
            diff["recommendations_added"] = list(sim_recs - base_recs)
            diff["recommendations_removed"] = list(base_recs - sim_recs)

    return SuccessResponse(
        data=SimulationResult(
            molecular_subtype=sim_result.molecular_subtype,
            subtype_confidence=sim_result.subtype_confidence,
            recommendations=sim_result.recommendations,
            alerts=sim_result.alerts,
            rule_trace=sim_result.rule_trace,
            version=0,
            diff_vs_baseline=diff,
        ),
        message="Simulation complete (not saved)",
    )
