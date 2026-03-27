"""Parsed emails log endpoint."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.parsed_email import ParsedEmail
from app.models.user import User

router = APIRouter(prefix="/api/emails", tags=["emails"])
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
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("")
async def get_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    offset = (page - 1) * page_size

    result = await db.execute(
        select(ParsedEmail)
        .where(ParsedEmail.user_id == user.id)
        .order_by(ParsedEmail.received_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    emails = result.scalars().all()

    return {
        "emails": [
            {
                "id": str(e.id),
                "subject": e.subject,
                "sender": e.sender,
                "received_at": e.received_at.isoformat(),
                "parse_status": e.parse_status.value,
                "attachment_count": e.attachment_count,
                "forwarded_at": e.forwarded_at.isoformat() if e.forwarded_at else None,
            }
            for e in emails
        ]
    }
