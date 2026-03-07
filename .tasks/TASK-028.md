# TASK-028: Analytics Endpoint

**Phase:** Phase 4
**Complexity:** Small

## Description

Track button tap rate vs. typed rate per template.

## DB Query
Group `conversation_history` by `template_id` + `input_method`, compute tap rate % per template.

## Endpoint
`GET /api/admin/analytics/input-methods` (admin auth only)

Returns:
```json
[
  { "template_id": "deadline_nudge_high", "button_pct": 87, "typed_pct": 13, "total": 234 },
  ...
]
```

**Warning:** if `typed_pct > 15%` on any template, log a warning.

## Deliverable
Analytics endpoint + simple read-only admin page in React frontend.

## Dependencies
- TASK-013 (Gio API, for conversation_history data)

## Dependencies

TASK-013

---

*Generated from PRD v2.7 task breakdown.*
