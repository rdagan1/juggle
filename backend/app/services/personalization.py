"""Render personalized Gio messages from templates."""
import json
import uuid
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import ConversationHistory, ConversationRole, InputMethod

TEMPLATES_PATH: Final[Path] = Path(__file__).parent.parent / "templates" / "gio_templates.yaml"
IL_TZ: Final = pytz.timezone("Asia/Jerusalem")


def load_templates() -> dict:
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


_templates_cache: dict | None = None


def get_templates() -> dict:
    global _templates_cache
    if _templates_cache is None:
        _templates_cache = load_templates()
    return _templates_cache


def get_opening(time_of_day: str, day_of_week: str) -> str:
    openings = {
        "morning": "בוקר טוב",
        "afternoon": "אחר הצהריים טובים",
        "evening": "ערב טוב",
        "night": "לילה טוב",
    }
    return openings.get(time_of_day, "שלום")


def classify_time_of_day(now: datetime) -> str:
    h = now.hour
    if 5 <= h < 12:
        return "morning"
    elif 12 <= h < 17:
        return "afternoon"
    elif 17 <= h < 21:
        return "evening"
    else:
        return "night"


def classify_urgency(days_until: int) -> str:
    if days_until >= 14:
        return "low"
    elif days_until >= 7:
        return "medium"
    elif days_until >= 3:
        return "high"
    elif days_until >= 1:
        return "urgent"
    else:
        return "day_of"


def get_due_day_phrase(days_until: int) -> str:
    if days_until == 0:
        return "היום"
    elif days_until == 1:
        return "מחר"
    elif days_until == 2:
        return "מחרתיים"
    elif days_until <= 7:
        return f"בעוד {days_until} ימים"
    else:
        return f"בעוד {days_until} ימים"


def get_workload_line(other_due_soon_count: int) -> str:
    if other_due_soon_count == 0:
        return ""
    elif other_due_soon_count == 1:
        return "יש לך עוד מטלה אחת קרובה."
    else:
        return f"יש לך עוד {other_due_soon_count} מטלות קרובות."


def get_behavioral_callback(ctx: dict) -> str:
    last_start = ctx.get("last_start_days_before")
    if last_start and last_start <= 2:
        return "לפי הרגלי הלמידה שלך, בדרך כלל מתחיל/ה בסמוך להגשה."
    return ""


def render_gio_message(template_id: str, ctx: dict) -> dict:
    """Returns dict with text, buttons, navigate_hint."""
    templates = get_templates()
    template = templates.get(template_id)
    if not template:
        return {
            "text": ctx.get("fallback_text", "יש לי עדכון בשבילך."),
            "buttons": [],
            "navigate_hint": None,
        }

    now_il = datetime.now(IL_TZ)
    time_of_day = classify_time_of_day(now_il)
    day_of_week = now_il.strftime("%A")

    days_until = ctx.get("days_until", 99)
    urgency = classify_urgency(days_until)

    variants = template.get("variants", {})
    text_template = variants.get(urgency) or variants.get("default") or template.get("text", "")

    include_name = ctx.get("include_name", False)
    name = ctx.get("name", "") if include_name else ""

    text = text_template.format(
        name=name,
        opening=get_opening(time_of_day, day_of_week),
        course_name=ctx.get("course_name", ""),
        assignment_title=ctx.get("assignment_title", ""),
        due_day_phrase=get_due_day_phrase(days_until),
        estimated_hours=ctx.get("estimated_hours", ""),
        estimate_sample=ctx.get("estimate_sample", ""),
        workload_line=get_workload_line(ctx.get("other_due_soon_count", 0)),
        behavioral_callback=get_behavioral_callback(ctx),
        **{k: v for k, v in ctx.items() if isinstance(v, str)},
    ).strip()

    buttons_config = template.get("buttons", {})
    buttons_for_urgency = buttons_config.get(urgency) or buttons_config.get("default") or []
    buttons = [{"label": b["label"], "value": b["value"]} for b in buttons_for_urgency]

    return {
        "text": text,
        "buttons": buttons,
        "navigate_hint": template.get("navigate_hint"),
        "template_id": template_id,
    }


async def create_gio_message(
    user_id: uuid.UUID,
    template_id: str,
    ctx: dict,
    db: AsyncSession,
) -> ConversationHistory:
    """Render and persist a Gio assistant message."""
    rendered = render_gio_message(template_id, ctx)

    msg = ConversationHistory(
        user_id=user_id,
        role=ConversationRole.assistant,
        content=rendered["text"],
        input_method=InputMethod.unknown,
        template_id=template_id,
        buttons=json.dumps(rendered["buttons"]) if rendered["buttons"] else None,
        navigate_hint=rendered.get("navigate_hint"),
    )
    db.add(msg)
    await db.flush()
    return msg
