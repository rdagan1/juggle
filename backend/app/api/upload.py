"""Manual PDF upload endpoint."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.uploaded_document import UploadedDocument, UploadedDocumentParseStatus

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

    from app.workers.celery_app import process_uploaded_pdf_task
    process_uploaded_pdf_task.delay(
        document_id=str(doc.id),
        user_id=str(user.id),
        filename=file.filename,
        pdf_bytes=pdf_bytes.hex(),
    )

    return {"document_id": str(doc.id), "status": "processing"}
