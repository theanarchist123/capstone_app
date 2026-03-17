"""api/routes/second_opinion.py"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.second_opinion import SecondOpinion
from schemas import SecondOpinionCreate, SecondOpinionOut, SecondOpinionUpdate, SuccessResponse
from services.case_service import get_case

router = APIRouter(prefix="/api/second-opinion", tags=["second_opinion"])


@router.post("/", response_model=SuccessResponse, status_code=201)
async def request_opinion(
    body: SecondOpinionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, body.case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found or not yours")

    opinion = SecondOpinion(
        case_id=body.case_id,
        requesting_doctor_id=current_user.id,
        reviewing_doctor_id=body.reviewing_doctor_id,
        status="pending",
    )
    db.add(opinion)
    await db.commit()
    await db.refresh(opinion)
    return SuccessResponse(data=SecondOpinionOut.model_validate(opinion), message="Second opinion requested")


@router.get("/", response_model=SuccessResponse)
async def list_opinions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(SecondOpinion).where(
        or_(
            SecondOpinion.requesting_doctor_id == current_user.id,
            SecondOpinion.reviewing_doctor_id == current_user.id,
        )
    ).order_by(SecondOpinion.created_at.desc())
    opinions = (await db.execute(q)).scalars().all()
    return SuccessResponse(data=[SecondOpinionOut.model_validate(o) for o in opinions])


@router.patch("/{opinion_id}", response_model=SuccessResponse)
async def submit_review(
    opinion_id: uuid.UUID,
    body: SecondOpinionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(SecondOpinion).where(
        SecondOpinion.id == opinion_id,
        SecondOpinion.reviewing_doctor_id == current_user.id,
    )
    opinion = (await db.execute(q)).scalar_one_or_none()
    if not opinion:
        raise HTTPException(404, "Opinion request not found or not assigned to you")

    opinion.notes = body.notes
    opinion.status = body.status
    await db.commit()
    await db.refresh(opinion)
    return SuccessResponse(data=SecondOpinionOut.model_validate(opinion), message="Review submitted")
