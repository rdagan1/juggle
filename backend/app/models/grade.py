import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Float, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class GradeType(str, enum.Enum):
    assignment = "assignment"
    exam = "exam"
    bonus = "bonus"
    final = "final"


class GradeSource(str, enum.Enum):
    email = "email"
    upload = "upload"
    manual = "manual"


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("deadlines.id", ondelete="SET NULL"), nullable=True)
    grade: Mapped[float] = mapped_column(Float, nullable=False)
    max_grade: Mapped[float] = mapped_column(Float, default=100.0)
    grade_type: Mapped[GradeType] = mapped_column(SAEnum(GradeType), default=GradeType.assignment)
    source: Mapped[GradeSource] = mapped_column(SAEnum(GradeSource), default=GradeSource.email)
    source_pdf_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("pdf_attachments.id", ondelete="SET NULL"), nullable=True)
    assignment_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    course: Mapped["Course"] = relationship("Course", back_populates="grades")
