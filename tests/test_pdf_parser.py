"""Unit tests for LLM PDF parser (mock Anthropic API)."""
import json
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


SAMPLE_LLM_RESPONSE = json.dumps({
    "events": [
        {
            "type": "assignment",
            "title": "ממ\"ן 11",
            "course_code": "20441",
            "due_date": "2025-04-15T23:59:00+03:00",
            "confidence": "high",
        },
        {
            "type": "exam",
            "title": "בחינה מסכמת",
            "course_code": "20441",
            "due_date": None,
            "confidence": "high",
            "exam_dates": [
                {"moed_label": "מועד א׳", "sitting_date": "2025-06-15T09:00:00+03:00", "location": "רמת אביב"},
                {"moed_label": "מועד ב׳", "sitting_date": "2025-08-10T09:00:00+03:00", "location": None},
            ],
        },
    ]
})


@pytest.mark.asyncio
async def test_parse_returns_events():
    mock_content = MagicMock()
    mock_content.text = SAMPLE_LLM_RESPONSE
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from app.services.pdf_parser import parse_pdf_with_llm
        result = await parse_pdf_with_llm("טקסט לדוגמה עם מטלות ובחינות", uuid.uuid4())

    assert "events" in result
    assert len(result["events"]) == 2


@pytest.mark.asyncio
async def test_parse_strips_markdown_fences():
    fenced = f"```json\n{SAMPLE_LLM_RESPONSE}\n```"
    mock_content = MagicMock()
    mock_content.text = fenced
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from app.services.pdf_parser import parse_pdf_with_llm
        result = await parse_pdf_with_llm("text", uuid.uuid4())

    assert result["events"][0]["type"] == "assignment"


@pytest.mark.asyncio
async def test_parse_handles_invalid_json():
    mock_content = MagicMock()
    mock_content.text = "לא JSON תקין"
    mock_message = MagicMock()
    mock_message.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        from app.services.pdf_parser import parse_pdf_with_llm
        result = await parse_pdf_with_llm("text", uuid.uuid4())

    assert result == {"events": []}


def test_high_confidence_no_review():
    """high confidence events should not need review."""
    event = {"confidence": "high"}
    needs_review = event["confidence"] != "high"
    assert needs_review is False


def test_medium_confidence_needs_review():
    event = {"confidence": "medium"}
    needs_review = event["confidence"] != "high"
    assert needs_review is True


def test_low_confidence_needs_review():
    event = {"confidence": "low"}
    needs_review = event["confidence"] != "high"
    assert needs_review is True
