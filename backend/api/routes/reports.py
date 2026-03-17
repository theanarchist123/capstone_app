"""api/routes/reports.py"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.deps import get_current_user
from models.user import User
from models.report import Report
from schemas import ReportOut, SuccessResponse
from services.case_service import get_case
from services.report_service import upload_report, run_nlp_extraction

router = APIRouter(prefix="/api/cases/{case_id}/reports", tags=["reports"])


@router.post("/upload", response_model=SuccessResponse, status_code=201)
async def upload(
    case_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")

    content = await file.read()
    report = await upload_report(db, case_id, file.filename or "report", content, file.content_type or "")
    await db.commit()
    await db.refresh(report)

    # NLP extraction happens in background
    text = content.decode("utf-8", errors="ignore") if report.file_type == "txt" else ""
    if text:
        background_tasks.add_task(run_nlp_extraction, db, report.id, text)

    return SuccessResponse(
        data={
            "report_id": str(report.id),
            "file_name": report.file_name,
            "extraction_status": "queued" if text else "manual_upload_required",
        },
        message="Report uploaded. NLP extraction queued.",
    )


@router.get("/", response_model=SuccessResponse)
async def list_reports(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    case = await get_case(db, case_id, current_user.id)
    if not case:
        raise HTTPException(404, "Case not found")

    q = select(Report).where(Report.case_id == case_id).order_by(Report.uploaded_at.desc())
    reports = (await db.execute(q)).scalars().all()
    return SuccessResponse(data=[ReportOut.model_validate(r) for r in reports])


@router.get("/{report_id}", response_model=SuccessResponse)
async def get_report(
    case_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Report).where(Report.id == report_id, Report.case_id == case_id)
    report = (await db.execute(q)).scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")
    return SuccessResponse(data=ReportOut.model_validate(report))


@router.patch("/{report_id}/verify", response_model=SuccessResponse)
async def verify_report(
    case_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Report).where(Report.id == report_id, Report.case_id == case_id)
    report = (await db.execute(q)).scalar_one_or_none()
    if not report:
        raise HTTPException(404, "Report not found")

    report.verified_by_doctor = True
    await db.commit()
    return SuccessResponse(message="Report verified by physician")
