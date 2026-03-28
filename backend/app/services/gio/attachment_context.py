import uuid
from datetime import datetime, timezone
from typing import Final

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.deadline import Deadline
from app.models.grade import Grade
from app.models.pdf_attachment import PdfAttachment
from app.models.uploaded_document import UploadedDocument

_DEADLINE_TYPE_LABELS: Final[dict[str, str]] = {
    "assignment": "מטלה",
    "exam": "בחינה",
    "lecture": "הרצאה",
    "announcement": "הודעה",
}
_DEADLINE_STATUS_LABELS: Final[dict[str, str]] = {
    "pending": "ממתין",
    "completed": "הושלם",
    "missed": "הוחמץ",
}
_PDF_STATUS_LABELS: Final[dict[str, str]] = {
    "pending": "בעיבוד",
    "parsed": "עובד בהצלחה",
    "unreadable": "לא ניתן לקריאה",
    "no_events": "לא נמצאו אירועים",
    "failed": "שגיאה בעיבוד",
}


async def _build_attachment_context(
    db: AsyncSession,
    user_id: uuid.UUID,
    attachments: list,
) -> str | None:
    """Query DB for each attachment ref and return a rich Hebrew context block."""
    if not attachments:
        return None

    parts: list[str] = []
    now = datetime.now(timezone.utc)

    for ref in attachments:
        att_type: str = ref.type
        att_id: uuid.UUID = ref.id

        if att_type == "deadline":
            result = await db.execute(
                select(Deadline)
                .join(Deadline.course)
                .options(selectinload(Deadline.course), selectinload(Deadline.exam_sittings))
                .where(Deadline.id == att_id, Course.user_id == user_id)
            )
            dl = result.scalar_one_or_none()
            if not dl:
                continue
            course = dl.course
            course_str = course.name + (f" ({course.code})" if course.code else "")
            lines = [
                f"[אירוע: {dl.title}]",
                f"קורס: {course_str}",
                f"סוג: {_DEADLINE_TYPE_LABELS.get(dl.type.value, dl.type.value)}",
                f"תאריך: {dl.due_date.strftime('%d/%m/%Y %H:%M')}",
                f"סטטוס: {_DEADLINE_STATUS_LABELS.get(dl.status.value, dl.status.value)}",
            ]
            for sitting in dl.exam_sittings:
                loc = f" — {sitting.location}" if sitting.location else ""
                lines.append(
                    f"מועד {sitting.moed_label}: {sitting.sitting_date.strftime('%d/%m/%Y %H:%M')}{loc}"
                )
            parts.append("\n".join(lines))

        elif att_type in ("grade", "course"):
            course_result = await db.execute(
                select(Course).where(Course.id == att_id, Course.user_id == user_id)
            )
            course = course_result.scalar_one_or_none()
            if not course:
                continue

            grades_result = await db.execute(
                select(Grade)
                .where(Grade.course_id == att_id, Grade.user_id == user_id)
                .order_by(Grade.received_at.desc())
                .limit(10)
            )
            grades = grades_result.scalars().all()

            lines = [f"[קורס: {course.name}]"]
            if course.code:
                lines.append(f"קוד: {course.code}")
            if course.semester:
                lines.append(f"סמסטר: {course.semester}")

            if grades:
                pcts = [g.grade / g.max_grade * 100 for g in grades if g.max_grade > 0]
                avg = sum(pcts) / len(pcts) if pcts else 0
                lines.append(f"ממוצע ציונים: {avg:.1f}%")
                lines.append("ציונים:")
                for g in grades[:6]:
                    pct = g.grade / g.max_grade * 100 if g.max_grade > 0 else 0
                    title = g.assignment_title or "ציון"
                    lines.append(
                        f"  • {title}: {g.grade}/{g.max_grade} ({pct:.0f}%) — {g.received_at.strftime('%d/%m/%Y')}"
                    )

            upcoming_result = await db.execute(
                select(Deadline)
                .where(Deadline.course_id == att_id, Deadline.due_date >= now)
                .order_by(Deadline.due_date.asc())
                .limit(5)
            )
            upcoming = upcoming_result.scalars().all()
            if upcoming:
                lines.append("אירועים קרובים:")
                for dl in upcoming:
                    type_str = _DEADLINE_TYPE_LABELS.get(dl.type.value, dl.type.value)
                    lines.append(f"  • {dl.title} ({type_str}) — {dl.due_date.strftime('%d/%m/%Y')}")

            parts.append("\n".join(lines))

        elif att_type == "pdf":
            doc_result = await db.execute(
                select(UploadedDocument)
                .options(selectinload(UploadedDocument.inferred_course))
                .where(UploadedDocument.id == att_id, UploadedDocument.user_id == user_id)
            )
            doc = doc_result.scalar_one_or_none()
            if not doc:
                continue
            status_label = _PDF_STATUS_LABELS.get(doc.parse_status.value, doc.parse_status.value)
            lines = [f"[מסמך שהועלה: {doc.filename}]", f"סטטוס: {status_label}"]
            if doc.inferred_course:
                lines.append(f"קורס מזוהה: {doc.inferred_course.name}")

            # Enrich with extracted content when the PDF has been processed
            if doc.pdf_hash:
                att_rows = await db.execute(
                    select(PdfAttachment).where(
                        PdfAttachment.pdf_hash == doc.pdf_hash,
                        PdfAttachment.user_id == user_id,
                    )
                )
                pdf_att_ids = [r.id for r in att_rows.scalars().all()]

                if pdf_att_ids:
                    dl_rows = await db.execute(
                        select(Deadline)
                        .options(selectinload(Deadline.course), selectinload(Deadline.exam_sittings))
                        .where(Deadline.source_pdf_id.in_(pdf_att_ids))
                        .order_by(Deadline.due_date.asc())
                    )
                    deadlines = dl_rows.scalars().all()
                    if deadlines:
                        lines.append("אירועים שחולצו:")
                        for dl in deadlines:
                            type_str = _DEADLINE_TYPE_LABELS.get(dl.type.value, dl.type.value)
                            course_str = dl.course.name if dl.course else ""
                            lines.append(
                                f"  • {dl.title} ({type_str}) — {dl.due_date.strftime('%d/%m/%Y')}"
                                + (f" — {course_str}" if course_str else "")
                            )
                            for sitting in dl.exam_sittings:
                                lines.append(
                                    f"    מועד {sitting.moed_label}: {sitting.sitting_date.strftime('%d/%m/%Y')}"
                                    + (f" — {sitting.location}" if sitting.location else "")
                                )

                    gr_rows = await db.execute(
                        select(Grade)
                        .options(selectinload(Grade.course))
                        .where(Grade.source_pdf_id.in_(pdf_att_ids))
                    )
                    grades = gr_rows.scalars().all()
                    if grades:
                        lines.append("ציונים שחולצו:")
                        for g in grades:
                            pct = g.grade / g.max_grade * 100 if g.max_grade > 0 else 0
                            title = g.assignment_title or "ציון"
                            course_str = g.course.name if g.course else ""
                            lines.append(
                                f"  • {title}: {g.grade}/{g.max_grade} ({pct:.0f}%)"
                                + (f" — {course_str}" if course_str else "")
                            )

            parts.append("\n".join(lines))

    return "\n\n".join(parts) if parts else None
