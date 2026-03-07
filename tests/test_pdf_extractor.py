"""Unit tests for PDF extraction service."""
import io
import pytest
from app.services.pdf_extractor import (
    extract_pdf_text,
    has_extractable_events,
    compute_pdf_hash,
    _contains_hebrew,
)


def _make_minimal_pdf(text: str) -> bytes:
    """Create a minimal valid PDF with given text using reportlab if available,
    otherwise return a pre-built fixture bytes."""
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        buf = io.BytesIO()
        c = rl_canvas.Canvas(buf)
        # reportlab doesn't support Hebrew bidi by default, so embed raw text
        c.drawString(100, 750, text)
        c.save()
        return buf.getvalue()
    except ImportError:
        pass

    # Minimal PDF with embedded text (ASCII only for fixture)
    content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Parent 2 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length {len(text) + 50}>>
stream
BT /F1 12 Tf 100 700 Td ({text}) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000400 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
472
%%EOF"""
    return content.encode("latin-1")


# ── extract_pdf_text tests ────────────────────────────────────────────────────

def test_extract_returns_unreadable_for_empty_bytes():
    result = extract_pdf_text(b"not a pdf")
    assert result["readable"] is False
    assert result["text"] is None


def test_extract_result_keys():
    result = extract_pdf_text(b"not a pdf")
    assert set(result.keys()) == {"readable", "text", "page_count", "raw_text_length"}


def test_readability_requires_hebrew():
    # Text without Hebrew should be unreadable even if long
    long_ascii = "a" * 200
    assert not _contains_hebrew(long_ascii)


def test_readability_hebrew_detected():
    hebrew_text = "מ" * 50 + " some text " * 5
    assert _contains_hebrew(hebrew_text)


# ── has_extractable_events tests ─────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ('ממ"ן 11 בקורס מבוא למדעי המחשב', True),
    ("בחינה מסכמת בתאריך 15/06/2025", True),
    ("10 במרץ 2025 יש הגשה", True),
    ("ציון סופי יפורסם לאחר הבחינה", True),
    ("מועד א׳ בחינה", True),
    ("תאריך הגשה: 20/04/2025", True),
    ("This is a random English text with no events", False),
    ("", False),
])
def test_has_extractable_events(text, expected):
    assert has_extractable_events(text) == expected


# ── compute_pdf_hash tests ────────────────────────────────────────────────────

def test_hash_is_64_chars():
    h = compute_pdf_hash(b"some pdf bytes")
    assert len(h) == 64


def test_same_bytes_same_hash():
    data = b"identical content"
    assert compute_pdf_hash(data) == compute_pdf_hash(data)


def test_different_bytes_different_hash():
    assert compute_pdf_hash(b"aaa") != compute_pdf_hash(b"bbb")
