# TASK-019: Email Log Tab

**Phase:** Phase 3
**Complexity:** Small

## Description

Build the email log view.

## Backend
`GET /api/emails` — returns all `parsed_emails` for authed user, sorted by `received_at` desc, with `parse_status` and attachment count.

## Frontend
- List of all OUI emails: subject, date, parse status badge (parsed / unreadable / partial / pending), attachment count
- Unread badge for unprocessed/unreadable items
- Tapping an email: shows extracted events if parsed, or unreadable notice with link to PDF attachment (presigned S3 URL)

## Deliverable
Email log tab populated from real data.

## Dependencies
- TASK-006 (React skeleton)
- TASK-004 (email webhook)

## Dependencies

TASK-004, TASK-006

---

*Generated from PRD v2.7 task breakdown.*
