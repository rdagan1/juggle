import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, func, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class CourseSource(str, enum.Enum):
    email = "email"
    manual = "manual"
    upload = "upload"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[CourseSource] = mapped_column(SAEnum(CourseSource), default=CourseSource.email)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="courses")
    deadlines: Mapped[list["Deadline"]] = relationship("Deadline", back_populates="course", lazy="select")
    grades: Mapped[list["Grade"]] = relationship("Grade", back_populates="course", lazy="select")
