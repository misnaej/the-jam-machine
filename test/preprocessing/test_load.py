"""Tests for the model loading module."""

from __future__ import annotations

import pytest

from jammy.preprocessing.load import LoadModel


class TestLoadModelInit:
    """Tests for LoadModel.__init__ error handling."""

    def test_load_model_invalid_local_path_raises(self) -> None:
        """Test that a non-existent local path raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="does not exist"):
            LoadModel("/nonexistent/path", from_huggingface=False)

    def test_load_model_huggingface_skips_path_check(self) -> None:
        """Test that from_huggingface=True doesn't check local path."""
        # Should not raise even though path doesn't exist locally
        loader = LoadModel("some/repo", from_huggingface=True)
        assert loader.path == "some/repo"

    def test_load_model_stores_revision(self) -> None:
        """Test that revision is stored correctly."""
        loader = LoadModel("some/repo", revision="abc123")
        assert loader.revision == "abc123"

    def test_load_model_default_revision_none(self) -> None:
        """Test that default revision is None."""
        loader = LoadModel("some/repo")
        assert loader.revision is None
