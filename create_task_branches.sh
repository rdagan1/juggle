#!/bin/bash
set -e

SESSION_ID="H7IUP"
BASE_BRANCH="master"

declare -A TASKS
TASKS["001"]="postgresql-schema"
TASKS["002"]="fastapi-skeleton"
TASKS["003"]="user-auth"
TASKS["004"]="inbound-email-webhook"
TASKS["005"]="s3-storage-service"
TASKS["006"]="react-frontend-skeleton"
TASKS["007"]="pdf-extraction"
TASKS["008"]="gio-chat-ui"
TASKS["009"]="claude-haiku-pdf-parser"
TASKS["010"]="pdf-pipeline-celery"
TASKS["011"]="manual-pdf-upload"
TASKS["012"]="personalization-renderer"
TASKS["013"]="gio-message-api"
TASKS["014"]="timeline-tab"
TASKS["015"]="proactivity-scheduler"
TASKS["016"]="exam-date-selection"
TASKS["017"]="completion-effort-flow"
TASKS["018"]="grades-tab"
TASKS["019"]="email-log-tab"
TASKS["020"]="settings-tab"
TASKS["021"]="manual-record-update"
TASKS["022"]="gcal-oauth"
TASKS["023"]="study-slot-booking"
TASKS["024"]="onboarding-flow"
TASKS["025"]="batched-llm-reminders"
TASKS["026"]="parse-confirmation-flow"
TASKS["027"]="redis-caching"
TASKS["028"]="analytics-endpoint"
TASKS["029"]="rtl-polish"
TASKS["030"]="e2e-test-suite"

ORDER=(001 002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 019 020 021 022 023 024 025 026 027 028 029 030)

for NUM in "${ORDER[@]}"; do
  SLUG="${TASKS[$NUM]}"
  BRANCH="claude/task-${NUM}-${SLUG}-${SESSION_ID}"
  echo "Creating branch: $BRANCH"

  git checkout "$BASE_BRANCH" -q
  git checkout -b "$BRANCH" -q

  # Create task file
  mkdir -p .tasks
  cat > ".tasks/TASK-${NUM}.md" << TASKEOF
# TASK-${NUM}: ${SLUG}

See project PRD for full specification.
TASKEOF

  git add ".tasks/TASK-${NUM}.md"
  git commit -q -m "chore: scaffold TASK-${NUM} ${SLUG}

https://claude.ai/code/session_01UdeZr4pKmYLFZrMPAHe69A"

  echo "  Pushing $BRANCH..."
  git push -u origin "$BRANCH" -q 2>&1 | grep -v "^remote:" || true
  echo "  Done: $BRANCH"
done

echo ""
echo "All branches created and pushed!"
