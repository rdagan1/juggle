"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.VARCHAR(255), nullable=False),
        sa.Column("password_hash", sa.VARCHAR(255), nullable=True),
        sa.Column("name", sa.VARCHAR(255), nullable=True),
        sa.Column("virtual_email", sa.VARCHAR(255), nullable=True),
        sa.Column("google_id", sa.VARCHAR(255), nullable=True),
        sa.Column("google_calendar_token", sa.TEXT(), nullable=True),
        sa.Column(
            "email_verified",
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "onboarding_completed",
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "onboarding_step",
            sa.INTEGER(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "preferences",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "gio_memory",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("virtual_email", name="uq_users_virtual_email"),
        sa.UniqueConstraint("google_id", name="uq_users_google_id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_virtual_email", "users", ["virtual_email"], unique=True)

    # --- courses ---
    op.create_table(
        "courses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_code", sa.VARCHAR(50), nullable=False),
        sa.Column("course_name", sa.VARCHAR(255), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_courses_user_id",
            ondelete="CASCADE",
        ),
    )

    # --- deadlines ---
    op.create_table(
        "deadlines",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.VARCHAR(500), nullable=False),
        sa.Column("type", sa.VARCHAR(50), nullable=False),
        sa.Column("due_date", sa.TIMESTAMPTZ(), nullable=False),
        sa.Column(
            "status",
            sa.VARCHAR(20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "needs_review",
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("source_pdf_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gcal_event_id", sa.VARCHAR(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_deadlines_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_deadlines_course_id",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'missed')",
            name="ck_deadlines_status",
        ),
    )
    op.create_index("ix_deadlines_user_id", "deadlines", ["user_id"])
    op.create_index("ix_deadlines_due_date", "deadlines", ["due_date"])

    # --- exam_sittings ---
    op.create_table(
        "exam_sittings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("deadline_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("moed_label", sa.VARCHAR(50), nullable=True),
        sa.Column("sitting_date", sa.TIMESTAMPTZ(), nullable=False),
        sa.Column("location", sa.VARCHAR(255), nullable=True),
        sa.Column(
            "status",
            sa.VARCHAR(20),
            nullable=True,
            server_default=sa.text("'optional'"),
        ),
        sa.Column("gcal_event_id", sa.VARCHAR(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["deadline_id"],
            ["deadlines.id"],
            name="fk_exam_sittings_deadline_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('optional', 'confirmed', 'cancelled')",
            name="ck_exam_sittings_status",
        ),
    )

    # --- parsed_emails ---
    op.create_table(
        "parsed_emails",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_address", sa.VARCHAR(255), nullable=True),
        sa.Column("to_address", sa.VARCHAR(255), nullable=True),
        sa.Column("subject", sa.TEXT(), nullable=True),
        sa.Column(
            "received_at",
            sa.TIMESTAMPTZ(),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "parse_status",
            sa.VARCHAR(20),
            nullable=True,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "raw_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_parsed_emails_user_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "parse_status IN ('pending', 'parsed', 'unreadable', 'partial')",
            name="ck_parsed_emails_parse_status",
        ),
    )

    # --- pdf_attachments ---
    op.create_table(
        "pdf_attachments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("parsed_email_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploaded_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.VARCHAR(500), nullable=True),
        sa.Column("storage_url", sa.TEXT(), nullable=False),
        sa.Column("pdf_hash", sa.VARCHAR(64), nullable=True),
        sa.Column(
            "parse_status",
            sa.VARCHAR(20),
            nullable=True,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["parsed_email_id"],
            ["parsed_emails.id"],
            name="fk_pdf_attachments_parsed_email_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_pdf_attachments_user_id",
            ondelete="CASCADE",
        ),
        # uploaded_document_id FK is deferred/manual — no FK constraint here
    )

    # --- uploaded_documents ---
    op.create_table(
        "uploaded_documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.VARCHAR(500), nullable=True),
        sa.Column("storage_url", sa.TEXT(), nullable=False),
        sa.Column("inferred_course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_match_confidence", sa.FLOAT(), nullable=True),
        sa.Column(
            "parse_status",
            sa.VARCHAR(20),
            nullable=True,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_uploaded_documents_user_id",
            ondelete="CASCADE",
        ),
    )

    # Now add the FK from pdf_attachments.uploaded_document_id -> uploaded_documents.id
    op.create_foreign_key(
        "fk_pdf_attachments_uploaded_document_id",
        "pdf_attachments",
        "uploaded_documents",
        ["uploaded_document_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- grades ---
    op.create_table(
        "grades",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deadline_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.VARCHAR(500), nullable=True),
        sa.Column("grade", sa.FLOAT(), nullable=False),
        sa.Column(
            "max_grade",
            sa.FLOAT(),
            nullable=True,
            server_default=sa.text("100"),
        ),
        sa.Column(
            "source",
            sa.VARCHAR(50),
            nullable=True,
            server_default=sa.text("'parsed'"),
        ),
        sa.Column("graded_at", sa.TIMESTAMPTZ(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_grades_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["deadline_id"],
            ["deadlines.id"],
            name="fk_grades_deadline_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name="fk_grades_course_id",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "source IN ('parsed', 'manual', 'gio')",
            name="ck_grades_source",
        ),
    )

    # --- study_blocks ---
    op.create_table(
        "study_blocks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deadline_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_time", sa.TIMESTAMPTZ(), nullable=False),
        sa.Column("end_time", sa.TIMESTAMPTZ(), nullable=False),
        sa.Column(
            "status",
            sa.VARCHAR(20),
            nullable=True,
            server_default=sa.text("'scheduled'"),
        ),
        sa.Column("gcal_event_id", sa.VARCHAR(255), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_study_blocks_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["deadline_id"],
            ["deadlines.id"],
            name="fk_study_blocks_deadline_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled')",
            name="ck_study_blocks_status",
        ),
    )

    # --- effort_records ---
    op.create_table(
        "effort_records",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("course_code", sa.VARCHAR(50), nullable=False),
        sa.Column("assignment_label", sa.VARCHAR(255), nullable=False),
        sa.Column("hours_spent", sa.FLOAT(), nullable=False),
        sa.Column(
            "input_method",
            sa.VARCHAR(20),
            nullable=True,
            server_default=sa.text("'button_bucket'"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "input_method IN ('button_bucket', 'typed')",
            name="ck_effort_records_input_method",
        ),
    )

    # --- effort_aggregates ---
    op.create_table(
        "effort_aggregates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("course_code", sa.VARCHAR(50), nullable=False),
        sa.Column("assignment_label", sa.VARCHAR(255), nullable=False),
        sa.Column("mean_hours", sa.FLOAT(), nullable=False),
        sa.Column("p25_hours", sa.FLOAT(), nullable=False),
        sa.Column("p75_hours", sa.FLOAT(), nullable=False),
        sa.Column("sample_count", sa.INTEGER(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "course_code",
            "assignment_label",
            name="uq_effort_aggregates_course_assignment",
        ),
    )

    # --- reminder_state ---
    op.create_table(
        "reminder_state",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deadline_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_sent_at", sa.TIMESTAMPTZ(), nullable=True),
        sa.Column(
            "consecutive_snoozes",
            sa.INTEGER(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("silenced_until", sa.TIMESTAMPTZ(), nullable=True),
        sa.Column(
            "nudge_count",
            sa.INTEGER(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_reminder_state_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["deadline_id"],
            ["deadlines.id"],
            name="fk_reminder_state_deadline_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "user_id",
            "deadline_id",
            name="uq_reminder_state_user_deadline",
        ),
    )

    # --- manual_update_log ---
    op.create_table(
        "manual_update_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deadline_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("field_changed", sa.VARCHAR(100), nullable=True),
        sa.Column("old_value", sa.TEXT(), nullable=True),
        sa.Column("new_value", sa.TEXT(), nullable=True),
        sa.Column(
            "changed_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "source",
            sa.VARCHAR(50),
            nullable=True,
            server_default=sa.text("'gio'"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_manual_update_log_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["deadline_id"],
            ["deadlines.id"],
            name="fk_manual_update_log_deadline_id",
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "source IN ('gio', 'user_direct')",
            name="ck_manual_update_log_source",
        ),
    )

    # --- conversation_history ---
    op.create_table(
        "conversation_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.VARCHAR(20), nullable=False),
        sa.Column("content", sa.TEXT(), nullable=False),
        sa.Column("template_id", sa.VARCHAR(100), nullable=True),
        sa.Column("button_value", sa.VARCHAR(100), nullable=True),
        sa.Column("input_method", sa.VARCHAR(20), nullable=True),
        sa.Column(
            "context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_conversation_history_user_id",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant')",
            name="ck_conversation_history_role",
        ),
        sa.CheckConstraint(
            "input_method IN ('button', 'typed', 'unknown')",
            name="ck_conversation_history_input_method",
        ),
    )
    op.create_index(
        "ix_conversation_history_user_id", "conversation_history", ["user_id"]
    )

    # --- pdf_parse_cache ---
    op.create_table(
        "pdf_parse_cache",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("pdf_hash", sa.VARCHAR(64), nullable=False),
        sa.Column(
            "parse_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "parsed_at",
            sa.TIMESTAMPTZ(),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "hit_count",
            sa.INTEGER(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("pdf_hash", name="uq_pdf_parse_cache_pdf_hash"),
    )
    op.create_index(
        "ix_pdf_parse_cache_pdf_hash", "pdf_parse_cache", ["pdf_hash"], unique=True
    )


def downgrade() -> None:
    op.drop_table("pdf_parse_cache")
    op.drop_table("conversation_history")
    op.drop_table("manual_update_log")
    op.drop_table("reminder_state")
    op.drop_table("effort_aggregates")
    op.drop_table("effort_records")
    op.drop_table("study_blocks")
    op.drop_table("grades")
    op.drop_constraint(
        "fk_pdf_attachments_uploaded_document_id", "pdf_attachments", type_="foreignkey"
    )
    op.drop_table("uploaded_documents")
    op.drop_table("pdf_attachments")
    op.drop_table("parsed_emails")
    op.drop_table("exam_sittings")
    op.drop_table("deadlines")
    op.drop_table("courses")
    op.drop_table("users")
