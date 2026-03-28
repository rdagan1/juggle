import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationHistory
from app.models.uploaded_document import UploadedDocument, UploadedDocumentParseStatus
from app.services.gio.attachment_context import _build_attachment_context
from app.services.gio.constants import KNOWN_BUTTON_VALUES
from app.services.gio.llm_handler import llm_handler
from app.services.gio.template_handler import template_handler, _simple_gio_response

_PENDING_TIMEOUT: timedelta = timedelta(minutes=5)
_ERROR_STATUSES: frozenset[UploadedDocumentParseStatus] = frozenset({
    UploadedDocumentParseStatus.failed,
    UploadedDocumentParseStatus.unreadable,
})


async def handle_response(
    user_id: uuid.UUID,
    db: AsyncSession,
    message_id: uuid.UUID | None = None,
    value: str | None = None,
    text: str | None = None,
    input_method: str = "button",
    attachments: list | None = None,
) -> ConversationHistory:
    """Route to template or LLM handler. Returns persisted Gio response."""

    # Fetch context message if provided
    ctx_msg = None
    if message_id:
        result = await db.execute(
            select(ConversationHistory).where(ConversationHistory.id == message_id)
        )
        ctx_msg = result.scalar_one_or_none()

    # Gate on PDF attachment status before going to the LLM.
    for att in (attachments or []):
        if att.type != "pdf":
            continue
        doc_result = await db.execute(
            select(UploadedDocument).where(
                UploadedDocument.id == att.id,
                UploadedDocument.user_id == user_id,
            )
        )
        doc = doc_result.scalar_one_or_none()
        if not doc:
            continue

        if doc.parse_status == UploadedDocumentParseStatus.pending:
            age = datetime.now(timezone.utc) - doc.created_at
            if age > _PENDING_TIMEOUT:
                # Task likely failed without updating the status — treat as error
                return await _simple_gio_response(
                    user_id,
                    db,
                    f'לא הצלחתי לעבד את הקובץ "{doc.filename}". אפשר לנסות להעלות שוב?',
                )
            return await _simple_gio_response(
                user_id,
                db,
                f'הקובץ "{doc.filename}" עדיין בעיבוד — נסה/י לשלוח שוב בעוד כמה רגעים.',
            )

        if doc.parse_status in _ERROR_STATUSES:
            return await _simple_gio_response(
                user_id,
                db,
                f'לא הצלחתי לקרוא את הקובץ "{doc.filename}" — ייתכן שהוא פגום או לא נתמך.',
            )
        # no_events / parsed → fall through to context building

    # Build rich context from DB for any attached items
    context = await _build_attachment_context(db, user_id, attachments or [])

    if value and value in KNOWN_BUTTON_VALUES:
        return await template_handler(user_id, db, value, ctx_msg)
    else:
        return await llm_handler(user_id, db, text or value or "", ctx_msg, context=context)
