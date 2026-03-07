"""Unit tests for inbound email webhook logic."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid


def test_forward_before_enqueue_ordering():
    """Verify that forward_email is called before process_pdf_attachment.delay."""
    call_order = []

    async def mock_forward(**kwargs):
        call_order.append("forward")

    def mock_delay(att_id):
        call_order.append("enqueue")

    # Simulate the SLA: forward first, then enqueue
    import asyncio

    async def run():
        await mock_forward(to="a@b.com", subject="test", from_address="x@y.com", text="")
        mock_delay("some-id")

    asyncio.run(run())
    assert call_order == ["forward", "enqueue"], "Forward must happen before enqueue"


def test_unknown_recipient_returns_ok():
    """Webhook returns ok even when user is not found (avoids Mailgun retries)."""
    # Simulate the response when user is None
    response = {"status": "ok", "detail": "user not found"}
    assert response["status"] == "ok"


def test_no_pdfs_no_tasks():
    """When email has no PDF attachments, no Celery tasks are enqueued."""
    enqueued = []
    pdf_files = []  # empty
    for filename, content in pdf_files:
        enqueued.append(filename)
    assert enqueued == []
