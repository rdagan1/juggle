import json
import re

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.infra.log import tagged_logger
from app.services.gio.constants import HAIKU_MODEL

settings = get_settings()
anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
logger = tagged_logger("GIO_ENGINE")


async def _parse_event_text(text: str, today: str) -> dict:
    """Use LLM to extract structured event data from free-form Hebrew text."""
    prompt = (
        f"You are a scheduling assistant for Hebrew university students.\n"
        f"Parse the following Hebrew text and extract event information.\n\n"
        f"Return ONLY valid JSON (no other text):\n"
        f'{{"action": "create or update or delete", "title": "event title in Hebrew", '
        f'"due_date": "YYYY-MM-DD or null", '
        f'"type": "exam or assignment or lecture or announcement", '
        f'"course_name": "course name in Hebrew or null", '
        f'"moed": "א or ב or ג or null"}}\n\n'
        f'Use action "create" for new events, "update" for rescheduled/moved events, '
        f'"delete" for cancelled or removed events.\n'
        f'Set moed only for exam events; extract from text (e.g. "מועד א" → "א").\n'
        f"Always include title and course_name even for delete actions.\n"
        f"The title should NOT include the course name — keep it short (e.g. 'בחינה', 'מטלה 3').\n"
        f"Today's date: {today}\n\n"
        f"Text: {text}"
    )
    try:
        response = await anthropic_client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        logger.exception("Failed to parse event text")
    return {}


async def _parse_grade_text(text: str) -> dict:
    """Use LLM to extract structured grade data from free-form Hebrew text."""
    prompt = (
        "You are a grade extractor for Hebrew university students.\n"
        "Parse the following Hebrew text and extract grade information.\n\n"
        "Return ONLY valid JSON (no other text):\n"
        '{"grade": number_or_null, "max_grade": number_or_null, '
        '"course_name": "course name in Hebrew or null", '
        '"assignment_title": "title of the graded item or null", '
        '"moed": "א or ב or ג or null", '
        '"grade_type": "exam or assignment"}\n\n'
        "grade: the numeric score received (e.g. 85, 92.5). MUST be a number, not null.\n"
        "max_grade: the maximum possible score if mentioned; default to null (system uses 100).\n"
        "grade_type: 'exam' for exams/tests/בחינה, 'assignment' for homework/ממ\"ן/מטלה.\n"
        f"Text: {text}"
    )
    try:
        response = await anthropic_client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        logger.exception("Failed to parse grade text")
    return {}


async def _extract_course_name(text: str) -> str | None:
    """Use LLM to extract just the course name from a short Hebrew reply."""
    prompt = (
        "You are a university course name extractor.\n"
        "The student was asked for a course name and replied in Hebrew.\n"
        "Extract the course name from their reply and return ONLY the course name — nothing else.\n"
        "If you cannot identify a course name, return the single word: null\n\n"
        f"Reply: {text}"
    )
    try:
        response = await anthropic_client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=64,
            messages=[{"role": "user", "content": prompt}],
        )
        result = response.content[0].text.strip()
        return None if result.lower() == "null" else result
    except Exception:
        logger.exception("Failed to extract course name")
        return None
