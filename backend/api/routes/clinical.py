"""api/routes/clinical.py"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from schemas import ClinicalDataCreate, ClinicalDataOut, SuccessResponse
from services.case_service import (
    get_case, save_clinical_data, get_clinical_data
)

router = APIRouter(prefix="/api/cases/{case_id}/clinical", tags=["clinical"])


@router.post("/", response_model=SuccessResponse, status_code=201)
async def submit_clinical(
    case_id: uuid.UUID,
    body: ClinicalDataCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")

    cd = await save_clinical_data(
        db, case_id,
        body.model_dump(exclude_none=True),
        current_user.id, request.client.host,
    )
    await db.commit()
    await db.refresh(cd)
    return SuccessResponse(data=ClinicalDataOut.model_validate(cd), message="Clinical data saved")


@router.get("/", response_model=SuccessResponse)
async def get_clinical(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")
    cd = await get_clinical_data(db, case_id)
    if not cd:
        raise HTTPException(404, "Clinical data not yet submitted")
    return SuccessResponse(data=ClinicalDataOut.model_validate(cd))


@router.patch("/", response_model=SuccessResponse)
async def update_clinical(
    case_id: uuid.UUID,
    body: ClinicalDataCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")

    cd = await save_clinical_data(
        db, case_id,
        body.model_dump(exclude_none=True),
        current_user.id, request.client.host,
    )
    await db.commit()
    await db.refresh(cd)
    return SuccessResponse(data=ClinicalDataOut.model_validate(cd), message="Clinical data updated")
