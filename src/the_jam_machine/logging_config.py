"""Logging configuration for The Jam Machine."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logging(
    output_dir: str | Path | None = None,
    level: int = logging.INFO,
    log_to_console: bool = True,
    log_to_file: bool = True,
) -> Path | None:
    """Configure logging for the application.

    Sets up logging to both console and file. The log file is created
    in the specified output directory with a timestamp.

    Args:
        output_dir: Directory for log files. If None, uses './output/logs'.
        level: Logging level (default: INFO).
        log_to_console: Whether to log to console.
        log_to_file: Whether to log to file.

    Returns:
        Path to the log file if file logging is enabled, else None.
    """
    # Determine output directory
    log_dir = Path("./output/logs") if output_dir is None else Path(output_dir) / "logs"

    # Create output directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"jam_machine_{timestamp}.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log initial message
    logging.info("Logging initialized - output: %s", log_file if log_to_file else "console only")

    return log_file if log_to_file else None


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
