"""Logging utilities."""
import logging

import rich.logging

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[rich.logging.RichHandler()],
)
logger = logging.getLogger(__name__)
