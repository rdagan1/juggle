# TASK-012: Personalization Renderer

**Phase:** Phase 2
**Complexity:** Large

## Description

Implement the context variable injection system.

## Function: `render_gio_message(template_id: str, ctx: dict) -> GioMessage`

## Must Implement
- Load template from `app/templates/gio_templates.yaml`
- `classify_urgency(days_until: int) -> str` — maps to `low | medium | high | urgent | day_of`
- `get_opening(time_of_day: str, day_of_week: str) -> str` — all variants from PRD table
- `get_due_day_phrase(days_until: int) -> str` — "היום" / "מחר" / "מחרתיים" / "ביום X" / "בעוד N ימים"
- `get_workload_line(other_due_soon_count: int) -> str` — empty string if 0
- `get_behavioral_callback(ctx: dict) -> str` — uses `last_start_days_before` from gio_memory

## GioMessage Schema
```python
@dataclass
class GioMessage:
    text: str
    buttons: list[dict]   # {text, value, style}
    escape_hatch: bool
    navigate_hint: dict | None = None
    context: dict | None = None
```

## Deliverable
`app/services/personalization.py` + `app/templates/gio_templates.yaml`. Unit tests covering every urgency variant and opening combination.

## Dependencies
- TASK-001 (schema)
- TASK-010 (pipeline, for post-parse messages)

## Dependencies

TASK-001, TASK-010

---

*Generated from PRD v2.7 task breakdown.*
