"""Tests for the text_parsing module."""

from __future__ import annotations

from jammy.embedding.text_parsing import _is_beyond_quantization
from jammy.tokens import NOTE_ON, TIME_DELTA


class TestIsBeyondQuantization:
    """Tests for _is_beyond_quantization."""

    def test_is_beyond_quantization_within_limit(self) -> None:
        """Test that events within the limit are not flagged."""
        beyond, cumul = _is_beyond_quantization(TIME_DELTA, "2", 0, 16)
        assert beyond is False
        assert cumul == 2

    def test_is_beyond_quantization_exceeds_limit(self) -> None:
        """Test that TIME_DELTA exceeding limit is flagged."""
        beyond, cumul = _is_beyond_quantization(TIME_DELTA, "4", 14, 16)
        assert beyond is True
        assert cumul == 14  # reverted, not accumulated

    def test_is_beyond_quantization_note_on_at_limit(self) -> None:
        """Test that NOTE_ON at max cumul is flagged."""
        beyond, cumul = _is_beyond_quantization(NOTE_ON, "60", 16, 16)
        assert beyond is True
        assert cumul == 16

    def test_is_beyond_quantization_note_on_below_limit(self) -> None:
        """Test that NOTE_ON below limit is not flagged."""
        beyond, cumul = _is_beyond_quantization(NOTE_ON, "60", 8, 16)
        assert beyond is False
        assert cumul == 8

    def test_is_beyond_quantization_other_event_type(self) -> None:
        """Test that non-TIME_DELTA/NOTE_ON events are never flagged."""
        beyond, cumul = _is_beyond_quantization("BAR_START", None, 16, 16)
        assert beyond is False
        assert cumul == 16

    def test_is_beyond_quantization_none_value_safe(self) -> None:
        """Test that TIME_DELTA with None value doesn't crash."""
        beyond, cumul = _is_beyond_quantization(TIME_DELTA, None, 0, 16)
        assert beyond is False
        assert cumul == 0
