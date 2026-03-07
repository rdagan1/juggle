# TASK-004: Inbound Email Webhook

**Phase:** Phase 1
**Complexity:** Medium

## Description

Handle incoming emails from Mailgun/Postmark.

## Endpoint
`POST /webhooks/email/inbound`

## Logic
1. Parse `to`, `from`, `subject`, `attachments[]` from webhook payload
2. Look up user by `virtual_email` address
3. If `preferences.forward_emails == true`: forward original email with all attachments to `users.email` via Mailgun
4. Insert row into `parsed_emails` with `parse_status='pending'`
5. For each PDF attachment: upload to S3, insert `pdf_attachments` row, enqueue Celery task `process_pdf_attachment(pdf_attachment_id)`
6. Return `200 OK` immediately (async processing)

**SLA:** Forwarding must happen before enqueuing — forward first, then queue.

## Deliverable
Webhook endpoint + Celery task stub (processing logic in TASK-007).

## Dependencies
- TASK-001 (schema)
- TASK-005 (S3 storage)

## Dependencies

TASK-001, TASK-003, TASK-005

---

*Generated from PRD v2.7 task breakdown.*
