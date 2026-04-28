import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    patient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    patient_name: Mapped[str | None] = mapped_column(String(255))
    patient_age: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        Enum(
            "draft", "under_analysis", "treatment_decided",
            "ongoing", "follow_up", "closed",
            name="case_status"
        ),
        default="draft",
        nullable=False,
    )
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    # relationships
    doctor: Mapped["User"] = relationship("User", foreign_keys=[doctor_id], back_populates="cases_as_doctor")
    clinical_data: Mapped["ClinicalData | None"] = relationship("ClinicalData", back_populates="case", uselist=False)
    results: Mapped[list["Result"]] = relationship("Result", back_populates="case", order_by="Result.version")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="case")
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="case")
    doctor_notes: Mapped[list["DoctorNote"]] = relationship("DoctorNote", back_populates="case")
    second_opinions: Mapped[list["SecondOpinion"]] = relationship("SecondOpinion", back_populates="case")


# Avoid circular import issues by importing here
from models.clinical_data import ClinicalData  # noqa: E402, F401
from models.result import Result  # noqa: E402, F401
from models.report import Report  # noqa: E402, F401
from models.audit_log import AuditLog  # noqa: E402, F401
from models.doctor_note import DoctorNote  # noqa: E402, F401
from models.second_opinion import SecondOpinion  # noqa: E402, F401
from models.user import User  # noqa: E402, F401
