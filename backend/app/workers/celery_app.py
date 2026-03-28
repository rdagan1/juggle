"""Celery application + task definitions."""
import asyncio
from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "juggle",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Jerusalem",
    enable_utc=True,
    beat_schedule={
        "proactivity-check-every-2h": {
            "task": "app.workers.celery_app.run_proactivity_check_all",
            "schedule": crontab(minute=0, hour="*/2"),
        },
        "effort-aggregator-nightly": {
            "task": "app.workers.celery_app.aggregate_effort",
            "schedule": crontab(minute=0, hour=3),
        },
        "cleanup-pdf-cache": {
            "task": "app.workers.celery_app.cleanup_expired_pdf_cache",
            "schedule": crontab(minute=0, hour=4),
        },
    },
)


def run_async(coro):
    """Run async coroutine in Celery (sync) context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.celery_app.process_pdf_task", bind=True, max_retries=3, time_limit=180, soft_time_limit=150)
def process_pdf_task(self, pdf_attachment_id: str, user_id: str, email_id: str, filename: str, storage_key: str):
    """Process a PDF attachment through the full pipeline."""
    import uuid

    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.pdf_pipeline import run_pipeline
        from app.services.personalization import create_gio_message
        from app.api.chat import push_gio_message
        from app.services.storage import download, delete

        async with AsyncSessionLocal() as db:
            try:
                pdf_bytes_raw = download(storage_key)
                result = await run_pipeline(
                    pdf_bytes=pdf_bytes_raw,
                    user_id=uuid.UUID(user_id),
                    pdf_attachment_id=uuid.UUID(pdf_attachment_id),
                    db=db,
                )

                # Send Gio notification
                status = result.get("status")
                if status == "unreadable":
                    msg = await create_gio_message(
                        uuid.UUID(user_id),
                        "unreadable_pdf",
                        {"filename": filename},
                        db,
                    )
                elif status == "parsed":
                    inserted = result.get("inserted", {})
                    total = sum(inserted.values())
                    if total > 0:
                        template = "post_parse_multiple" if total > 1 else "post_parse_single"
                        msg = await create_gio_message(
                            uuid.UUID(user_id),
                            template,
                            {
                                "filename": filename,
                                "count": str(total),
                                "assignments": str(inserted.get("assignments", 0)),
                                "exams": str(inserted.get("exams", 0)),
                            },
                            db,
                        )
                        await push_gio_message(user_id, msg)

                await db.commit()
                # Clean up stored file after successful processing
                delete(storage_key)
            except Exception as exc:
                await db.rollback()
                raise self.retry(exc=exc, countdown=60)

    run_async(_run())


@celery_app.task(name="app.workers.celery_app.process_uploaded_pdf_task", bind=True, max_retries=3, time_limit=180, soft_time_limit=150)
def process_uploaded_pdf_task(self, document_id: str, user_id: str, filename: str, storage_key: str):
    """Process a manually uploaded PDF."""
    import uuid

    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.pdf_attachment import PdfAttachment, PdfParseStatus
        from app.models.uploaded_document import UploadedDocument, UploadedDocumentParseStatus
        from app.services.pdf_pipeline import run_pipeline
        from app.services.personalization import create_gio_message
        from app.api.chat import push_gio_message
        from app.services.storage import download, delete
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            try:
                pdf_bytes_raw = download(storage_key)

                # Create a synthetic PdfAttachment for the pipeline
                att = PdfAttachment(
                    user_id=uuid.UUID(user_id),
                    filename=filename,
                    parse_status=PdfParseStatus.pending,
                )
                db.add(att)
                await db.flush()

                result = await run_pipeline(
                    pdf_bytes=pdf_bytes_raw,
                    user_id=uuid.UUID(user_id),
                    pdf_attachment_id=att.id,
                    db=db,
                )

                # Update uploaded document status
                doc_result = await db.execute(
                    select(UploadedDocument).where(UploadedDocument.id == uuid.UUID(document_id))
                )
                doc = doc_result.scalar_one_or_none()
                if doc:
                    status_map = {
                        "parsed": UploadedDocumentParseStatus.parsed,
                        "unreadable": UploadedDocumentParseStatus.unreadable,
                        "no_events": UploadedDocumentParseStatus.no_events,
                    }
                    doc.parse_status = status_map.get(result.get("status"), UploadedDocumentParseStatus.failed)
                    if result.get("pdf_hash"):
                        doc.pdf_hash = result["pdf_hash"]

                status = result.get("status")
                if status == "parsed":
                    inserted = result.get("inserted", {})
                    total = sum(inserted.values())
                    if total > 0:
                        template = "post_parse_multiple" if total > 1 else "post_parse_single"
                        msg = await create_gio_message(
                            uuid.UUID(user_id),
                            template,
                            {"filename": filename, "count": str(total)},
                            db,
                        )
                        await push_gio_message(user_id, msg)
                elif status == "unreadable":
                    msg = await create_gio_message(
                        uuid.UUID(user_id),
                        "unreadable_pdf",
                        {"filename": filename},
                        db,
                    )
                    await push_gio_message(user_id, msg)

                await db.commit()
                # Do NOT delete the storage file — users may want to open it via the download endpoint.
            except Exception as exc:
                # Mark the document as failed so it doesn't stay stuck in pending
                try:
                    async with AsyncSessionLocal() as err_db:
                        err_doc = await err_db.get(UploadedDocument, uuid.UUID(document_id))
                        if err_doc and err_doc.parse_status == UploadedDocumentParseStatus.pending:
                            err_doc.parse_status = UploadedDocumentParseStatus.failed
                            await err_db.commit()
                except Exception:
                    pass
                raise self.retry(exc=exc, countdown=60)

    run_async(_run())


@celery_app.task(name="app.workers.celery_app.forward_email_task")
def forward_email_task(user_email: str, raw_mime: str, email_id: str):
    """Forward raw email to user's personal inbox (within 60s SLA)."""
    async def _run():
        from app.services.email_forwarder import forward_email
        from app.database import AsyncSessionLocal
        from app.models.parsed_email import ParsedEmail
        from sqlalchemy import select
        import uuid
        from datetime import datetime, timezone

        await forward_email(user_email, raw_mime)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ParsedEmail).where(ParsedEmail.id == uuid.UUID(email_id))
            )
            email = result.scalar_one_or_none()
            if email:
                email.forwarded_at = datetime.now(timezone.utc)
            await db.commit()

    run_async(_run())


@celery_app.task(name="app.workers.celery_app.run_proactivity_check_all")
def run_proactivity_check_all():
    """Run proactivity check for all active users."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.user import User
        from app.services.scheduler import run_proactivity_check
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User).where(User.is_active == True, User.onboarding_completed == True)
            )
            users = result.scalars().all()
            for user in users:
                try:
                    await run_proactivity_check(user, db)
                except Exception:
                    pass
            await db.commit()

    run_async(_run())


@celery_app.task(name="app.workers.celery_app.aggregate_effort")
def aggregate_effort():
    """Nightly effort aggregation."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.effort_aggregator import compute_aggregates

        async with AsyncSessionLocal() as db:
            await compute_aggregates(db)
            await db.commit()

    run_async(_run())


@celery_app.task(name="app.workers.celery_app.cleanup_expired_pdf_cache")
def cleanup_expired_pdf_cache():
    """Remove expired PDF parse cache entries (90-day TTL)."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.pdf_parse_cache import PdfParseCache
        from sqlalchemy import select, delete
        from datetime import datetime, timezone

        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            await db.execute(
                delete(PdfParseCache).where(
                    PdfParseCache.delete_at < now
                )
            )
            await db.commit()

    run_async(_run())
