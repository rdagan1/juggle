"""Google Calendar API wrapper with AES-256 token encryption."""
import base64
import json
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import get_settings

settings = get_settings()


def _get_fernet() -> Fernet:
    key = settings.gcal_encryption_key
    if not key:
        # Generate a dev key (not for production)
        key = base64.urlsafe_b64encode(b"juggle-dev-key-00000000000000000")[:44].decode()
    # Ensure key is properly padded Fernet key
    if len(key) < 44:
        key = base64.urlsafe_b64encode(key.encode().ljust(32, b"0")[:32]).decode()
    return Fernet(key.encode())


def encrypt_token(token_data: dict) -> str:
    f = _get_fernet()
    return f.encrypt(json.dumps(token_data).encode()).decode()


def decrypt_token(encrypted: str) -> dict:
    f = _get_fernet()
    return json.loads(f.decrypt(encrypted.encode()).decode())


def _build_service(token_data: dict):
    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    return build("calendar", "v3", credentials=creds)


async def get_busy_slots(user, days: int = 14) -> list[dict]:
    """Fetch busy time slots from GCal freebusy API."""
    if not user.google_calendar_token:
        return []
    try:
        token_data = decrypt_token(user.google_calendar_token)
        service = _build_service(token_data)
        now = datetime.now(timezone.utc)
        from datetime import timedelta
        end = now + timedelta(days=days)

        body = {
            "timeMin": now.isoformat(),
            "timeMax": end.isoformat(),
            "items": [{"id": "primary"}],
        }
        result = service.freebusy().query(body=body).execute()
        calendars = result.get("calendars", {})
        busy = []
        for cal_id, data in calendars.items():
            for slot in data.get("busy", []):
                busy.append({
                    "start": slot["start"],
                    "end": slot["end"],
                })
        return busy
    except Exception as e:
        return []


async def create_study_event(user, start: datetime, end: datetime, course_name: str) -> Optional[str]:
    """Create a study block event in GCal. Returns event_id."""
    if not user.google_calendar_token:
        return None
    try:
        token_data = decrypt_token(user.google_calendar_token)
        service = _build_service(token_data)
        event = {
            "summary": f"לימוד: {course_name}",
            "start": {"dateTime": start.isoformat(), "timeZone": "Asia/Jerusalem"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Jerusalem"},
            "colorId": "7",  # Teal/blue for study blocks
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return created.get("id")
    except Exception:
        return None


async def delete_event(user, event_id: str) -> bool:
    """Delete a GCal event by ID. Returns True on success."""
    if not user.google_calendar_token or not event_id:
        return False
    try:
        token_data = decrypt_token(user.google_calendar_token)
        service = _build_service(token_data)
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return True
    except Exception:
        return False


async def create_exam_event(user, sitting) -> Optional[str]:
    """Create or update a GCal event for an exam sitting."""
    if not user.google_calendar_token:
        return None
    try:
        from datetime import timedelta
        token_data = decrypt_token(user.google_calendar_token)
        service = _build_service(token_data)

        is_confirmed = sitting.status.value == "confirmed"
        title = f"בחינה מועד {sitting.moed_label}"
        if not is_confirmed:
            title = f"[אופציונלי] {title}"

        end = sitting.sitting_date + timedelta(hours=3)
        event = {
            "summary": title,
            "location": sitting.location or "",
            "start": {"dateTime": sitting.sitting_date.isoformat(), "timeZone": "Asia/Jerusalem"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Asia/Jerusalem"},
            "status": "confirmed" if is_confirmed else "tentative",
        }

        if sitting.gcal_event_id:
            updated = service.events().update(
                calendarId="primary", eventId=sitting.gcal_event_id, body=event
            ).execute()
            return updated.get("id")
        else:
            created = service.events().insert(calendarId="primary", body=event).execute()
            return created.get("id")
    except Exception:
        return None
