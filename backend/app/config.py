from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://juggle:juggle@localhost:5432/juggle"
    redis_url: str = "redis://localhost:6379/0"

    anthropic_api_key: str = ""

    mailgun_api_key: str = ""
    mailgun_domain: str = "students.juggle.app"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    gcal_redirect_uri: str = "http://localhost:8000/auth/google-calendar/callback"

    r2_bucket: str = "juggle-pdfs"
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_endpoint: str = ""
    local_storage_path: str = "./uploads"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30

    gcal_encryption_key: str = ""  # Base64-encoded 32-byte key

    virtual_email_domain: str = "students.juggle.app"

    frontend_url: str = "http://localhost:5173"

    demo_mode: bool = False

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
