"""Logging infrastructure."""
import logging
from typing import Final

LOG_FORMAT: Final[str] = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

logging.basicConfig(format=LOG_FORMAT)


def tagged_logger(tag: str) -> logging.Logger:
    """Return a logger identified by the given UPPER_CASE tag."""
    return logging.getLogger(tag)
