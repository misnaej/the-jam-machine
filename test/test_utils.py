"""Tests for the utils module."""

from __future__ import annotations

import re

import pytest

from jammy.utils import compute_list_average, get_datetime, get_miditok, index_has_substring


class TestIndexHasSubstring:
    """Tests for index_has_substring."""

    def test_index_has_substring_found(self) -> None:
        """Test finding a substring in the list."""
        items = ["hello", "world", "foo_bar"]
        assert index_has_substring(items, "world") == 1

    def test_index_has_substring_not_found(self) -> None:
        """Test returning -1 when substring is absent."""
        items = ["hello", "world"]
        assert index_has_substring(items, "missing") == -1

    def test_index_has_substring_partial_match(self) -> None:
        """Test matching a partial substring."""
        items = ["NOTE_ON=60", "TIME_DELTA=4", "BAR_END"]
        assert index_has_substring(items, "DELTA") == 1

    def test_index_has_substring_empty_list(self) -> None:
        """Test returning -1 for an empty list."""
        assert index_has_substring([], "anything") == -1

    def test_index_has_substring_returns_first(self) -> None:
        """Test that the first matching index is returned."""
        items = ["abc", "abc_2", "abc_3"]
        assert index_has_substring(items, "abc") == 0


class TestComputeListAverage:
    """Tests for compute_list_average."""

    def test_compute_list_average_simple(self) -> None:
        """Test average of simple values."""
        assert compute_list_average([1.0, 2.0, 3.0]) == 2.0

    def test_compute_list_average_single(self) -> None:
        """Test average of a single value."""
        assert compute_list_average([5.0]) == 5.0

    def test_compute_list_average_integers(self) -> None:
        """Test average with integer inputs."""
        assert compute_list_average([10, 20]) == 15.0

    def test_compute_list_average_empty_raises(self) -> None:
        """Test that empty input raises ZeroDivisionError."""
        with pytest.raises(ZeroDivisionError):
            compute_list_average([])


class TestGetDatetime:
    """Tests for get_datetime."""

    def test_get_datetime_format(self) -> None:
        """Test that datetime string matches YYYYMMDD_HHMMSS format."""
        result = get_datetime()
        assert re.match(r"\d{8}_\d{6}", result)


class TestGetMiditok:
    """Tests for get_miditok."""

    def test_get_miditok_returns_tokenizer(self) -> None:
        """Test that get_miditok returns a MIDILike instance."""
        tok = get_miditok()
        assert tok is not None

    def test_get_miditok_is_singleton(self) -> None:
        """Test that repeated calls return the same cached instance."""
        tok1 = get_miditok()
        tok2 = get_miditok()
        assert tok1 is tok2
