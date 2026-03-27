import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ExamSittingStatus(str, enum.Enum):
    confirmed = "confirmed"
    optional = "optional"
    cancelled = "cancelled"


class ExamSitting(Base):
    __tablename__ = "exam_sittings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deadline_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("deadlines.id", ondelete="CASCADE"), nullable=False, index=True)
    moed_label: Mapped[str] = mapped_column(String(10), nullable=False)  # "א", "ב", "ג"
    sitting_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ExamSittingStatus] = mapped_column(SAEnum(ExamSittingStatus), default=ExamSittingStatus.optional)
    gcal_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deadline: Mapped["Deadline"] = relationship("Deadline", back_populates="exam_sittings")
