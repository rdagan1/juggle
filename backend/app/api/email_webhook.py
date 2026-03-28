"""Mailgun inbound email webhook."""
import hashlib
import hmac
from datetime import datetime, timezone

from fastapi import APIRouter, Form, HTTPException, UploadFile, File, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.config import get_settings
from app.database import get_db
from app.models.parsed_email import ParsedEmail, ParseStatus
from app.models.pdf_attachment import PdfAttachment, PdfParseStatus
from app.models.user import User

router = APIRouter(prefix="/api/email", tags=["email"])
settings = get_settings()


def _verify_mailgun_signature(timestamp: str, token: str, signature: str) -> bool:
    value = f"{timestamp}{token}".encode()
    expected = hmac.new(settings.mailgun_api_key.encode(), value, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/inbound")
async def inbound_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = await request.form()

    # Mailgun signature verification (skip in dev if key not set)
    if settings.mailgun_api_key:
        timestamp = form.get("timestamp", "")
        token = form.get("token", "")
        signature = form.get("signature", "")
        if not _verify_mailgun_signature(timestamp, token, signature):
            raise HTTPException(status_code=403, detail="Invalid Mailgun signature")

    recipient = form.get("recipient", "")
    sender = form.get("sender", "")
    subject = form.get("subject", "")

    # Find user by virtual_email
    result = await db.execute(select(User).where(User.virtual_email == recipient))
    user = result.scalar_one_or_none()
    if not user:
        # Try stripping alias
        result = await db.execute(select(User).where(User.virtual_email == recipient.lower()))
        user = result.scalar_one_or_none()
    if not user:
        return {"status": "ignored", "reason": "no user for recipient"}

    # Count attachments
    attachment_count = int(form.get("attachment-count", 0))

    # Store parsed_email row immediately
    parsed_email = ParsedEmail(
        user_id=user.id,
        received_at=datetime.now(timezone.utc),
        subject=subject,
        sender=sender,
        attachment_count=attachment_count,
        parse_status=ParseStatus.pending,
    )
    db.add(parsed_email)
    await db.flush()

    # Queue forwarding task if enabled
    if user.preferences.get("forward_emails", True):
        from app.workers.celery_app import forward_email_task
        forward_email_task.delay(
            user_email=user.email,
            raw_mime=form.get("body-mime", ""),
            email_id=str(parsed_email.id),
        )

    # Queue PDF attachment tasks
    for i in range(1, attachment_count + 1):
        attachment = form.get(f"attachment-{i}")
        filename = form.get(f"attachment-{i}", f"attachment-{i}.pdf")
        if hasattr(attachment, "filename"):
            filename = attachment.filename

        if not str(filename).lower().endswith(".pdf"):
            continue

        pdf_attachment = PdfAttachment(
            email_id=parsed_email.id,
            user_id=user.id,
            filename=str(filename),
            parse_status=PdfParseStatus.pending,
        )
        db.add(pdf_attachment)
        await db.flush()

        # Store PDF bytes in R2/S3 or local folder — avoids passing them through Redis.
        from app.workers.celery_app import process_pdf_task
        from app.services import storage
        if hasattr(attachment, "read"):
            pdf_bytes = await attachment.read()
            storage_key = f"emails/{user.id}/{pdf_attachment.id}.pdf"
            await storage.upload_async(storage_key, pdf_bytes)
            pdf_attachment.storage_url = storage_key
            process_pdf_task.delay(
                pdf_attachment_id=str(pdf_attachment.id),
                user_id=str(user.id),
                email_id=str(parsed_email.id),
                filename=str(filename),
                storage_key=storage_key,
            )

    return {"status": "ok", "email_id": str(parsed_email.id)}
