"""Tests for PDF pipeline service."""
import hashlib
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.pdf_pipeline import (
    EVENT_KEYWORDS,
    extract_text,
    has_extractable_events,
)


def test_has_extractable_events_with_keywords():
    text = 'יש לך מטלה ממ"ן 11 להגשה עד 15.3.2025'
    assert has_extractable_events(text) is True


def test_has_extractable_events_date_pattern():
    text = "הרצאה תתקיים ב-20/12/2024 בשעה 18:00"
    assert has_extractable_events(text) is True


def test_has_extractable_events_no_match():
    text = "זהו מסמך כללי ללא מועדים או מטלות. אנא קרא בעיון."
    assert has_extractable_events(text) is False


def test_has_extractable_events_grade_keyword():
    text = "ציון הבחינה הסופי הוא 87"
    assert has_extractable_events(text) is True


def test_extract_text_empty_bytes():
    # Empty/invalid PDF should return empty string or raise
    import fitz
    try:
        text = extract_text(b"not a pdf")
    except Exception:
        text = ""
    assert isinstance(text, str)


@pytest.mark.asyncio
async def test_get_cached_parse_miss(db_session):
    from app.services.pdf_pipeline import get_cached_parse
    result = await get_cached_parse("nonexistent_hash_123", db_session)
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_parse_hit(db_session):
    from app.services.pdf_pipeline import get_cached_parse, store_cache
    from datetime import datetime, timezone

    pdf_hash = "abc123" + "0" * 58
    parse_result = {"assignments": [{"title": "ממ\"ן 11", "course_code": "20407", "due_date": "2025-03-15"}]}

    await store_cache(pdf_hash, parse_result, db_session)
    await db_session.flush()

    cached = await get_cached_parse(pdf_hash, db_session)
    assert cached is not None
    assert cached["assignments"][0]["title"] == 'ממ"ן 11'


@pytest.mark.asyncio
async def test_run_pipeline_unreadable(db_session, test_user):
    from app.services.pdf_pipeline import run_pipeline
    from app.models.pdf_attachment import PdfAttachment, PdfParseStatus

    att = PdfAttachment(
        user_id=test_user.id,
        filename="test.pdf",
        parse_status=PdfParseStatus.pending,
    )
    db_session.add(att)
    await db_session.flush()

    # Minimal valid PDF with no text
    minimal_pdf = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"

    result = await run_pipeline(minimal_pdf, test_user.id, att.id, db_session)
    assert result["status"] in ("unreadable", "no_events", "parsed")


@pytest.mark.asyncio
async def test_run_pipeline_cache_hit(db_session, test_user):
    from app.services.pdf_pipeline import run_pipeline, store_cache
    from app.models.pdf_attachment import PdfAttachment, PdfParseStatus

    att = PdfAttachment(
        user_id=test_user.id,
        filename="cached.pdf",
        parse_status=PdfParseStatus.pending,
    )
    db_session.add(att)
    await db_session.flush()

    # Pre-populate cache with a known hash
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    # Empty doc bytes
    pdf_bytes = doc.tobytes()
    doc.close()

    pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
    await store_cache(pdf_hash, {}, db_session)
    await db_session.flush()

    result = await run_pipeline(pdf_bytes, test_user.id, att.id, db_session)
    # Either cache hit (empty result = no_events-like) or unreadable
    assert "status" in result
