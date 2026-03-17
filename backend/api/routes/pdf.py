"""api/routes/pdf.py"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from services.case_service import get_case, get_clinical_data
from services.pdf_service import generate_pdf
from sqlalchemy import select
from models.result import Result

router = APIRouter(prefix="/api/cases/{case_id}/export", tags=["pdf"])


@router.get("/pdf")
async def export_pdf(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")

    cd = await get_clinical_data(db, case_id)
    if not cd:
        raise HTTPException(400, "No clinical data available for this case")

    # Get latest non-simulation result
    q = (select(Result)
         .where(Result.case_id == case_id, Result.is_simulation == False)
         .order_by(Result.version.desc())
         .limit(1))
    result = (await db.execute(q)).scalar_one_or_none()
    if not result:
        raise HTTPException(400, "Run analysis before exporting PDF")

    cd_dict = {
        col.name: getattr(cd, col.name)
        for col in cd.__table__.columns
        if col.name not in ("id", "case_id")
    }

    pdf_bytes = generate_pdf({
        "patient_name": case.patient_name or "Anonymous",
        "patient_age": case.patient_age,
        "case_id": str(case_id),
        "doctor_name": current_user.name,
        "clinical_data": cd_dict,
        "result": {
            "molecular_subtype": result.molecular_subtype,
            "subtype_confidence": result.subtype_confidence,
            "recommendations": result.recommendations or [],
            "alerts": result.alerts or [],
            "rule_trace": result.rule_trace or [],
        },
    })

    media_type = "application/pdf"
    filename = f"CancerCopilot_{case_id}_v{result.version}.pdf"
    return Response(
        content=pdf_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
