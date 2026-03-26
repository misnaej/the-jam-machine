"""Tests for the model loading module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from jammy.load import load_model_and_tokenizer

if TYPE_CHECKING:
    from pathlib import Path


def test_load_model_and_tokenizer_invalid_local_path_raises() -> None:
    """Test that a non-existent local path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_model_and_tokenizer("/nonexistent/path", from_huggingface=False)


def test_load_model_and_tokenizer_missing_tokenizer_raises(tmp_path: Path) -> None:
    """Test that a local path without tokenizer.json raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match=r"tokenizer\.json"):
        load_model_and_tokenizer(str(tmp_path), from_huggingface=False)
