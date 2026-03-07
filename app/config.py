from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    ANTHROPIC_API_KEY: str = ""
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = "students.juggle.app"
    S3_BUCKET: str = ""
    S3_ENDPOINT: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    GCAL_CLIENT_ID: str = ""
    GCAL_CLIENT_SECRET: str = ""
    SECRET_KEY: str = "dev-secret-change-in-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    class Config:
        env_file = ".env"

settings = Settings(_env_file=".env" if __import__("os").path.exists(".env") else None)
