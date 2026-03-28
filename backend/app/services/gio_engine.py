"""Backwards-compatibility shim — all logic lives in app.services.gio.*"""
from app.services.gio.constants import EFFORT_BUCKETS, KNOWN_BUTTON_VALUES, SNOOZE_CONFIGS
from app.services.gio.engine import handle_response
from app.services.gio.llm import anthropic_client
from app.services.gio.llm_handler import llm_handler
from app.services.gio.template_handler import template_handler

__all__ = [
    "EFFORT_BUCKETS",
    "KNOWN_BUTTON_VALUES",
    "SNOOZE_CONFIGS",
    "anthropic_client",
    "handle_response",
    "llm_handler",
    "template_handler",
]
