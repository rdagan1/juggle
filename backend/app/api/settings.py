"""User settings endpoint."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.manual_update_log import ManualUpdateLog
from app.models.api_models import UserPreferencesIn

router = APIRouter(prefix="/api/settings", tags=["settings"])
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
async def get_settings_endpoint(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    return {
        "virtual_email": user.virtual_email,
        "name": user.name,
        "email": user.email,
        "preferences": user.preferences,
        "has_calendar": bool(user.google_calendar_token),
        "has_work_calendar": bool(user.work_calendar_token),
        "onboarding_completed": user.onboarding_completed,
        "onboarding_step": user.onboarding_step,
    }


@router.patch("")
async def update_settings(
    body: UserPreferencesIn,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    prefs = dict(user.preferences or {})

    updates = body.model_dump(exclude_none=True)
    prefs.update(updates)
    user.preferences = prefs

    return {"message": "Settings updated", "preferences": prefs}


@router.delete("/account")
async def delete_account(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """GDPR full soft-delete."""
    user = await _get_current_user(token, db)
    user.is_active = False
    user.email = f"deleted_{user.id}@deleted.juggle.app"
    user.name = None
    user.virtual_email = None
    user.hashed_password = None
    user.google_calendar_token = None
    user.work_calendar_token = None
    user.gio_memory = {}
    return {"message": "Account deleted"}


@router.get("/manual-updates")
async def get_manual_updates(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_current_user(token, db)
    result = await db.execute(
        select(ManualUpdateLog)
        .where(ManualUpdateLog.user_id == user.id)
        .order_by(ManualUpdateLog.changed_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()
    return {
        "logs": [
            {
                "id": str(l.id),
                "target_type": l.target_type,
                "target_id": str(l.target_id),
                "field_changed": l.field_changed,
                "old_value": l.old_value,
                "new_value": l.new_value,
                "changed_at": l.changed_at.isoformat(),
            }
            for l in logs
        ]
    }
