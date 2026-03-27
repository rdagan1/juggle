import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Float, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class UploadedDocumentParseStatus(str, enum.Enum):
    pending = "pending"
    parsed = "parsed"
    unreadable = "unreadable"
    no_events = "no_events"
    failed = "failed"


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    parse_status: Mapped[UploadedDocumentParseStatus] = mapped_column(SAEnum(UploadedDocumentParseStatus), default=UploadedDocumentParseStatus.pending)
    inferred_course_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="SET NULL"), nullable=True)
    course_match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    pdf_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inferred_course: Mapped["Course | None"] = relationship("Course", lazy="select")
