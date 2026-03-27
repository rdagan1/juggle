import uuid
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
import enum


class EffortInputMethod(str, enum.Enum):
    button = "button"
    typed = "typed"


class EffortRecordType(str, enum.Enum):
    assignment = "assignment"
    exam = "exam"


class EffortRecord(Base):
    """Anonymous effort records — no user_id by design."""
    __tablename__ = "effort_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    assignment_label: Mapped[str] = mapped_column(String(255), nullable=False)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hours_spent: Mapped[float] = mapped_column(Float, nullable=False)
    input_method: Mapped[EffortInputMethod] = mapped_column(SAEnum(EffortInputMethod), default=EffortInputMethod.button)
    record_type: Mapped[EffortRecordType] = mapped_column(SAEnum(EffortRecordType), default=EffortRecordType.assignment)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EffortAggregate(Base):
    __tablename__ = "effort_aggregates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    assignment_label: Mapped[str] = mapped_column(String(255), nullable=False)
    record_type: Mapped[EffortRecordType] = mapped_column(SAEnum(EffortRecordType), nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    mean_hours: Mapped[float] = mapped_column(Float, nullable=False)
    p25_hours: Mapped[float] = mapped_column(Float, nullable=False)
    p75_hours: Mapped[float] = mapped_column(Float, nullable=False)
    last_computed: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
