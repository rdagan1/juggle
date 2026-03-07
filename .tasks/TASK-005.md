# TASK-005: S3 Storage Service

**Phase:** Phase 1
**Complexity:** Small

## Description

Thin wrapper around boto3 for PDF storage.

## Methods
- `upload_pdf(file_bytes: bytes, filename: str, user_id: UUID) -> str` — returns `storage_url`
- `get_pdf_url(storage_url: str, expires_in_seconds: int = 3600) -> str` — returns presigned URL
- `delete_pdf(storage_url: str) -> None`

## Config
Reads from env vars: `S3_BUCKET`, `S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.

## Deliverable
`app/services/storage.py` with the three methods + unit tests using moto.

## Dependencies

None

---

*Generated from PRD v2.7 task breakdown.*
