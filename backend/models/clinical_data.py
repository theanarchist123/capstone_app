import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalData(Base):
    __tablename__ = "clinical_data"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), unique=True, nullable=False)

    # Tumour characteristics
    tumour_size: Mapped[float | None] = mapped_column(Float)  # cm
    stage: Mapped[str | None] = mapped_column(String(10))
    grade: Mapped[int | None] = mapped_column(Integer)
    histological_type: Mapped[str | None] = mapped_column(String(255))
    lymph_nodes_involved: Mapped[bool | None]
    lymph_node_count: Mapped[int | None] = mapped_column(Integer)

    # Receptor status
    er_status: Mapped[str | None] = mapped_column(String(50))    # Positive / Negative / Unknown
    pr_status: Mapped[str | None] = mapped_column(String(50))
    her2_status: Mapped[str | None] = mapped_column(String(50))
    ki67_percent: Mapped[float | None] = mapped_column(Float)
    pdl1_status: Mapped[str | None] = mapped_column(String(50))

    # Mutations
    brca1_status: Mapped[str | None] = mapped_column(String(50))
    brca2_status: Mapped[str | None] = mapped_column(String(50))
    pik3ca_status: Mapped[str | None] = mapped_column(String(50))
    tp53_status: Mapped[str | None] = mapped_column(String(50))
    cyclin_d1: Mapped[str | None] = mapped_column(String(50))
    top2a: Mapped[str | None] = mapped_column(String(50))
    bcl2: Mapped[str | None] = mapped_column(String(50))

    # Immune & genomic
    tils_percent: Mapped[float | None] = mapped_column(Float)
    oncotype_dx_score: Mapped[float | None] = mapped_column(Float)
    mammaprint: Mapped[str | None] = mapped_column(String(50))
    pam50: Mapped[str | None] = mapped_column(String(100))

    # Systemic health
    lvef_percent: Mapped[float | None] = mapped_column(Float)
    menopausal_status: Mapped[str | None] = mapped_column(String(50))
    ecog_score: Mapped[int | None] = mapped_column(Integer)
    comorbidities: Mapped[dict | None] = mapped_column(JSON)
    medications: Mapped[str | None] = mapped_column(Text)
    allergies: Mapped[str | None] = mapped_column(Text)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    case: Mapped["Case"] = relationship("Case", back_populates="clinical_data")


from models.case import Case  # noqa: E402, F401
