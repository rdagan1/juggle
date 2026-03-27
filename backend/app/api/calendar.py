"""Google Calendar endpoint helpers."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

# GCal OAuth is handled in auth.py (/auth/google-calendar)
# This router provides calendar-specific utility endpoints.

@router.get("/status")
async def calendar_status():
    """Placeholder — calendar status is exposed via /api/settings."""
    return {"message": "See /api/settings for calendar status"}
