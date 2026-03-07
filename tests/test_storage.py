import pytest
import boto3
from moto import mock_aws
from unittest.mock import patch
from app.services.storage import upload_pdf, get_pdf_url, delete_pdf

BUCKET = "test-juggle-pdfs"
USER_ID = "00000000-0000-0000-0000-000000000001"

@pytest.fixture
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture
def s3_bucket(aws_credentials):
    with mock_aws():
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=BUCKET)
        yield conn

def test_upload_pdf(s3_bucket, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.S3_BUCKET", BUCKET)
    monkeypatch.setattr("app.services.storage.settings.S3_ENDPOINT", "")

    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=BUCKET)
        url = upload_pdf(b"%PDF-1.4 test content", "test.pdf", USER_ID)
        assert url.startswith(f"s3://{BUCKET}/pdfs/{USER_ID}/")
        assert url.endswith("test.pdf")

def test_get_pdf_url(s3_bucket, monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.S3_BUCKET", BUCKET)
    monkeypatch.setattr("app.services.storage.settings.S3_ENDPOINT", "")

    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=BUCKET)
        storage_url = upload_pdf(b"%PDF-1.4 content", "doc.pdf", USER_ID)
        presigned = get_pdf_url(storage_url)
        assert "doc.pdf" in presigned or "X-Amz-Signature" in presigned

def test_delete_pdf(monkeypatch):
    monkeypatch.setattr("app.services.storage.settings.S3_BUCKET", BUCKET)
    monkeypatch.setattr("app.services.storage.settings.S3_ENDPOINT", "")

    with mock_aws():
        boto3.client("s3", region_name="us-east-1").create_bucket(Bucket=BUCKET)
        storage_url = upload_pdf(b"%PDF content", "delete_me.pdf", USER_ID)
        delete_pdf(storage_url)  # Should not raise
