import random
import string
import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory verification code store (use Redis in production)
_verification_codes: dict[str, str] = {}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def generate_verification_code(email: str) -> str:
    code = "".join(random.choices(string.digits, k=6))
    _verification_codes[email] = code
    return code


def check_verification_code(email: str, code: str) -> bool:
    stored = _verification_codes.get(email)
    if stored and stored == code:
        del _verification_codes[email]
        return True
    return False


def generate_virtual_email(name: str | None) -> str:
    """Generate {firstname}.{lastname}.{4-char-random}@students.juggle.app"""
    parts = (name or "user").strip().split()
    firstname = parts[0].lower() if parts else "user"
    lastname = parts[1].lower() if len(parts) > 1 else "student"
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{firstname}.{lastname}.{suffix}@students.juggle.app"
