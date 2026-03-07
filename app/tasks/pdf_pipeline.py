"""Celery task stub — full pipeline implemented in TASK-010."""
from celery_app import celery_app


@celery_app.task(name="tasks.process_pdf_attachment")
def process_pdf_attachment(pdf_attachment_id: str) -> None:
    """Process a PDF attachment through the extraction + LLM pipeline.

    Full implementation in TASK-010. This stub enqueues the task ID
    so the webhook can return 200 immediately.
    """
    # TASK-010 will implement: extract text → LLM parse → insert deadlines
    pass
