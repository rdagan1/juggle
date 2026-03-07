# TASK-006: React Frontend Skeleton

**Phase:** Phase 1
**Complexity:** Medium

## Description

Scaffold the React frontend with RTL support and the 5-tab navigator.

## Requirements
- React 18, Vite, Tailwind CSS
- `dir="rtl"` on root element
- Tab navigator at bottom with 5 tabs:
  - 💬 ג'יו (default, route `/`)
  - 📅 לוח זמנים (route `/timeline`)
  - 🎓 ציונים (route `/grades`)
  - 📬 מיילים (route `/emails`)
  - ⚙️ הגדרות (route `/settings`)
- Each tab renders a placeholder `<div>` with tab name
- React Router v6 for routing
- Auth context provider (reads JWT from localStorage, redirects to `/login` if missing)
- `/login` page: Google OAuth button + email/password form

## Deliverable
`npm run dev` shows the 5-tab shell with navigation working.

## Dependencies

None

---

*Generated from PRD v2.7 task breakdown.*
