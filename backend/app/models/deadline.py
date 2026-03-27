import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class DeadlineType(str, enum.Enum):
    assignment = "assignment"
    exam = "exam"
    lecture = "lecture"
    announcement = "announcement"


class DeadlineStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    missed = "missed"


class DeadlineSource(str, enum.Enum):
    email = "email"
    manual = "manual"
    upload = "upload"


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[DeadlineType] = mapped_column(SAEnum(DeadlineType), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[DeadlineStatus] = mapped_column(SAEnum(DeadlineStatus), default=DeadlineStatus.pending)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[DeadlineSource] = mapped_column(SAEnum(DeadlineSource), default=DeadlineSource.email)
    source_pdf_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pdf_attachments.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    course: Mapped["Course"] = relationship("Course", back_populates="deadlines")
    exam_sittings: Mapped[list["ExamSitting"]] = relationship("ExamSitting", back_populates="deadline", lazy="select")
    source_pdf: Mapped["PdfAttachment | None"] = relationship("PdfAttachment", foreign_keys=[source_pdf_id], lazy="select")
