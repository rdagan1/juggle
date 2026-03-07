from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/juggle"
    REDIS_URL: str = "redis://localhost:6379/0"
    S3_BUCKET: str = "juggle-pdfs"
    S3_ENDPOINT: str = "https://s3.amazonaws.com"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = "students.juggle.app"

    class Config:
        env_file = ".env"


settings = Settings()
