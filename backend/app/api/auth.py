"""Authentication: email/password + Google OAuth."""
import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.api_models import Token, RegisterRequest, VerifyRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_jwt(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_tokens(user_id: str) -> Token:
    access = create_jwt({"sub": user_id, "type": "access"}, timedelta(minutes=settings.access_token_expire_minutes))
    refresh = create_jwt({"sub": user_id, "type": "refresh"}, timedelta(days=settings.refresh_token_expire_days))
    return Token(access_token=access, refresh_token=refresh)


def generate_virtual_email(name: str) -> str:
    clean = name.lower().replace(" ", ".")
    suffix = "".join(random.choices(string.digits, k=6))
    return f"{clean}.{suffix}@{settings.virtual_email_domain}"


async def get_or_create_user_by_google(email: str, name: str, google_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        if not user.google_id:
            user.google_id = google_id
        return user
    user = User(
        email=email,
        name=name,
        google_id=google_id,
        email_verified=True,
        virtual_email=generate_virtual_email(name),
        preferences={
            "forward_emails": True,
            "assignment_first_reminder_days": 7,
            "exam_first_reminder_days": 14,
            "shabbat_blackout": True,
            "grade_alert_threshold": 70.0,
            "min_study_session_minutes": 30,
        },
    )
    db.add(user)
    await db.flush()
    return user


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

@router.get("/demo", response_model=Token)
async def demo_login(db: AsyncSession = Depends(get_db)):
    """Return tokens for a shared demo user. Only available when DEMO_MODE=true."""
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Demo mode is not enabled")

    demo_email = "demo@juggle.app"
    result = await db.execute(select(User).where(User.email == demo_email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=demo_email,
            name="Demo User",
            email_verified=True,
            virtual_email=generate_virtual_email("demo"),
            preferences={
                "forward_emails": True,
                "assignment_first_reminder_days": 7,
                "exam_first_reminder_days": 14,
                "shabbat_blackout": True,
                "grade_alert_threshold": 70.0,
                "min_study_session_minutes": 30,
            },
        )
        db.add(user)
        await db.flush()
    return create_tokens(str(user.id))


# ---------------------------------------------------------------------------
# Email/password registration
# ---------------------------------------------------------------------------

@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    existing = result.scalar_one_or_none()
    if existing and existing.email_verified:
        raise HTTPException(status_code=409, detail="Email already registered")

    code = "".join(random.choices(string.digits, k=6))
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)

    if existing:
        existing.name = body.name
        existing.verification_code = code
        existing.verification_code_expires = expires
        user = existing
    else:
        user = User(
            email=body.email,
            name=body.name,
            verification_code=code,
            verification_code_expires=expires,
            virtual_email=generate_virtual_email(body.name),
            preferences={
                "forward_emails": True,
                "assignment_first_reminder_days": 7,
                "exam_first_reminder_days": 14,
                "shabbat_blackout": True,
                "grade_alert_threshold": 70.0,
                "min_study_session_minutes": 30,
            },
        )
        db.add(user)

    # TODO: send verification email via Mailgun/SMTP
    # For now, return code in dev mode
    return {"message": "Verification code sent", "dev_code": code}


@router.post("/verify", response_model=Token)
async def verify(body: VerifyRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or user.verification_code != body.code:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    if user.verification_code_expires and user.verification_code_expires < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Code expired")

    user.hashed_password = pwd_context.hash(body.password)
    user.email_verified = True
    user.verification_code = None
    user.verification_code_expires = None

    return create_tokens(str(user.id))


@router.post("/login", response_model=Token)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not pwd_context.verify(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")
    return create_tokens(str(user.id))


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

@router.get("/config")
async def auth_config():
    """Returns which auth providers are configured."""
    google_configured = bool(
        settings.google_client_id
        and not settings.google_client_id.startswith("...")
        and "googleusercontent" in settings.google_client_id
    )
    return {"google_enabled": google_configured}


@router.get("/google")
async def google_oauth():
    if not settings.google_client_id or settings.google_client_id.startswith("..."):
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
        )
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    from urllib.parse import urlencode
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/google/callback", response_model=Token)
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    import httpx
    token_resp = await _exchange_google_code(code, settings.google_redirect_uri)
    id_token_str = token_resp.get("id_token")
    if not id_token_str:
        raise HTTPException(status_code=400, detail="No id_token in Google response")

    try:
        idinfo = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {e}")

    user = await get_or_create_user_by_google(
        email=idinfo["email"],
        name=idinfo.get("name", idinfo["email"].split("@")[0]),
        google_id=idinfo["sub"],
        db=db,
    )
    return create_tokens(str(user.id))


async def _exchange_google_code(code: str, redirect_uri: str) -> dict:
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Google Calendar OAuth
# ---------------------------------------------------------------------------

@router.get("/google-calendar")
async def gcal_oauth():
    from urllib.parse import urlencode
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.gcal_redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/google-calendar/callback")
async def gcal_callback(code: str, user_id: str, calendar_type: str = "personal", db: AsyncSession = Depends(get_db)):
    from app.services.gcal_client import encrypt_token
    token_resp = await _exchange_google_code(code, settings.gcal_redirect_uri)
    encrypted = encrypt_token(token_resp)

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if calendar_type == "work":
        user.work_calendar_token = encrypted
    else:
        user.google_calendar_token = encrypted

    return {"message": "Calendar connected successfully"}
