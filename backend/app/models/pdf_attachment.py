import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Integer, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class PdfParseStatus(str, enum.Enum):
    pending = "pending"
    parsed = "parsed"
    unreadable = "unreadable"
    no_events = "no_events"
    failed = "failed"
    cache_hit = "cache_hit"


class PdfAttachment(Base):
    __tablename__ = "pdf_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("parsed_emails.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    parse_status: Mapped[PdfParseStatus] = mapped_column(SAEnum(PdfParseStatus), default=PdfParseStatus.pending)
    document_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_text_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pdf_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    email: Mapped["ParsedEmail | None"] = relationship("ParsedEmail", back_populates="attachments")
