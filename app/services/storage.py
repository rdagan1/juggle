import boto3
import uuid
from botocore.config import Config
from app.config import settings

def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT or None,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )

def upload_pdf(file_bytes: bytes, filename: str, user_id: str) -> str:
    """Upload PDF to S3 and return the storage URL (s3://bucket/key)."""
    client = _get_client()
    key = f"pdfs/{user_id}/{uuid.uuid4()}/{filename}"
    client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=key,
        Body=file_bytes,
        ContentType="application/pdf",
    )
    return f"s3://{settings.S3_BUCKET}/{key}"

def get_pdf_url(storage_url: str, expires_in_seconds: int = 3600) -> str:
    """Generate a presigned URL for a stored PDF."""
    client = _get_client()
    # Parse s3://bucket/key format
    without_prefix = storage_url[len("s3://"):]
    bucket, key = without_prefix.split("/", 1)
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in_seconds,
    )
    return url

def delete_pdf(storage_url: str) -> None:
    """Delete a PDF from S3."""
    client = _get_client()
    without_prefix = storage_url[len("s3://"):]
    bucket, key = without_prefix.split("/", 1)
    client.delete_object(Bucket=bucket, Key=key)
