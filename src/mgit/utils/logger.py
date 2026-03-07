"""Logging utilities."""
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
