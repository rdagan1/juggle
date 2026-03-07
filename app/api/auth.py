import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth import (
    check_verification_code,
    create_access_token,
    generate_verification_code,
    generate_virtual_email,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Email/Password flow ───────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    virtual = generate_virtual_email(None)
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        virtual_email=virtual,
    )
    db.add(user)
    await db.commit()

    code = generate_verification_code(body.email)
    # In production: send via Mailgun. Here we return it for testability.
    return {"message": "Verification code sent", "debug_code": code}


@router.post("/verify", response_model=TokenResponse)
async def verify(body: VerifyRequest, db: AsyncSession = Depends(get_db)):
    if not check_verification_code(body.email, body.code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code")

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    return TokenResponse(access_token=create_access_token(user.id))


# ── Google OAuth flow ─────────────────────────────────────────────────────────

@router.get("/google")
async def google_oauth_redirect():
    from urllib.parse import urlencode
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    })
    return {"redirect_url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}"}


@router.get("/google/callback", response_model=TokenResponse)
async def google_oauth_callback(code: str, db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange Google code")

    id_token_data = token_resp.json()
    # Decode Google's ID token (skip signature verification for brevity; use google-auth in prod)
    import base64, json as _json
    payload_b64 = id_token_data["id_token"].split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    profile = _json.loads(base64.urlsafe_b64decode(payload_b64))

    google_id = profile["sub"]
    email = profile["email"]
    name = profile.get("name")

    # Upsert user
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()
    if not user:
        result2 = await db.execute(select(User).where(User.email == email))
        user = result2.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            name=name,
            google_id=google_id,
            email_verified=True,
            virtual_email=generate_virtual_email(name),
        )
        db.add(user)
    else:
        user.google_id = google_id
        user.name = user.name or name
        user.email_verified = True

    await db.commit()
    return TokenResponse(access_token=create_access_token(user.id))
