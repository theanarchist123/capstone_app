import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ─── User ───────────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "doctor"
    hospital: str | None = None
    designation: str | None = None
    license_number: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: str | None = None
    hospital: str | None = None
    designation: str | None = None
    license_number: str | None = None


class UserOut(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Auth ────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# ─── Case ────────────────────────────────────────────────────────────────────
class CaseCreate(BaseModel):
    patient_name: str | None = None
    patient_age: int | None = None
    patient_id: uuid.UUID | None = None
    tags: list[str] | None = None


class CaseUpdate(BaseModel):
    status: str | None = None
    tags: list[str] | None = None


# ─── Clinical Data ─────────────────────────────────────────────────────────
# Defined BEFORE CaseOut so CaseOut can reference them without forward refs
class ClinicalDataCreate(BaseModel):
    tumour_size: float | None = None
    stage: str | None = None
    grade: int | None = None
    histological_type: str | None = None
    lymph_nodes_involved: bool | None = None
    lymph_node_count: int | None = None

    er_status: str | None = None
    pr_status: str | None = None
    her2_status: str | None = None
    ki67_percent: float | None = None
    pdl1_status: str | None = None

    brca1_status: str | None = None
    brca2_status: str | None = None
    pik3ca_status: str | None = None
    tp53_status: str | None = None
    cyclin_d1: str | None = None
    top2a: str | None = None
    bcl2: str | None = None

    tils_percent: float | None = None
    oncotype_dx_score: float | None = None
    mammaprint: str | None = None
    pam50: str | None = None

    lvef_percent: float | None = None
    menopausal_status: str | None = None
    ecog_score: int | None = None
    comorbidities: dict[str, Any] | None = None
    medications: str | None = None
    allergies: str | None = None


class ClinicalDataOut(ClinicalDataCreate):
    id: uuid.UUID
    case_id: uuid.UUID
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Result Summary (embedded in CaseOut) ────────────────────────────────────
class ResultSummary(BaseModel):
    """Lightweight result embedded in CaseOut to avoid lazy-load serialization issues."""
    id: uuid.UUID
    version: int
    molecular_subtype: str | None
    subtype_confidence: float | None
    recommendations: Any | None
    alerts: Any | None
    rule_trace: Any | None
    is_simulation: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── CaseOut ─────────────────────────────────────────────────────────────────
class CaseOut(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_name: str | None
    patient_age: int | None
    status: str
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime
    clinical_data: ClinicalDataOut | None = None
    results: list[ResultSummary] | None = None

    model_config = {"from_attributes": True}


# ─── Analysis ────────────────────────────────────────────────────────────────
class AnalysisResult(BaseModel):
    molecular_subtype: str
    subtype_confidence: float
    recommendations: list[dict[str, Any]]
    alerts: list[dict[str, Any]]
    rule_trace: list[dict[str, Any]]
    version: int


class SimulationRequest(BaseModel):
    overrides: ClinicalDataCreate


class SimulationResult(AnalysisResult):
    diff_vs_baseline: dict[str, Any] | None = None


# ─── Report ──────────────────────────────────────────────────────────────────
class ReportOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    file_name: str
    file_url: str
    file_type: str
    extracted_raw: dict[str, Any] | None
    extraction_confidence: float | None
    verified_by_doctor: bool
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ─── Notification ────────────────────────────────────────────────────────────
class NotificationOut(BaseModel):
    id: uuid.UUID
    message: str
    type: str
    read: bool
    link: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Second Opinion ───────────────────────────────────────────────────────────
class SecondOpinionCreate(BaseModel):
    case_id: uuid.UUID
    reviewing_doctor_id: uuid.UUID | None = None


class SecondOpinionUpdate(BaseModel):
    notes: str
    status: str = "completed"


class SecondOpinionOut(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    requesting_doctor_id: uuid.UUID
    reviewing_doctor_id: uuid.UUID | None
    status: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Analytics ───────────────────────────────────────────────────────────────
class AnalyticsSummary(BaseModel):
    total_cases: int
    active_cases: int
    completed_cases: int
    cases_this_month: int


# ─── Standard response wrappers ──────────────────────────────────────────────
class SuccessResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "OK"


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str
    code: int


class PaginatedResponse(BaseModel):
    success: bool = True
    data: list[Any]
    total: int
    page: int
    limit: int
