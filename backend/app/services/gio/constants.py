import re
from datetime import timedelta
from typing import Final

HAIKU_MODEL: Final[str] = "claude-haiku-4-5-20251001"

# Snooze durations
SNOOZE_CONFIGS: Final[dict[str, timedelta]] = {
    "snooze_tomorrow": timedelta(days=1),
    "snooze_2d": timedelta(days=2),
    "snooze_1w": timedelta(days=7),
    "snooze_never": timedelta(days=365),
}

# Effort bucket midpoints (hours)
EFFORT_BUCKETS: Final[dict[str, float]] = {
    "effort_bucket_1": 0.5,   # 0-1h → 0.5
    "effort_bucket_2": 1.5,   # 1-2h → 1.5
    "effort_bucket_3": 3.0,   # 2-4h → 3.0
    "effort_bucket_4": 6.0,   # 4-8h → 6.0
    "effort_bucket_5": 12.0,  # 8h+  → 12.0
}

# Action verbs that clearly signal a schedule change (required for update_detected)
EVENT_ACTION_KEYWORDS: Final[tuple[str, ...]] = (
    "נדחה", "הוקדם", "שונה", "התבטל", "בוטל", "זזה", "הועבר", "הוסר",
    "נדחית", "הוקדמה", "שונתה", "התבטלה",
)

# Event nouns (required alongside an action verb for update_detected)
EVENT_NOUN_KEYWORDS: Final[tuple[str, ...]] = (
    "בחינה", "מבחן", "הגשה", "מטלה", 'ממ"ן', 'ממ"מ', "תרגיל", "שיעור", "הרצאה",
)

# Kept for backwards compatibility in imports — not used for routing logic
EVENT_KEYWORDS: Final[tuple[str, ...]] = EVENT_ACTION_KEYWORDS + EVENT_NOUN_KEYWORDS

# Explicit moed pattern ("מועד א/ב/ג") is a strong scheduling signal
EXAM_KEYWORDS: Final[tuple[str, ...]] = ("מועד א", "מועד ב", "מועד ג")

# Exam nouns without moed — only trigger scheduling when paired with a date
EXAM_NOUN_KEYWORDS: Final[tuple[str, ...]] = ("בחינה", "מבחן")

# Matches date-like patterns: "5/3", "5.3.2025", "ב-15", "ב15 לחודש" etc.
_DATE_RE: Final = re.compile(
    r'\b\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?\b'
    r'|ב-?\d{1,2}\b'
    r'|\bב\s*\d{1,2}\s*ל',
    re.UNICODE,
)

GRADE_KEYWORDS: Final[tuple[str, ...]] = (
    "קיבלתי", "קיבלת", "קיבל", "ציון", "ציוני", "נקודות",
    "עברתי", "כשלתי", "לא עברתי", "נפלתי", "עמדתי",
)

_GRADE_SCORE_RE: Final = re.compile(r'\b(1?\d{1,2}(?:\.\d+)?)\b')

KNOWN_BUTTON_VALUES = set([
    "completed", "pending", "confirm_plan", "confirm_schedule", "reschedule",
    "dismiss", "ack", "grade_ack", "grade_improve", "confirm_exam", "cancel_exam",
    "confirm_grade", "cancel_grade",
    "confirm_gcal", "dismiss_gcal",
    "needs_time", "confirm_parse", "reject_parse", "confirm_update", "reject_update",
    "open_file", "moed_a", "moed_b", "moed_c",
    "lecture_attend", "lecture_no_attend", "schedule_recording",
    "ready", "needs_time",
    "lecture_mode_attend", "lecture_mode_recording", "lecture_mode_per_course",
    "works_yes", "works_no",
    "onboarding_complete",
] + list(SNOOZE_CONFIGS.keys()) + list(EFFORT_BUCKETS.keys()))

_CANCEL_WORDS: Final[tuple[str, ...]] = ("בטל", "לא", "סגור", "עזוב", "cancel", "never mind", "נעזוב")

_MOED_RE: Final = re.compile(r'מועד\s*([אבג])|([אבג])', re.UNICODE)


def _extract_moed(text: str) -> str | None:
    m = _MOED_RE.search(text)
    return (m.group(1) or m.group(2)) if m else None
