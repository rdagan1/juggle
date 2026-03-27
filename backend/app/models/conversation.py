import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class ConversationRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class InputMethod(str, enum.Enum):
    button = "button"
    typed = "typed"
    unknown = "unknown"


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[ConversationRole] = mapped_column(SAEnum(ConversationRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    input_method: Mapped[InputMethod] = mapped_column(SAEnum(InputMethod), default=InputMethod.unknown)
    template_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    buttons: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    navigate_hint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string for extra context
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="conversation_history")
