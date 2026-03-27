# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt -r tests/requirements-test.txt

# Run dev server
uvicorn app.main:app --reload                          # http://localhost:8000

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Run all tests
pytest

# Run a single test file
pytest tests/test_auth.py

# Run a single test
pytest tests/test_auth.py::test_login_success

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Celery worker (requires Redis)
celery -A app.workers.celery_app.celery_app worker --loglevel=info --concurrency=4

# Celery Beat scheduler
celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend

npm install
npm run dev        # Dev server on :5173, proxies /api + /auth + /ws to backend:8000
npm run build      # TypeScript check + Vite production build
npm run lint       # ESLint
npm run preview    # Preview production build
```

### Docker (full stack)

```bash
docker compose up           # All 6 services: postgres, redis, backend, celery-worker, celery-beat, frontend
docker compose up backend   # Single service
```

## Architecture

Juggle is a chat-first AI study companion for Open University of Israel students. The AI assistant ("Gio") is the primary interface — all notifications, reminders, and data interactions flow through a single WebSocket chat thread.

### Backend (`backend/app/`)

**Entry point**: `main.py` — FastAPI app with 9 routers and a WebSocket endpoint at `/ws/{user_id}?token=JWT`.

**Request flow for chat**:
1. WebSocket message arrives at `api/chat.py` → `ConnectionManager` routes to `services/gio_engine.py`
2. `gio_engine.py` decides: button press → template handler (snooze/confirm/etc.) OR freeform text → Claude Haiku LLM
3. Response rendered via `services/personalization.py` which injects user context (name, courses, deadlines, time-of-day, behavioral history) into templates from `templates/gio_templates.yaml`
4. Reply sent back over WebSocket; persisted to `ConversationHistory`

**PDF pipeline** (`services/pdf_pipeline.py`): SHA-256 hash → `PdfParseCache` check → PyMuPDF extraction → Claude Haiku → store deadlines/grades. Triggered via Celery task `process_pdf_task`.

**Celery Beat schedule** (all in `workers/celery_app.py`):
- Every 2h: proactivity check — sends Gio reminders for upcoming deadlines
- Nightly 3am: effort aggregation (only published if n≥5 samples, no user_id stored)
- Nightly 4am: PDF cache cleanup

**Database**: PostgreSQL + SQLAlchemy async (asyncpg). All models in `models/`. Tests use SQLite in-memory via `tests/conftest.py`. Key design: `EffortRecord` has no `user_id` by design (anonymous).

**Google Calendar tokens** stored AES-256 Fernet-encrypted in the `User` table (`gcal_encryption_key` from settings).

### Frontend (`frontend/src/`)

**Single-page app** with 5 tabs: Gio (chat), Timeline, Grades, Emails, Settings. RTL layout (`dir="rtl" lang="he"`), mobile-first (`max-w-md`).

- **Auth state**: Zustand store in `hooks/useAuth.ts`, JWT persisted to `localStorage`
- **Chat state**: `hooks/useGioChat.ts` — WebSocket connection + message history
- **API client**: `api/client.ts` — Axios with request interceptor (injects JWT) and 401 auto-logout
- **Proxy**: Vite dev server proxies `/api`, `/auth`, `/ws` to `http://backend:8000`
- **i18n**: All Hebrew strings in `i18n/he.ts` — no hardcoded UI text

### Key external services

| Service | Purpose | Config key |
|---------|---------|-----------|
| Claude Haiku (`claude-haiku-4-5-20251001`) | PDF parsing + LLM chat | `anthropic_api_key` |
| Cloudflare R2 | PDF/document storage | `r2_*` settings |
| Mailgun | Inbound email webhook (`/api/email-webhook`) | `mailgun_api_key` |
| Google Calendar | OAuth 2.0, conflict detection | `google_*` settings |
| Google OR-Tools | Study block scheduling optimization | (library, no API key) |

---

# Juggle — Claude Instructions

## Python Best Practices

### Code Style

- Follow Black code formatting
- Use isort for import sorting
- Follow PEP 8 naming conventions:
  - snake_case for functions and variables
  - PascalCase for classes
  - UPPER_CASE for constants
- Maximum line length of 120 characters
- Use absolute imports over relative imports
- Use module-level imports
- If a signature has more than 2 arguments, add a trailing comma and reformat using black
- Use immutable data structures over mutable ones (`tuple` over `list`, `attrs.frozen` over `dataclass` etc.)

### Code Ordering

A module should be ordered as follows, unless the code flow mandates a different order:

1. imports
2. `TYPE_CHECKING` block
3. Constants
4. TypeVars
5. functions
6. classes

Inside classes, the order is as follows (unless specified otherwise):

1. `__init__` if needed
2. Implementations of `functools.cached_property`
3. Regular `property`
4. Implementation of other "dunder" methods
5. Private methods
6. Public methods

Inside each category, the methods are ordered in a logically consistent manner.

### Performance

- Use `functools.cached_property` where possible.
- Use data structures that allow efficient operations according to their use (`set` for search, `dict` for mapping etc.).

### Logging

- Maintain the existing logs, do not remove logs unless explicitly requested.
- Use `tagged_logger` from the `infra.log` module to create loggers for newly-created classes, along with a log tag that is in `UPPER_CASE`.
- Make the aforementioned logger a `functools.cached_property`.

### Typing

- Use type hints for all function parameters and returns — use MyPy-style typing
- For parameters — use the most generic typing possible. For returns — use the explicit type
- Import types from `typing` module, except builtins
- The `infra.units` module contains `TypeAlias`es and conversion functions in between them
- All constants should be marked with `typing.Final`, unless the constant's type is defined in `infra.units`, then include it as a type hint
- Prefer explicitly defining types over implicitly, for example, `Type | None` instead of `Optional`
- Use iterators where storing all items in memory is not necessary
- Use `Protocol` for duck typing
- Use `TypeVar` for generic types

### Exceptions and Error Handling

- When creating a custom exception, inherit from a known exception and implement an `__str__` that describes the exception.
- If there are more than 2 exceptions in the same module, create a parent exception that contains the name of the module from which both children exceptions will inherit.

### Testing

- Use pytest for testing
- Write tests for all routes
- Use pytest-cov for coverage
- Implement proper fixtures, avoid adding a `fixture_` prefix to their names.
- Use proper mocking using `unittest.mock`
- Test all error scenarios
