"""Logging infrastructure."""
import logging
from typing import Final

LOG_FORMAT: Final[str] = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

# Keep noisy libraries at WARNING so they don't drown out app logs
for _noisy in ("sqlalchemy", "httpx", "httpcore", "anthropic", "urllib3", "boto3", "botocore"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)


def tagged_logger(tag: str) -> logging.Logger:
    """Return a logger identified by the given UPPER_CASE tag."""
    return logging.getLogger(tag)
