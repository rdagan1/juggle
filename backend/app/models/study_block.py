import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class StudyBlockStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    missed = "missed"


class StudyBlock(Base):
    __tablename__ = "study_blocks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    deadline_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("deadlines.id", ondelete="SET NULL"), nullable=True)
    gcal_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[StudyBlockStatus] = mapped_column(SAEnum(StudyBlockStatus), default=StudyBlockStatus.scheduled)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
