"""Manual PDF upload and download endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from sqlalchemy import select
import io
import redis.asyncio as aioredis

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.uploaded_document import UploadedDocument, UploadedDocumentParseStatus
from app.services import storage

_TASK_ID_TTL = 3600  # seconds — long enough to cover any retry cycle


def _redis() -> aioredis.Redis:
    return aioredis.from_url(get_settings().redis_url, decode_responses=True)


def _task_key(document_id: str) -> str:
    return f"juggle:pdf_task:{document_id}"

router = APIRouter(prefix="/api/upload", tags=["upload"])
settings = get_settings()


async def _get_current_user(token: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("")
async def upload_pdf(
    file: UploadFile = File(...),
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    doc = UploadedDocument(
        user_id=user.id,
        filename=file.filename,
        parse_status=UploadedDocumentParseStatus.pending,
    )
    db.add(doc)
    await db.flush()

    # Store the PDF bytes in R2/S3 or local folder — avoids passing them through Redis.
    storage_key = f"uploads/{user.id}/{doc.id}.pdf"
    await storage.upload_async(storage_key, pdf_bytes)
    doc.storage_url = storage_key

    from app.workers.celery_app import process_uploaded_pdf_task
    task = process_uploaded_pdf_task.delay(
        document_id=str(doc.id),
        user_id=str(user.id),
        filename=file.filename,
        storage_key=storage_key,
    )

    # Persist task ID in Redis so the cancel endpoint can revoke it
    r = _redis()
    await r.set(_task_key(str(doc.id)), task.id, ex=_TASK_ID_TTL)
    await r.aclose()

    return {"document_id": str(doc.id), "status": "processing"}


@router.delete("/{document_id}")
async def cancel_pdf(
    document_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)

    result = await db.execute(
        select(UploadedDocument).where(
            UploadedDocument.id == uuid.UUID(document_id),
            UploadedDocument.user_id == user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.parse_status == UploadedDocumentParseStatus.pending:
        # Revoke the Celery task (works whether queued or running)
        r = _redis()
        task_id = await r.get(_task_key(document_id))
        await r.delete(_task_key(document_id))
        await r.aclose()

        if task_id:
            from app.workers.celery_app import celery_app
            celery_app.control.revoke(task_id, terminate=True, signal="SIGTERM")

        doc.parse_status = UploadedDocumentParseStatus.failed

    # Remove the stored file
    if doc.storage_url:
        await storage.delete_async(doc.storage_url)
        doc.storage_url = None

    return {"status": "cancelled"}


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    result = await db.execute(
        select(UploadedDocument).where(
            UploadedDocument.id == uuid.UUID(document_id),
            UploadedDocument.user_id == user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"parse_status": doc.parse_status.value}


@router.get("/{document_id}")
async def download_pdf(
    document_id: str,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)

    result = await db.execute(
        select(UploadedDocument).where(
            UploadedDocument.id == uuid.UUID(document_id),
            UploadedDocument.user_id == user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc or not doc.storage_url:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        pdf_bytes = await storage.download_async(doc.storage_url)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File no longer available")
    except Exception:
        raise HTTPException(status_code=502, detail="Storage unavailable")

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'},
    )
