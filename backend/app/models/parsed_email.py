import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Integer, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ParseStatus(str, enum.Enum):
    pending = "pending"
    parsed = "parsed"
    unreadable = "unreadable"
    no_events = "no_events"
    failed = "failed"


class ParsedEmail(Base):
    __tablename__ = "parsed_emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)
    forwarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attachment_count: Mapped[int] = mapped_column(Integer, default=0)
    parse_status: Mapped[ParseStatus] = mapped_column(SAEnum(ParseStatus), default=ParseStatus.pending)
    raw_mime: Mapped[str | None] = mapped_column(String, nullable=True)  # stored temporarily
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="parsed_emails")
    attachments: Mapped[list["PdfAttachment"]] = relationship("PdfAttachment", back_populates="email", lazy="select")
