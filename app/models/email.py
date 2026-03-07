import uuid
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ParsedEmail(Base):
    __tablename__ = "parsed_emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    parse_status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="pending")
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PdfAttachment(Base):
    __tablename__ = "pdf_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parsed_email_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    uploaded_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parse_status: Mapped[str | None] = mapped_column(String(20), nullable=True, default="pending")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
