"""Inbound email webhook — POST /webhooks/email/inbound"""
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Form, UploadFile, File, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.email import ParsedEmail, PdfAttachment
from app.models.user import User
from app.services.mailgun import forward_email
from app.services.storage import upload_pdf
from app.tasks.pdf_pipeline import process_pdf_attachment

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/email/inbound")
async def inbound_email(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle inbound email from Mailgun/Postmark.

    Steps (SLA: forward before enqueue):
    1. Parse to/from/subject/attachments from payload
    2. Look up user by virtual_email
    3. If preferences.forward_emails == true: forward email first
    4. Insert parsed_emails row
    5. For each PDF: upload to S3, insert pdf_attachments row, enqueue Celery task
    6. Return 200 immediately
    """
    form = await request.form()
    payload = dict(form)

    to_address = payload.get("recipient") or payload.get("To") or ""
    from_address = payload.get("sender") or payload.get("From") or ""
    subject = payload.get("subject") or payload.get("Subject") or ""
    body_text = payload.get("body-plain") or payload.get("stripped-text") or ""

    # Collect PDF attachments from multipart form
    pdf_files: list[tuple[str, bytes]] = []
    attachment_count = int(payload.get("attachment-count", 0))
    for i in range(1, attachment_count + 1):
        att = form.get(f"attachment-{i}")
        if att and hasattr(att, "filename") and att.filename.lower().endswith(".pdf"):
            content = await att.read()
            pdf_files.append((att.filename, content))

    # Look up user by virtual_email
    result = await db.execute(select(User).where(User.virtual_email == to_address))
    user = result.scalar_one_or_none()

    if not user:
        # Unknown recipient — still return 200 to avoid Mailgun retries
        return {"status": "ok", "detail": "user not found"}

    # Step 3: Forward BEFORE enqueuing (SLA requirement)
    if user.preferences.get("forward_emails"):
        await forward_email(
            to=user.email,
            subject=subject,
            from_address=from_address,
            text=body_text,
            attachments=pdf_files,
        )

    # Step 4: Insert parsed_emails row
    parsed_email = ParsedEmail(
        user_id=user.id,
        from_address=from_address,
        to_address=to_address,
        subject=subject,
        parse_status="pending",
        raw_payload={k: v for k, v in payload.items() if isinstance(v, str)},
    )
    db.add(parsed_email)
    await db.flush()  # get the ID

    # Step 5: Upload each PDF to S3, insert row, enqueue task
    for filename, content in pdf_files:
        storage_url = upload_pdf(content, filename, user.id)
        attachment = PdfAttachment(
            parsed_email_id=parsed_email.id,
            user_id=user.id,
            filename=filename,
            storage_url=storage_url,
            parse_status="pending",
        )
        db.add(attachment)
        await db.flush()
        process_pdf_attachment.delay(str(attachment.id))

    await db.commit()
    return {"status": "ok"}
