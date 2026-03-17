"""
services/case_service.py
CRUD and business logic for cases.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.case import Case
from models.clinical_data import ClinicalData
from models.result import Result
from models.audit_log import AuditLog
from schemas import CaseCreate, CaseUpdate


async def _audit(db: AsyncSession, user_id: uuid.UUID, case_id: uuid.UUID | None,
                 action: str, details: dict, ip: str = "") -> None:
    log = AuditLog(user_id=user_id, case_id=case_id, action=action, details=details, ip_address=ip)
    db.add(log)


async def list_cases(db: AsyncSession, doctor_id: uuid.UUID,
                     page: int = 1, limit: int = 20,
                     sort: str = "created_at", order: str = "desc") -> tuple[list[Case], int]:
    offset = (page - 1) * limit
    col = getattr(Case, sort, Case.created_at)
    ord_col = col.desc() if order == "desc" else col.asc()

    q = select(Case).where(Case.doctor_id == doctor_id, Case.is_deleted == False).order_by(ord_col)
    count_q = select(func.count()).select_from(Case).where(Case.doctor_id == doctor_id, Case.is_deleted == False)

    total = (await db.execute(count_q)).scalar_one()
    result = await db.execute(q.offset(offset).limit(limit))
    return list(result.scalars().all()), total


async def get_case(db: AsyncSession, case_id: uuid.UUID, doctor_id: uuid.UUID) -> Case | None:
    q = select(Case).where(Case.id == case_id, Case.doctor_id == doctor_id, Case.is_deleted == False)
    r = await db.execute(q)
    return r.scalar_one_or_none()


async def create_case(db: AsyncSession, doctor_id: uuid.UUID, data: CaseCreate,
                      ip: str = "") -> Case:
    case = Case(doctor_id=doctor_id, **data.model_dump(exclude_none=True))
    db.add(case)
    await db.flush()
    await _audit(db, doctor_id, case.id, "case_created", {"patient_name": data.patient_name}, ip)
    return case


async def update_case(db: AsyncSession, case: Case, data: CaseUpdate,
                      doctor_id: uuid.UUID, ip: str = "") -> Case:
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(case, k, v)
    case.updated_at = datetime.now(timezone.utc)
    await _audit(db, doctor_id, case.id, "case_updated", data.model_dump(exclude_none=True), ip)
    return case


async def soft_delete_case(db: AsyncSession, case: Case, doctor_id: uuid.UUID, ip: str = "") -> None:
    case.is_deleted = True
    case.updated_at = datetime.now(timezone.utc)
    await _audit(db, doctor_id, case.id, "case_deleted", {}, ip)


async def get_case_history(db: AsyncSession, case_id: uuid.UUID) -> list[Result]:
    q = select(Result).where(Result.case_id == case_id, Result.is_simulation == False).order_by(Result.version)
    r = await db.execute(q)
    return list(r.scalars().all())


async def save_clinical_data(db: AsyncSession, case_id: uuid.UUID, clinical_dict: dict,
                             doctor_id: uuid.UUID, ip: str = "") -> ClinicalData:
    # Upsert
    existing_q = select(ClinicalData).where(ClinicalData.case_id == case_id)
    existing = (await db.execute(existing_q)).scalar_one_or_none()

    if existing:
        for k, v in clinical_dict.items():
            if v is not None:
                setattr(existing, k, v)
        cd = existing
    else:
        cd = ClinicalData(case_id=case_id, **clinical_dict)
        db.add(cd)

    await db.flush()
    await _audit(db, doctor_id, case_id, "clinical_data_saved", {"fields": list(clinical_dict.keys())}, ip)
    return cd


async def get_clinical_data(db: AsyncSession, case_id: uuid.UUID) -> ClinicalData | None:
    q = select(ClinicalData).where(ClinicalData.case_id == case_id)
    r = await db.execute(q)
    return r.scalar_one_or_none()


async def save_result(db: AsyncSession, case_id: uuid.UUID, pipeline_result,
                      is_simulation: bool = False, doctor_id: uuid.UUID | None = None) -> Result:
    # Get next version number
    version_q = select(func.max(Result.version)).where(Result.case_id == case_id, Result.is_simulation == False)
    max_ver = (await db.execute(version_q)).scalar_one() or 0
    version = max_ver + 1 if not is_simulation else max_ver

    result = Result(
        case_id=case_id,
        version=version,
        molecular_subtype=pipeline_result.molecular_subtype,
        subtype_confidence=pipeline_result.subtype_confidence,
        recommendations=pipeline_result.recommendations,
        alerts=pipeline_result.alerts,
        rule_trace=pipeline_result.rule_trace,
        is_simulation=is_simulation,
    )
    db.add(result)
    await db.flush()

    if doctor_id and not is_simulation:
        await _audit(db, doctor_id, case_id, "analysis_run", {"version": version}, "")

    return result
