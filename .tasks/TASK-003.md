# TASK-003: User Auth

**Phase:** Phase 1
**Complexity:** Medium

## Description

Implement authentication with email/password and Google OAuth flows.

## Email/Password Flow
- `POST /auth/register` — accepts `email`, `password`; sends 6-digit verification code; stores user with `onboarding_completed=false`
- `POST /auth/verify` — accepts `email`, `code`; marks email verified; returns JWT
- `POST /auth/login` — accepts `email`, `password`; returns JWT

## Google OAuth Flow
- `GET /auth/google` — redirects to Google OAuth consent
- `GET /auth/google/callback` — exchanges code, creates/upserts user, returns JWT
- Auto-populates `users.name` and `users.email` from Google profile

## Virtual Email Generation
On user creation, generate `{firstname}.{lastname}.{4-char-random}@students.juggle.app` and store in `users.virtual_email`.

## Middleware
JWT bearer auth middleware that populates `request.state.user`.

## Deliverable
Auth routes + middleware. Unit tests for register, verify, login flows.

## Dependencies

TASK-001

---

*Generated from PRD v2.7 task breakdown.*
