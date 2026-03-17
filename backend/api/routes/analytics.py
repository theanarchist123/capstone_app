"""api/routes/analytics.py"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, extract, case as sql_case
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.case import Case
from models.result import Result
from models.clinical_data import ClinicalData
from schemas import SuccessResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=SuccessResponse)
async def summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(func.count()).select_from(Case).where(
        Case.doctor_id == current_user.id, Case.is_deleted == False
    )
    total = (await db.execute(base)).scalar_one()
    active = (await db.execute(base.where(Case.status.in_(["under_analysis", "ongoing", "draft"])))).scalar_one()
    completed = (await db.execute(base.where(Case.status.in_(["treatment_decided", "closed"])))).scalar_one()

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_cases = (await db.execute(
        select(func.count()).select_from(Case).where(
            Case.doctor_id == current_user.id,
            Case.is_deleted == False,
            Case.created_at >= month_start,
        )
    )).scalar_one()

    return SuccessResponse(data={
        "total_cases": total,
        "active_cases": active,
        "completed_cases": completed,
        "cases_this_month": month_cases,
    })


@router.get("/subtypes", response_model=SuccessResponse)
async def subtypes_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Join cases → results
    q = (select(Result.molecular_subtype, func.count().label("count"))
         .join(Case, Result.case_id == Case.id)
         .where(Case.doctor_id == current_user.id, Case.is_deleted == False,
                Result.is_simulation == False)
         .group_by(Result.molecular_subtype))
    rows = (await db.execute(q)).all()
    return SuccessResponse(data=[{"subtype": r[0], "count": r[1]} for r in rows])


@router.get("/stages", response_model=SuccessResponse)
async def stages_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (select(ClinicalData.stage, func.count().label("count"))
         .join(Case, ClinicalData.case_id == Case.id)
         .where(Case.doctor_id == current_user.id, Case.is_deleted == False,
                ClinicalData.stage != None)
         .group_by(ClinicalData.stage))
    rows = (await db.execute(q)).all()
    return SuccessResponse(data=[{"stage": r[0], "count": r[1]} for r in rows])


@router.get("/biomarkers", response_model=SuccessResponse)
async def biomarker_frequency(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns positivity rate for each receptor/marker."""
    fields = ["er_status", "pr_status", "her2_status", "pdl1_status",
              "brca1_status", "brca2_status", "pik3ca_status", "tp53_status"]
    results = []
    for field in fields:
        col = getattr(ClinicalData, field)
        total_q = (select(func.count()).select_from(ClinicalData)
                   .join(Case, ClinicalData.case_id == Case.id)
                   .where(Case.doctor_id == current_user.id, Case.is_deleted == False, col != None))
        pos_q = (select(func.count()).select_from(ClinicalData)
                 .join(Case, ClinicalData.case_id == Case.id)
                 .where(Case.doctor_id == current_user.id, Case.is_deleted == False, col == "Positive"))
        total = (await db.execute(total_q)).scalar_one()
        positive = (await db.execute(pos_q)).scalar_one()
        results.append({
            "biomarker": field.replace("_status", "").upper(),
            "positive": positive,
            "total": total,
            "positivity_rate": round(positive / total, 3) if total else 0,
        })
    return SuccessResponse(data=results)


@router.get("/treatments", response_model=SuccessResponse)
async def treatment_frequency(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (select(Result.recommendations)
         .join(Case, Result.case_id == Case.id)
         .where(Case.doctor_id == current_user.id, Case.is_deleted == False,
                Result.is_simulation == False, Result.recommendations != None))
    rows = (await db.execute(q)).scalars().all()
    freq: dict[str, int] = {}
    for recs in rows:
        if isinstance(recs, list):
            for r in recs:
                name = r.get("protocol_name", "Unknown")
                freq[name] = freq.get(name, 0) + 1
    data = sorted([{"protocol": k, "count": v} for k, v in freq.items()], key=lambda x: -x["count"])
    return SuccessResponse(data=data)


@router.get("/alerts", response_model=SuccessResponse)
async def alert_frequency(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (select(Result.alerts)
         .join(Case, Result.case_id == Case.id)
         .where(Case.doctor_id == current_user.id, Case.is_deleted == False,
                Result.is_simulation == False, Result.alerts != None))
    rows = (await db.execute(q)).scalars().all()
    freq: dict[str, int] = {}
    for alerts in rows:
        if isinstance(alerts, list):
            for a in alerts:
                atype = a.get("alert_type", "Unknown")
                freq[atype] = freq.get(atype, 0) + 1
    return SuccessResponse(data=sorted([{"alert_type": k, "count": v} for k, v in freq.items()], key=lambda x: -x["count"]))


@router.get("/monthly", response_model=SuccessResponse)
async def monthly_volume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Case count per month for the last 12 months."""
    q = (select(
            extract("year", Case.created_at).label("year"),
            extract("month", Case.created_at).label("month"),
            func.count().label("count"),
         )
         .where(Case.doctor_id == current_user.id, Case.is_deleted == False)
         .group_by("year", "month")
         .order_by("year", "month")
         .limit(12))
    rows = (await db.execute(q)).all()
    return SuccessResponse(data=[{"year": int(r[0]), "month": int(r[1]), "count": r[2]} for r in rows])
