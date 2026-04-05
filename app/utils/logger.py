"""
Centralized logger setup. Writes to console and optionally to a log file.
"""

import logging
import os
from pathlib import Path


def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    Returns a configured logger.

    Args:
        name: Logger name (usually __name__).
        log_file: Optional path to a .txt log file. Falls back to LOG_PATH env var.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    target = log_file or os.getenv("LOG_PATH")
    if target:
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(target, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
