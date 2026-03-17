import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _now():
    return datetime.now(timezone.utc)


class Result(Base):
    __tablename__ = "results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    molecular_subtype: Mapped[str | None]
    subtype_confidence: Mapped[float | None] = mapped_column(Float)
    recommendations: Mapped[dict | None] = mapped_column(JSONB)
    alerts: Mapped[dict | None] = mapped_column(JSONB)
    rule_trace: Mapped[dict | None] = mapped_column(JSONB)
    is_simulation: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    case: Mapped["Case"] = relationship("Case", back_populates="results")


from models.case import Case  # noqa: E402, F401
