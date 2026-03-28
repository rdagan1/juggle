"""PDF storage: Cloudflare R2/S3 with local-folder fallback.

Upload/download are offered in both sync (for Celery workers) and async
(for FastAPI request handlers) flavours.  The backend is selected once at
import time based on whether R2 credentials are present in settings.
"""
import asyncio
from functools import partial
from pathlib import Path
from typing import Final

from app.config import get_settings
from app.infra.log import tagged_logger

logger = tagged_logger("STORAGE")

_PDF_CONTENT_TYPE: Final[str] = "application/pdf"


def _use_s3() -> bool:
    s = get_settings()
    return bool(s.r2_access_key and s.r2_secret_key and s.r2_endpoint)


def _s3_client():
    import boto3
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.r2_endpoint,
        aws_access_key_id=s.r2_access_key,
        aws_secret_access_key=s.r2_secret_key,
        region_name="auto",
    )


# ── Sync API (Celery workers) ─────────────────────────────────────────────────

def upload(key: str, data: bytes) -> None:
    """Store *data* under *key*.  Key is the canonical storage path."""
    if _use_s3():
        s = get_settings()
        _s3_client().put_object(
            Bucket=s.r2_bucket,
            Key=key,
            Body=data,
            ContentType=_PDF_CONTENT_TYPE,
        )
        logger.info("R2/S3 upload key=%s size=%d", key, len(data))
    else:
        path = Path(get_settings().local_storage_path) / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.info("Local upload key=%s size=%d", key, len(data))


def download(key: str) -> bytes:
    """Fetch bytes stored under *key*."""
    if _use_s3():
        s = get_settings()
        response = _s3_client().get_object(Bucket=s.r2_bucket, Key=key)
        return response["Body"].read()
    else:
        return (Path(get_settings().local_storage_path) / key).read_bytes()


def delete(key: str) -> None:
    """Remove *key* from storage — errors are logged, never raised."""
    try:
        if _use_s3():
            s = get_settings()
            _s3_client().delete_object(Bucket=s.r2_bucket, Key=key)
        else:
            (Path(get_settings().local_storage_path) / key).unlink(missing_ok=True)
        logger.info("Deleted storage key=%s", key)
    except Exception:
        logger.exception("Failed to delete storage key=%s", key)


# ── Async API (FastAPI request handlers) ─────────────────────────────────────

async def upload_async(key: str, data: bytes) -> None:
    """Async wrapper around :func:`upload` — runs in the default thread pool."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(upload, key, data))


async def download_async(key: str) -> bytes:
    """Async wrapper around :func:`download`."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(download, key))


async def delete_async(key: str) -> None:
    """Async wrapper around :func:`delete`."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(delete, key))
