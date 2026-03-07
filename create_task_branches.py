#!/usr/bin/env python3
"""Creates all 30 task branches for the Juggle project."""
import subprocess
import sys
import os

SESSION_ID = "H7IUP"
BASE_BRANCH = "master"

TASKS = [
    ("001", "postgresql-schema", "Phase 1", "Medium",
     "Create the full PostgreSQL database schema as a single Alembic migration file (`migrations/versions/001_initial_schema.py`).\n\n## Tables\n- `users` — including `preferences` (JSONB) and `gio_memory` (JSONB)\n- `courses`\n- `deadlines` — status enum: `pending | completed | missed`\n- `exam_sittings`\n- `parsed_emails`\n- `pdf_attachments`\n- `uploaded_documents`\n- `grades`\n- `study_blocks`\n- `effort_records` — no `user_id` (anonymous)\n- `effort_aggregates`\n- `reminder_state`\n- `manual_update_log`\n- `conversation_history` — `input_method` enum: `button | typed | unknown`\n- `pdf_parse_cache` — fields: `id`, `pdf_hash` (unique), `parse_result` (JSONB), `parsed_at`, `hit_count` (default 0), `created_at`\n\n## Deliverable\nSingle Alembic migration file at `migrations/versions/001_initial_schema.py`."),

    ("002", "fastapi-skeleton", "Phase 1", "Small",
     "Scaffold the backend project structure.\n\n## Requirements\n- Python 3.11+, FastAPI, SQLAlchemy (async), Alembic, Pydantic v2\n- Folder structure: `app/api/`, `app/models/`, `app/services/`, `app/tasks/`, `app/templates/`\n- `.env.example` with all required env vars: `DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY`, `MAILGUN_API_KEY`, `S3_BUCKET`, `S3_ENDPOINT`, `GCal_CLIENT_ID`, `GCAL_CLIENT_SECRET`, `SECRET_KEY`\n- `requirements.txt` with pinned versions\n- `main.py` with app factory, CORS (allow all in dev), and health check endpoint `GET /health`\n\n## Deliverable\nRunnable skeleton where `uvicorn main:app` starts without errors."),

    ("003", "user-auth", "Phase 1", "Medium",
     "Implement authentication with email/password and Google OAuth flows.\n\n## Email/Password Flow\n- `POST /auth/register` — accepts `email`, `password`; sends 6-digit verification code; stores user with `onboarding_completed=false`\n- `POST /auth/verify` — accepts `email`, `code`; marks email verified; returns JWT\n- `POST /auth/login` — accepts `email`, `password`; returns JWT\n\n## Google OAuth Flow\n- `GET /auth/google` — redirects to Google OAuth consent\n- `GET /auth/google/callback` — exchanges code, creates/upserts user, returns JWT\n- Auto-populates `users.name` and `users.email` from Google profile\n\n## Virtual Email Generation\nOn user creation, generate `{firstname}.{lastname}.{4-char-random}@students.juggle.app` and store in `users.virtual_email`.\n\n## Middleware\nJWT bearer auth middleware that populates `request.state.user`.\n\n## Deliverable\nAuth routes + middleware. Unit tests for register, verify, login flows."),

    ("004", "inbound-email-webhook", "Phase 1", "Medium",
     "Handle incoming emails from Mailgun/Postmark.\n\n## Endpoint\n`POST /webhooks/email/inbound`\n\n## Logic\n1. Parse `to`, `from`, `subject`, `attachments[]` from webhook payload\n2. Look up user by `virtual_email` address\n3. If `preferences.forward_emails == true`: forward original email with all attachments to `users.email` via Mailgun\n4. Insert row into `parsed_emails` with `parse_status='pending'`\n5. For each PDF attachment: upload to S3, insert `pdf_attachments` row, enqueue Celery task `process_pdf_attachment(pdf_attachment_id)`\n6. Return `200 OK` immediately (async processing)\n\n**SLA:** Forwarding must happen before enqueuing — forward first, then queue.\n\n## Deliverable\nWebhook endpoint + Celery task stub (processing logic in TASK-007).\n\n## Dependencies\n- TASK-001 (schema)\n- TASK-005 (S3 storage)"),

    ("005", "s3-storage-service", "Phase 1", "Small",
     "Thin wrapper around boto3 for PDF storage.\n\n## Methods\n- `upload_pdf(file_bytes: bytes, filename: str, user_id: UUID) -> str` — returns `storage_url`\n- `get_pdf_url(storage_url: str, expires_in_seconds: int = 3600) -> str` — returns presigned URL\n- `delete_pdf(storage_url: str) -> None`\n\n## Config\nReads from env vars: `S3_BUCKET`, `S3_ENDPOINT`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.\n\n## Deliverable\n`app/services/storage.py` with the three methods + unit tests using moto."),

    ("006", "react-frontend-skeleton", "Phase 1", "Medium",
     "Scaffold the React frontend with RTL support and the 5-tab navigator.\n\n## Requirements\n- React 18, Vite, Tailwind CSS\n- `dir=\"rtl\"` on root element\n- Tab navigator at bottom with 5 tabs:\n  - 💬 ג'יו (default, route `/`)\n  - 📅 לוח זמנים (route `/timeline`)\n  - 🎓 ציונים (route `/grades`)\n  - 📬 מיילים (route `/emails`)\n  - ⚙️ הגדרות (route `/settings`)\n- Each tab renders a placeholder `<div>` with tab name\n- React Router v6 for routing\n- Auth context provider (reads JWT from localStorage, redirects to `/login` if missing)\n- `/login` page: Google OAuth button + email/password form\n\n## Deliverable\n`npm run dev` shows the 5-tab shell with navigation working."),

    ("007", "pdf-extraction", "Phase 1", "Medium",
     "Implement the PDF processing pipeline up to (not including) LLM parsing.\n\n## Function: `extract_pdf_text(pdf_bytes: bytes) -> dict`\nReturns:\n```python\n{\n  \"readable\": bool,\n  \"text\": str | None,\n  \"page_count\": int,\n  \"raw_text_length\": int\n}\n```\n**Readability rule:** `readable=True` if extracted text length > 100 chars AND contains Hebrew characters.\n\n## Pre-filter: `has_extractable_events(text: str) -> bool`\nKeyword scan with regex patterns for ממ\"ן, בחינה, dates in DD/MM/YYYY and \"14 במרץ\" formats, ציון, etc. Returns `False` → skip LLM.\n\n## Cache Check: `get_cached_parse(pdf_bytes: bytes) -> dict | None`\nCompute SHA-256 of bytes, query `pdf_parse_cache` table. If hit: increment `hit_count`, return `parse_result`. If miss: return `None`.\n\n## Deliverable\n`app/services/pdf_extractor.py` + unit tests with real Hebrew PDF fixtures.\n\n## Dependencies\n- TASK-001 (schema)"),

    ("008", "gio-chat-ui", "Phase 1", "Large",
     "Build the chat thread UI component.\n\n## Requirements\n- Chat bubble component: Gio messages on the left (grey), user messages on the right (blue)\n- RTL layout throughout\n- Button set renderer: renders `buttons[]` array as rounded pill buttons, max 4 per row\n- \"משהו אחר...\" accordion: collapsed by default, opens to reveal text input\n- Submitting a button tap: POSTs `{ message_id, button_value, input_method: \"button\" }` to backend\n- Submitting typed text: POSTs `{ message_id, text, input_method: \"typed\" }` to backend\n- Chat thread is scrollable; auto-scrolls to latest message\n- `navigate_hint` renders as a tappable text link, navigates to relevant tab\n\n## API\n- `GET /api/chat/history` — returns last N messages\n- `POST /api/chat/message` — sends user input\n\n## Deliverable\nFully functional chat UI on the ג'יו tab. Buttons render and submit. Accordion works.\n\n## Dependencies\n- TASK-006 (React skeleton)\n- TASK-013 (Gio API)"),

    ("009", "claude-haiku-pdf-parser", "Phase 2", "Medium",
     "Implement LLM-based event extraction from PDF text.\n\n## Function: `parse_pdf_with_llm(text: str, user_id: UUID) -> dict`\n\n## Prompt Requirements\n- System: instruct Claude to extract structured events from Hebrew OUI PDFs\n- Extract: assignments (ממ\"נים), exams (בחינות) with all מועדים, lectures, grades\n- Output: strict JSON with `events[]`, each with `type`, `title`, `course_code`, `due_date` (ISO), `confidence` (high/medium/low)\n- For exams: `exam_dates[]` with `moed_label`, `sitting_date`, `location`\n\n## After LLM Response\n- Store result in `pdf_parse_cache`\n- Insert events into `deadlines` / `exam_sittings` tables\n- High confidence → `needs_review=false`; medium/low → `needs_review=true`\n- Enqueue `send_gio_post_parse_message(user_id, parse_result)`\n\n**Model:** `claude-3-5-haiku-20241022`\n\n## Deliverable\n`app/services/pdf_parser.py`. Integration test: parse a real OUI syllabus PDF, assert ≥1 deadline inserted.\n\n## Dependencies\n- TASK-007 (PDF extraction)\n- TASK-001 (schema)"),

    ("010", "pdf-pipeline-celery", "Phase 2", "Medium",
     "Wire together TASK-007 and TASK-009 into the complete pipeline.\n\n## Task: `process_pdf_attachment(pdf_attachment_id: UUID)`\n\n## Steps (exact order)\n1. Fetch `pdf_attachments` row, download PDF bytes from S3\n2. Compute SHA-256 hash → check `pdf_parse_cache`\n   - Cache hit: use result directly, skip to step 6\n3. `extract_pdf_text()` → assess readability\n4. If unreadable: update `parse_status='unreadable'`, send Gio \"unreadable PDF\" message, stop\n5. `has_extractable_events(text)` → if False: update `parse_status='no_events'`, stop\n6. `parse_pdf_with_llm()` → insert events\n7. Update `parse_status='parsed'`, send Gio post-parse message\n\n**Same task used for both email attachments (TASK-004) and manual uploads (TASK-011).**\n\n## Deliverable\n`app/tasks/pdf_pipeline.py`. End-to-end test with mock Anthropic API response.\n\n## Dependencies\n- TASK-007, TASK-009, TASK-005"),

    ("011", "manual-pdf-upload", "Phase 2", "Small",
     "Allow students to upload PDFs directly.\n\n## Endpoint\n`POST /api/documents/upload` (multipart form, auth required)\n\n## Logic\n1. Accept PDF file, upload to S3\n2. Insert `uploaded_documents` row with `parse_status='pending'`\n3. Attempt course inference from filename/content (fuzzy match against user's `courses`)\n4. Store `inferred_course_id` and `course_match_confidence` if confident\n5. Enqueue `process_pdf_attachment(document_id)`\n6. Return `202 Accepted` immediately\n\n**If course not identified:** post-parse Gio message will ask student to identify course.\n\n## Deliverable\nUpload endpoint + drag-and-drop zone component in React frontend.\n\n## Dependencies\n- TASK-010 (PDF pipeline)\n- TASK-005 (S3)"),

    ("012", "personalization-renderer", "Phase 2", "Large",
     "Implement the context variable injection system.\n\n## Function: `render_gio_message(template_id: str, ctx: dict) -> GioMessage`\n\n## Must Implement\n- Load template from `app/templates/gio_templates.yaml`\n- `classify_urgency(days_until: int) -> str` — maps to `low | medium | high | urgent | day_of`\n- `get_opening(time_of_day: str, day_of_week: str) -> str` — all variants from PRD table\n- `get_due_day_phrase(days_until: int) -> str` — \"היום\" / \"מחר\" / \"מחרתיים\" / \"ביום X\" / \"בעוד N ימים\"\n- `get_workload_line(other_due_soon_count: int) -> str` — empty string if 0\n- `get_behavioral_callback(ctx: dict) -> str` — uses `last_start_days_before` from gio_memory\n\n## GioMessage Schema\n```python\n@dataclass\nclass GioMessage:\n    text: str\n    buttons: list[dict]   # {text, value, style}\n    escape_hatch: bool\n    navigate_hint: dict | None = None\n    context: dict | None = None\n```\n\n## Deliverable\n`app/services/personalization.py` + `app/templates/gio_templates.yaml`. Unit tests covering every urgency variant and opening combination.\n\n## Dependencies\n- TASK-001 (schema)\n- TASK-010 (pipeline, for post-parse messages)"),

    ("013", "gio-message-api", "Phase 2", "Large",
     "Backend endpoints for the chat interface.\n\n## Endpoints\n- `GET /api/chat/history?limit=50&before_id=<uuid>` — paginated `conversation_history` for authed user\n- `POST /api/chat/message` — accepts `{ message_id, button_value?, text?, input_method }`; logs to `conversation_history`; routes to template or LLM handler; returns `GioMessage`\n\n## Template Handler\nIf `button_value` matches known value (`completed`, `dismiss`, `snooze_3d`, etc.) → handle without LLM.\n\n## LLM Handler\nIf `input_method == 'typed'` or `button_value == 'other'` → call Claude Haiku with conversation history + user context.\n\n## Deliverable\n`app/api/chat.py`. Integration test: button tap returns correct template response without LLM call.\n\n## Dependencies\n- TASK-012 (personalization renderer)\n- TASK-003 (auth)"),

    ("014", "timeline-tab", "Phase 2", "Medium",
     "Build the read-only timeline view.\n\n## Backend\n`GET /api/timeline?days=30` — returns all `deadlines` for authed user, sorted by `due_date`, with joined course name, type, status badge, and effort estimate.\n\n## Frontend\n- Chronological list of items within 30 days + beyond\n- Each item: course name, type (ממ\"ן / בחינה / הרצאה), date (DD/MM/YYYY), status badge, effort estimate (~6.5 שעות)\n- Urgent strip at top for items due within 72 hours\n- Tapping item opens detail card with Gio context summary and two action buttons\n- RTL layout throughout\n\n## Deliverable\nTimeline tab fully populated from real data.\n\n## Dependencies\n- TASK-008 (chat UI)\n- TASK-013 (Gio API)"),

    ("015", "proactivity-scheduler", "Phase 3", "Large",
     "Implement the scheduler that sends proactive Gio messages.\n\n## Celery Beat Schedule\nRuns every 2 hours.\n\n## Per User, Per Deadline\n1. Compute `days_until` for each pending deadline\n2. Look up `reminder_state` for `(user_id, deadline_id)` pair\n3. Apply anti-creep rules:\n   - Max 1 proactive message per topic per day\n   - 3 consecutive snoozes → reduce to every 2 days (override if `days_until < 5`)\n   - Skip if `silenced_until` in future\n   - Skip if current time in `quiet_hours` (23:00–07:00 Jerusalem)\n   - Skip if Shabbat blackout enabled and current time is Shabbat\n4. If should send: call `render_gio_message()`, insert into `conversation_history`, update `reminder_state`\n\n## Cadences\n- Assignment: 10 days, 7 days (if no study block), 3 days, 1 day, day-of\n- Exam: 14 days, 5 days\n- Lecture (attend mode): N minutes before start\n- Lecture (recording mode + prompt=true): after lecture end + delay\n\n## Deliverable\n`app/tasks/scheduler.py`. Unit test: assert correct urgency variant for each `days_until` value.\n\n## Dependencies\n- TASK-012 (personalization)\n- TASK-013 (Gio API)"),

    ("016", "exam-date-selection", "Phase 3", "Medium",
     "Handle exam PDFs with multiple מועדים.\n\n## Trigger\nPost-parse, when `exam_sittings` has ≥2 rows for the same `deadline_id`.\n\n## Gio Message\nRender dynamic buttons, one per מועד: `[מועד א׳ — 15 באפריל, 09:00]`\n\n## On Button Tap\n- Mark selected `exam_sittings` row as `status='confirmed'`\n- Mark other rows as `status='optional'`\n- If Google Calendar connected: create standard GCal event for confirmed מועד, tentative events for others\n- Store `gcal_event_id` on each row\n- Gio confirms selection\n\n## Change Flow\nIf student says \"שיניתי דעתי\" → Gio re-renders the מועד buttons.\n\n## Deliverable\n`app/services/exam_flow.py` + handler in TASK-013 template router.\n\n## Dependencies\n- TASK-010 (PDF pipeline)\n- TASK-013 (Gio API)"),

    ("017", "completion-effort-flow", "Phase 3", "Medium",
     "Handle the completion check-in and crowdsourced effort data.\n\n## Completion Handler (triggered on `completed` button tap)\n1. Update `deadlines.status = 'completed'`\n2. Send effort collection message with bucket buttons (5 buckets each for assignment and exam)\n\n## Effort Submission Handler\n1. Convert bucket to midpoint float (e.g. \"2–4\" → 3.0)\n2. Insert into `effort_records` with NO `user_id`, `input_method='button_bucket'` or `'typed'`\n3. Gio thanks: \"תודה 🙏 עוזר לסטודנטים הבאים לתכנן.\"\n\n## Nightly Aggregation: `compute_effort_aggregates()`\n- Groups `effort_records` by `course_code + assignment_label`\n- Requires `sample_count >= 5` before writing to `effort_aggregates`\n- Computes `mean_hours`, `p25_hours`, `p75_hours`\n- Stores in `effort_aggregates`, invalidates Redis cache key\n\n## Deliverable\nFlow handlers + nightly Celery task. Unit test: bucket midpoint conversion for all bucket values.\n\n## Dependencies\n- TASK-013 (Gio API)"),

    ("018", "grades-tab", "Phase 3", "Medium",
     "Build the grades view.\n\n## Backend\n`GET /api/grades` — returns all grades grouped by course, with running average per course and trend indicator.\n\n## Frontend\n- Per-course breakdown: list assignments and exams with grade, max grade, date\n- Running average per course\n- Trend indicator per course (↑↓→)\n- Tapping a grade shows source and date\n- \"דווח ל-Gio\" button: navigates to ג'יו tab with pre-filled message\n- No manual entry form\n\n## Grade Notification Gio Messages (from TASK-010 pipeline)\n- Above average: \"קיבלת {grade} על {title} ב{course} 🎉...\" + feedback buttons\n- Below threshold (default <70): \"קיבלת {grade} על {title}. מועד ב׳ עדיין פתוח.\" + action buttons\n\n## Deliverable\nGrades tab with real data + grade notification messages from pipeline.\n\n## Dependencies\n- TASK-008 (chat UI)\n- TASK-010 (pipeline)"),

    ("019", "email-log-tab", "Phase 3", "Small",
     "Build the email log view.\n\n## Backend\n`GET /api/emails` — returns all `parsed_emails` for authed user, sorted by `received_at` desc, with `parse_status` and attachment count.\n\n## Frontend\n- List of all OUI emails: subject, date, parse status badge (parsed / unreadable / partial / pending), attachment count\n- Unread badge for unprocessed/unreadable items\n- Tapping an email: shows extracted events if parsed, or unreadable notice with link to PDF attachment (presigned S3 URL)\n\n## Deliverable\nEmail log tab populated from real data.\n\n## Dependencies\n- TASK-006 (React skeleton)\n- TASK-004 (email webhook)"),

    ("020", "settings-tab", "Phase 3", "Medium",
     "Build the settings screen.\n\n## UI Components\n- Virtual email address: displayed + \"📋 העתק\" copy button\n- Forward emails toggle → updates `preferences.forward_emails`\n- Google Calendar connect button or \"מחובר ✓\" state\n- Quiet hours: time range picker → `preferences.quiet_hours`\n- Shabbat blackout: toggle → `preferences.shabbat_blackout`\n- Grade alert threshold: slider 0–100 → `preferences.grade_threshold`\n- Minimum study session: slider in 30min increments\n- Preferred study windows: multi-select\n- Effort contribution opt-out: toggle\n- \"שינויים ידניים\" section: read-only log from `manual_update_log`\n- Data deletion button: modal → `DELETE /api/users/me`\n\n## Backend Endpoints\n- `PATCH /api/users/me/preferences` — partial update of `preferences` JSON\n- `DELETE /api/users/me` — full account + data deletion\n\n## Deliverable\nSettings tab with all controls wired to backend.\n\n## Dependencies\n- TASK-003 (auth)\n- TASK-006 (React skeleton)"),

    ("021", "manual-record-update", "Phase 3", "Medium",
     "Handle conversational updates from students.\n\n## NLU Trigger\nTyped messages containing update intent — detected by LLM handler in TASK-013.\n\n## Confirmation Pattern (always)\n1. Student types natural language update\n2. Gio rephrases and asks for confirmation with `[כן, עדכן]` `[לא, תקן]`\n3. `[כן, עדכן]` → update `deadlines` row, insert `manual_update_log`, update GCal if connected\n4. `[לא, תקן]` → Gio asks: \"מה הפרטים הנכונים?\"\n\n## gio_memory Updates\n- Store behavioral preferences mentioned in conversation\n- `last_start_days_before`: updated when student marks completion\n\n## Deliverable\n`app/services/manual_update.py`. Handles date postponement, cancellation, and preference updates.\n\n## Dependencies\n- TASK-013 (Gio API)\n- TASK-022 (GCal, for calendar updates)"),

    ("022", "gcal-oauth", "Phase 4", "Large",
     "Implement Google Calendar integration.\n\n## OAuth Flow\n- `GET /api/gcal/connect` → redirect to Google consent (scopes: `calendar.readonly` + `calendar.events`)\n- `GET /api/gcal/callback` → exchange code, encrypt token with AES-256, store in `users.google_calendar_token`\n- `GET /api/gcal/status` → returns `{ connected: bool }`\n- `DELETE /api/gcal/disconnect` → revoke token, null out DB column\n\n## Conflict Detection: `get_free_slots(user_id, duration_hours, after_date, count=3) -> list[TimeSlot]`\n- Fetch next 14 days of GCal events\n- Exclude: `work_hours` on `work_days`, `quiet_hours`, Shabbat if blackout enabled\n- Returns top 3 slots of `duration_hours` length\n\n## Deliverable\n`app/services/gcal.py`. Tokens encrypted at rest. Manual test: connect calendar, call `get_free_slots`, assert 3 results.\n\n## Dependencies\n- TASK-003 (auth)"),

    ("023", "study-slot-booking", "Phase 4", "Medium",
     "Wire together conflict detection and calendar event creation.\n\n## Flow Trigger\nUser taps `[כן, אמצא זמן ללמוד]` or `[כן, קבע]`\n\n## Steps\n1. Call `get_free_slots()` for the deadline's estimated hours\n2. Render dynamic slot buttons (max 3): e.g. `[רביעי 19:00–21:30]`\n3. User taps a slot:\n   - If GCal connected: create event titled \"לימוד: {course_name}\"\n   - Insert `study_blocks` row with `status='scheduled'`\n   - Gio confirms booking\n4. 1 hour before study block: Celery Beat sends reminder Gio message\n\n**If no GCal connected:** slots generated from `work_days`/`work_hours` + `preferred_study_windows`.\n\n## OR-Tools Integration (optional)\n`app/services/study_scheduler.py` — CP-SAT solver. Fallback: simple greedy slot finder.\n\n## Deliverable\nFull slot booking flow working end-to-end.\n\n## Dependencies\n- TASK-022 (GCal)\n- TASK-015 (scheduler)"),

    ("024", "onboarding-flow", "Phase 4", "Large",
     "Implement the 6-step onboarding conversation in Gio chat.\n\n## Pre-condition\nUser just authenticated, `onboarding_completed = false`.\n\n## Steps\n1. **Step 1** (email/password only): Gio asks for name → free text → store `users.name`\n2. **Step 2**: Virtual email display + forwarding toggle + action buttons\n3. **Step 3**: Lecture attendance style → 3 buttons → sub-questions → store `gio_memory.lecture_mode`\n4. **Step 4**: Work schedule → yes/no → if yes: multi-select work days → work hours → GCal connect option\n5. **Step 5**: Notification preferences → assignment reminder lead time → exam reminder lead time\n6. **Step 6**: Done message + `[העלה סילבוס עכשיו]` / `[אחר כך]`\n\n## Resume Support\nStore current step in `users.onboarding_step`; resume from last incomplete step.\n\n**On completion:** set `onboarding_completed = true`, clear `onboarding_step`.\n\n## Deliverable\nFull onboarding renders in Gio chat. All preferences stored correctly. Skip handling works.\n\n## Dependencies\n- TASK-013 (Gio API)\n- TASK-003 (auth)"),

    ("025", "batched-llm-reminders", "Phase 4", "Medium",
     "Implement the daily 06:00 batch job for LLM-generated nudges.\n\n## Celery Beat Task\n`generate_daily_llm_reminders()` — runs at 06:00 Asia/Jerusalem\n\n## Logic\n1. Find all users who need an LLM-generated nudge today\n2. Build batch prompt: one JSON object per user with `name`, `assignment`, `course`, `days_until`, `last_start_days_before`, `other_due_count`\n3. Single Claude Haiku call — return `user_id|reminder_text` per line, max 120 chars, Hebrew, warm tone\n4. Parse response, call `schedule_gio_message(user_id, text, buttons=get_reminder_buttons(user_id))` for each\n5. Log batch size and total tokens used\n\n**Routing rule:** nudges requiring LLM go to this batch; urgent reminders with `days_until < 1` go real-time.\n\n## Deliverable\n`app/tasks/batch_reminders.py`. Unit test: mock 5-user batch, assert 5 messages scheduled.\n\n## Dependencies\n- TASK-015 (scheduler)\n- TASK-017 (effort flow, for `last_start_days_before`)"),

    ("026", "parse-confirmation-flow", "Phase 4", "Medium",
     "Handle medium/low confidence parses that need student review.\n\n## Trigger\nAfter LLM parse, any event with `confidence != 'high'` → sets `deadlines.needs_review = true`.\n\n## Gio Message After Parse\n- Shows parsed events summary\n- Adds `[נראה נכון ✓]` `[יש שגיאה]` buttons\n\n## On `[יש שגיאה]`\n- Gio asks: \"מה לא נכון?\" → free text\n- LLM interprets correction → re-renders confirmation with corrected data\n- On `[כן, עדכן]` → update `deadlines` row, insert `manual_update_log`, clear `needs_review`\n\n## Course Identification Flow\nWhen course not identified from PDF → render dynamic course buttons from user's `courses`.\n\n## Deliverable\nConfirmation flow wired into post-parse Gio message sequence.\n\n## Dependencies\n- TASK-009 (PDF parser)\n- TASK-013 (Gio API)"),

    ("027", "redis-caching", "Phase 4", "Small",
     "Add Redis caching for performance.\n\n## Cache Keys\n- `effort:{course_code}:{assignment_label}` — TTL 1 hour — `effort_aggregates` result\n- `personalization_ctx:{user_id}` — TTL 5 minutes — pre-fetched context variables\n- `gcal_events:{user_id}` — TTL 15 minutes — fetched calendar events\n- `timeline:{user_id}` — TTL 2 minutes — compiled timeline response\n\n## Session State\nUse Redis for Celery broker + result backend.\n\n## Deliverable\n`app/services/cache.py` with typed get/set/invalidate helpers. Integration test: effort aggregate cache hit vs. miss.\n\n## Dependencies\n- TASK-002 (FastAPI skeleton)"),

    ("028", "analytics-endpoint", "Phase 4", "Small",
     "Track button tap rate vs. typed rate per template.\n\n## DB Query\nGroup `conversation_history` by `template_id` + `input_method`, compute tap rate % per template.\n\n## Endpoint\n`GET /api/admin/analytics/input-methods` (admin auth only)\n\nReturns:\n```json\n[\n  { \"template_id\": \"deadline_nudge_high\", \"button_pct\": 87, \"typed_pct\": 13, \"total\": 234 },\n  ...\n]\n```\n\n**Warning:** if `typed_pct > 15%` on any template, log a warning.\n\n## Deliverable\nAnalytics endpoint + simple read-only admin page in React frontend.\n\n## Dependencies\n- TASK-013 (Gio API, for conversation_history data)"),

    ("029", "rtl-polish", "Phase 4", "Medium",
     "Audit and fix RTL rendering across all React components.\n\n## Checklist\n- All text is right-aligned by default\n- Chat bubbles: Gio on LEFT (assistant), user on RIGHT\n- Button sets flow right-to-left\n- Tab navigator labels in Hebrew\n- Date formatting: DD/MM/YYYY throughout (not MM/DD)\n- Numbers: left-to-right within RTL context\n- Tailwind: use `rtl:` variants where needed\n- Test in Chrome with `dir=\"rtl\"` forced\n\n## Deliverable\nAudit report + all RTL issues fixed.\n\n## Dependencies\n- All frontend tasks (TASK-006, 008, 014, 018, 019, 020)"),

    ("030", "e2e-test-suite", "Phase 4", "Medium",
     "Write E2E tests covering the two critical happy paths.\n\n## Test 1 — Email with readable PDF\n1. POST to `/webhooks/email/inbound` with a test PDF attachment\n2. Assert: PDF uploaded to S3, Celery task enqueued\n3. Run task synchronously (eager mode)\n4. Assert: `deadlines` row inserted, `conversation_history` row inserted\n5. Assert: Gio message contains correct course name and days_until\n\n## Test 2 — Student completes assignment\n1. POST to `/api/chat/message` with `button_value='completed'`\n2. Assert: `deadlines.status = 'completed'`\n3. Assert: effort collection Gio message returned with 5 bucket buttons\n4. POST bucket tap\n5. Assert: `effort_records` row inserted with no `user_id`\n\n## Deliverable\n`tests/e2e/test_core_flows.py`. Both tests pass with a real test DB (not mocked).\n\n## Dependencies\n- All Phase 1–3 tasks"),
]

PHASE_DEPS = {
    "001": [],
    "002": [],
    "003": ["001"],
    "004": ["001", "003", "005"],
    "005": [],
    "006": [],
    "007": ["001"],
    "008": ["006"],
    "009": ["007"],
    "010": ["005", "007", "009"],
    "011": ["005", "010"],
    "012": ["001", "010"],
    "013": ["003", "012"],
    "014": ["008", "013"],
    "015": ["012", "013"],
    "016": ["010", "013"],
    "017": ["013"],
    "018": ["008", "010"],
    "019": ["004", "006"],
    "020": ["003", "006"],
    "021": ["013"],
    "022": ["003"],
    "023": ["015", "022"],
    "024": ["003", "013"],
    "025": ["015", "017"],
    "026": ["009", "013"],
    "027": ["002"],
    "028": ["013"],
    "029": ["006", "008", "014", "018", "019", "020"],
    "030": [],
}

def run(cmd, silent_errors=False):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and not silent_errors:
        print(f"  ERROR: {result.stderr.strip()}")
    return result

def create_branch(num, slug, phase, complexity, description):
    branch = f"claude/task-{num}-{slug}-{SESSION_ID}"
    print(f"\n[{num}/030] Creating {branch}...")

    # Checkout base
    run(f"git checkout {BASE_BRANCH} -q")

    # Check if branch already exists
    check = run(f"git branch --list {branch}", silent_errors=True)
    if check.stdout.strip():
        print(f"  Branch already exists, deleting...")
        run(f"git branch -D {branch}", silent_errors=True)

    run(f"git checkout -b {branch} -q")

    # Create task file
    os.makedirs(".tasks", exist_ok=True)
    task_content = f"""# TASK-{num}: {slug.replace('-', ' ').title()}

**Phase:** {phase}
**Complexity:** {complexity}

## Description

{description}

## Dependencies

{', '.join(['TASK-' + d for d in PHASE_DEPS.get(num, [])]) or 'None'}

---

*Generated from PRD v2.7 task breakdown.*
"""
    with open(f".tasks/TASK-{num}.md", "w") as f:
        f.write(task_content)

    run(f"git add .tasks/TASK-{num}.md")

    # Commit with GPG signing (required by git config)
    commit_msg = f"""chore: scaffold TASK-{num} {slug}

Phase: {phase} | Complexity: {complexity}

https://claude.ai/code/session_01UdeZr4pKmYLFZrMPAHe69A"""

    result = run(f'git commit -m "{commit_msg}"')
    if result.returncode != 0:
        print(f"  Commit failed: {result.stderr}")
        return False

    # Push
    print(f"  Pushing...")
    push_result = run(f"git push -u origin {branch} -q 2>&1")
    if push_result.returncode != 0:
        print(f"  Push failed: {push_result.stderr}")
        return False

    print(f"  ✓ Done")
    return True

if __name__ == "__main__":
    os.chdir("/home/user/juggle")
    success = 0
    failed = []

    for num, slug, phase, complexity, description in TASKS:
        if create_branch(num, slug, phase, complexity, description):
            success += 1
        else:
            failed.append(f"TASK-{num}")

    print(f"\n{'='*50}")
    print(f"Created: {success}/30 branches")
    if failed:
        print(f"Failed: {', '.join(failed)}")

    # Switch back to original branch
    run(f"git checkout claude/task-breakdown-phases-{SESSION_ID} -q")
    print("Done!")
