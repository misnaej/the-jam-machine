"""Tests for the logging_config module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jammy.logging_config import get_logger, setup_logging

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupLogging:
    """Tests for setup_logging."""

    def test_setup_logging_file_output(self, tmp_path: Path) -> None:
        """Test that file logging creates a log file."""
        log_file = setup_logging(output_dir=tmp_path, log_to_console=False)
        assert log_file is not None
        assert log_file.exists()
        assert log_file.suffix == ".log"

    def test_setup_logging_console_only(self, tmp_path: Path) -> None:
        """Test that console-only logging returns None."""
        result = setup_logging(output_dir=tmp_path, log_to_file=False)
        assert result is None

    def test_setup_logging_creates_log_dir(self, tmp_path: Path) -> None:
        """Test that the log directory is created automatically."""
        log_dir = tmp_path / "custom_output"
        setup_logging(output_dir=log_dir, log_to_file=False)
        assert (log_dir / "logs").is_dir()


class TestGetLogger:
    """Tests for get_logger."""

    def test_get_logger_returns_named_logger(self) -> None:
        """Test that get_logger returns a logger with the given name."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"
