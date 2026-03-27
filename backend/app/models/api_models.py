"""Shared Pydantic schemas for API request/response."""
from pydantic import BaseModel, EmailStr
from typing import Optional, Any
import uuid
from datetime import datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str


class VerifyRequest(BaseModel):
    email: EmailStr
    code: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GioButton(BaseModel):
    label: str
    value: str


class GioMessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    buttons: Optional[list[GioButton]] = None
    navigate_hint: Optional[str] = None
    template_id: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AttachmentRef(BaseModel):
    type: str  # "deadline" | "grade" | "course" | "pdf"
    id: uuid.UUID


class ChatRespondRequest(BaseModel):
    message_id: Optional[uuid.UUID] = None
    button_value: Optional[str] = None
    button_label: Optional[str] = None
    text: Optional[str] = None
    attachments: list[AttachmentRef] = []


class DeadlineOut(BaseModel):
    id: uuid.UUID
    course_name: str
    course_code: Optional[str]
    type: str
    title: str
    due_date: datetime
    status: str
    needs_review: bool
    estimated_hours: Optional[float] = None

    class Config:
        from_attributes = True


class GradeOut(BaseModel):
    id: uuid.UUID
    course_name: str
    assignment_title: Optional[str]
    grade: float
    max_grade: float
    grade_type: str
    source: str
    received_at: datetime

    class Config:
        from_attributes = True


class ParsedEmailOut(BaseModel):
    id: uuid.UUID
    subject: Optional[str]
    sender: Optional[str]
    received_at: datetime
    parse_status: str
    attachment_count: int
    forwarded_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserPreferencesIn(BaseModel):
    forward_emails: Optional[bool] = None
    lecture_mode: Optional[str] = None
    assignment_first_reminder_days: Optional[int] = None
    exam_first_reminder_days: Optional[int] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    shabbat_blackout: Optional[bool] = None
    grade_alert_threshold: Optional[float] = None
    min_study_session_minutes: Optional[int] = None
    preferred_study_windows: Optional[list[str]] = None
    effort_contribution_opt_out: Optional[bool] = None
