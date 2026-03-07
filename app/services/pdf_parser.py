"""LLM-based event extraction from PDF text using Claude Haiku."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import anthropic

MODEL = "claude-3-5-haiku-20241022"

SYSTEM_PROMPT = """אתה מומחה לניתוח מסמכי אוניברסיטה פתוחה בישראל.
תפקידך לחלץ אירועים אקדמיים מובנים מטקסט PDF.

חלץ את כל האירועים הבאים:
- ממ"נים (מטלות): סוג "assignment"
- בחינות: סוג "exam" (כולל כל המועדים)
- הרצאות: סוג "lecture"
- ציונים שהתפרסמו: סוג "grade"

החזר JSON בלבד (ללא טקסט נוסף) בפורמט:
{
  "events": [
    {
      "type": "assignment" | "exam" | "lecture" | "grade",
      "title": "שם המטלה/בחינה",
      "course_code": "קוד הקורס או null",
      "due_date": "ISO 8601 datetime or null",
      "confidence": "high" | "medium" | "low",
      "exam_dates": [   // רק לסוג exam
        {
          "moed_label": "מועד א׳",
          "sitting_date": "ISO 8601 datetime",
          "location": "מיקום או null"
        }
      ]
    }
  ]
}

כללים:
- confidence=high: תאריך מפורש וברור
- confidence=medium: תאריך משוער או חלקי
- confidence=low: אין תאריך או מידע מינימלי
- תאריכים: המר לפורמט ISO 8601 עם שעה 23:59:00+02:00 אם אין שעה
- אם אין אירועים, החזר {"events": []}"""


async def parse_pdf_with_llm(text: str, user_id: uuid.UUID, db=None) -> dict:
    """Extract structured events from Hebrew OUI PDF text using Claude Haiku.

    Args:
        text: Extracted PDF text.
        user_id: The user who owns this document.
        db: AsyncSession — if provided, events are written to DB and result cached.

    Returns:
        {"events": [...]} dict from LLM.
    """
    client = anthropic.AsyncAnthropic()

    message = await client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"נתח את הטקסט הבא וחלץ אירועים אקדמיים:\n\n{text[:12000]}"}],
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"events": []}

    if db:
        await _persist_events(result, user_id, db)

    return result


async def _persist_events(parse_result: dict, user_id: uuid.UUID, db) -> None:
    """Insert parsed events into deadlines and exam_sittings tables."""
    from sqlalchemy import text as sa_text

    for event in parse_result.get("events", []):
        event_type = event.get("type")
        if event_type not in ("assignment", "exam", "lecture"):
            continue

        confidence = event.get("confidence", "low")
        needs_review = confidence != "high"
        due_date = event.get("due_date")

        row = await db.execute(
            sa_text("""
                INSERT INTO deadlines (user_id, title, type, due_date, status, needs_review)
                VALUES (:user_id, :title, :type, :due_date::timestamptz, 'pending', :needs_review)
                RETURNING id
            """),
            {
                "user_id": str(user_id),
                "title": event.get("title", ""),
                "type": event_type,
                "due_date": due_date,
                "needs_review": needs_review,
            },
        )
        deadline_id = row.fetchone()[0]

        if event_type == "exam":
            for sitting in event.get("exam_dates", []):
                await db.execute(
                    sa_text("""
                        INSERT INTO exam_sittings (deadline_id, moed_label, sitting_date, location)
                        VALUES (:deadline_id, :moed_label, :sitting_date::timestamptz, :location)
                    """),
                    {
                        "deadline_id": str(deadline_id),
                        "moed_label": sitting.get("moed_label"),
                        "sitting_date": sitting.get("sitting_date"),
                        "location": sitting.get("location"),
                    },
                )

    await db.commit()


async def store_parse_cache(pdf_hash: str, parse_result: dict, db) -> None:
    """Store parse result in pdf_parse_cache."""
    from sqlalchemy import text as sa_text

    await db.execute(
        sa_text("""
            INSERT INTO pdf_parse_cache (pdf_hash, parse_result)
            VALUES (:pdf_hash, :parse_result::jsonb)
            ON CONFLICT (pdf_hash) DO NOTHING
        """),
        {"pdf_hash": pdf_hash, "parse_result": json.dumps(parse_result)},
    )
    await db.commit()
