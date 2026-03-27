import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    virtual_email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    google_calendar_token: Mapped[str | None] = mapped_column(String, nullable=True)  # AES-256 encrypted
    work_calendar_token: Mapped[str | None] = mapped_column(String, nullable=True)  # AES-256 encrypted
    preferences: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    gio_memory: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    verification_code_expires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    courses: Mapped[list["Course"]] = relationship("Course", back_populates="user", lazy="select")
    parsed_emails: Mapped[list["ParsedEmail"]] = relationship("ParsedEmail", back_populates="user", lazy="select")
    conversation_history: Mapped[list["ConversationHistory"]] = relationship("ConversationHistory", back_populates="user", lazy="select")
