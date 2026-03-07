# TASK-027: Redis Caching

**Phase:** Phase 4
**Complexity:** Small

## Description

Add Redis caching for performance.

## Cache Keys
- `effort:{course_code}:{assignment_label}` — TTL 1 hour — `effort_aggregates` result
- `personalization_ctx:{user_id}` — TTL 5 minutes — pre-fetched context variables
- `gcal_events:{user_id}` — TTL 15 minutes — fetched calendar events
- `timeline:{user_id}` — TTL 2 minutes — compiled timeline response

## Session State
Use Redis for Celery broker + result backend.

## Deliverable
`app/services/cache.py` with typed get/set/invalidate helpers. Integration test: effort aggregate cache hit vs. miss.

## Dependencies
- TASK-002 (FastAPI skeleton)

## Dependencies

TASK-002

---

*Generated from PRD v2.7 task breakdown.*
