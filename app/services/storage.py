"""S3 storage service stub (full impl in TASK-005)."""
import uuid
import boto3
from app.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def upload_pdf(file_bytes: bytes, filename: str, user_id: uuid.UUID) -> str:
    key = f"{user_id}/{uuid.uuid4()}/{filename}"
    _client().put_object(Bucket=settings.S3_BUCKET, Key=key, Body=file_bytes)
    return f"s3://{settings.S3_BUCKET}/{key}"
