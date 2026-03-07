# TASK-002: Fastapi Skeleton

**Phase:** Phase 1
**Complexity:** Small

## Description

Scaffold the backend project structure.

## Requirements
- Python 3.11+, FastAPI, SQLAlchemy (async), Alembic, Pydantic v2
- Folder structure: `app/api/`, `app/models/`, `app/services/`, `app/tasks/`, `app/templates/`
- `.env.example` with all required env vars: `DATABASE_URL`, `REDIS_URL`, `ANTHROPIC_API_KEY`, `MAILGUN_API_KEY`, `S3_BUCKET`, `S3_ENDPOINT`, `GCal_CLIENT_ID`, `GCAL_CLIENT_SECRET`, `SECRET_KEY`
- `requirements.txt` with pinned versions
- `main.py` with app factory, CORS (allow all in dev), and health check endpoint `GET /health`

## Deliverable
Runnable skeleton where `uvicorn main:app` starts without errors.

## Dependencies

None

---

*Generated from PRD v2.7 task breakdown.*
