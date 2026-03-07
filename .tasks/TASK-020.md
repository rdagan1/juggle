# TASK-020: Settings Tab

**Phase:** Phase 3
**Complexity:** Medium

## Description

Build the settings screen.

## UI Components
- Virtual email address: displayed + "📋 העתק" copy button
- Forward emails toggle → updates `preferences.forward_emails`
- Google Calendar connect button or "מחובר ✓" state
- Quiet hours: time range picker → `preferences.quiet_hours`
- Shabbat blackout: toggle → `preferences.shabbat_blackout`
- Grade alert threshold: slider 0–100 → `preferences.grade_threshold`
- Minimum study session: slider in 30min increments
- Preferred study windows: multi-select
- Effort contribution opt-out: toggle
- "שינויים ידניים" section: read-only log from `manual_update_log`
- Data deletion button: modal → `DELETE /api/users/me`

## Backend Endpoints
- `PATCH /api/users/me/preferences` — partial update of `preferences` JSON
- `DELETE /api/users/me` — full account + data deletion

## Deliverable
Settings tab with all controls wired to backend.

## Dependencies
- TASK-003 (auth)
- TASK-006 (React skeleton)

## Dependencies

TASK-003, TASK-006

---

*Generated from PRD v2.7 task breakdown.*
