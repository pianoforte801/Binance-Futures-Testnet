"""
Centralized logging configuration.

All API requests, responses, and errors are logged to a rotating log file
(bot.log) as well as to the console (console only shows INFO and above,
the file captures DEBUG and above for full traceability).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "bot.log")


def setup_logging(log_level: str = "DEBUG") -> logging.Logger:
    """
    Configure and return the root application logger.

    Creates a `logs/` directory (if missing) and attaches:
      - a rotating file handler (5 MB per file, 3 backups) -> logs/bot.log
      - a console handler (INFO and above) for immediate feedback

    Args:
        log_level: minimum level captured by the file handler.

    Returns:
        Configured logger instance named "trading_bot".
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))

    # Avoid duplicate handlers if setup_logging() is called more than once
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
