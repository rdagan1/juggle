# TASK-013: Gio Message Api

**Phase:** Phase 2
**Complexity:** Large

## Description

Backend endpoints for the chat interface.

## Endpoints
- `GET /api/chat/history?limit=50&before_id=<uuid>` — paginated `conversation_history` for authed user
- `POST /api/chat/message` — accepts `{ message_id, button_value?, text?, input_method }`; logs to `conversation_history`; routes to template or LLM handler; returns `GioMessage`

## Template Handler
If `button_value` matches known value (`completed`, `dismiss`, `snooze_3d`, etc.) → handle without LLM.

## LLM Handler
If `input_method == 'typed'` or `button_value == 'other'` → call Claude Haiku with conversation history + user context.

## Deliverable
`app/api/chat.py`. Integration test: button tap returns correct template response without LLM call.

## Dependencies
- TASK-012 (personalization renderer)
- TASK-003 (auth)

## Dependencies

TASK-003, TASK-012

---

*Generated from PRD v2.7 task breakdown.*
