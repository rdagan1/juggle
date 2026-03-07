import uuid
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PdfParseCache(Base):
    __tablename__ = "pdf_parse_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pdf_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    parse_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    parsed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
