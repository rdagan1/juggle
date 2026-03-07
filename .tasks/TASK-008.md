# TASK-008: Gio Chat Ui

**Phase:** Phase 1
**Complexity:** Large

## Description

Build the chat thread UI component.

## Requirements
- Chat bubble component: Gio messages on the left (grey), user messages on the right (blue)
- RTL layout throughout
- Button set renderer: renders `buttons[]` array as rounded pill buttons, max 4 per row
- "משהו אחר..." accordion: collapsed by default, opens to reveal text input
- Submitting a button tap: POSTs `{ message_id, button_value, input_method: "button" }` to backend
- Submitting typed text: POSTs `{ message_id, text, input_method: "typed" }` to backend
- Chat thread is scrollable; auto-scrolls to latest message
- `navigate_hint` renders as a tappable text link, navigates to relevant tab

## API
- `GET /api/chat/history` — returns last N messages
- `POST /api/chat/message` — sends user input

## Deliverable
Fully functional chat UI on the ג'יו tab. Buttons render and submit. Accordion works.

## Dependencies
- TASK-006 (React skeleton)
- TASK-013 (Gio API)

## Dependencies

TASK-006

---

*Generated from PRD v2.7 task breakdown.*
