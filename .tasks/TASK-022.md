# TASK-022: Gcal Oauth

**Phase:** Phase 4
**Complexity:** Large

## Description

Implement Google Calendar integration.

## OAuth Flow
- `GET /api/gcal/connect` → redirect to Google consent (scopes: `calendar.readonly` + `calendar.events`)
- `GET /api/gcal/callback` → exchange code, encrypt token with AES-256, store in `users.google_calendar_token`
- `GET /api/gcal/status` → returns `{ connected: bool }`
- `DELETE /api/gcal/disconnect` → revoke token, null out DB column

## Conflict Detection: `get_free_slots(user_id, duration_hours, after_date, count=3) -> list[TimeSlot]`
- Fetch next 14 days of GCal events
- Exclude: `work_hours` on `work_days`, `quiet_hours`, Shabbat if blackout enabled
- Returns top 3 slots of `duration_hours` length

## Deliverable
`app/services/gcal.py`. Tokens encrypted at rest. Manual test: connect calendar, call `get_free_slots`, assert 3 results.

## Dependencies
- TASK-003 (auth)

## Dependencies

TASK-003

---

*Generated from PRD v2.7 task breakdown.*
