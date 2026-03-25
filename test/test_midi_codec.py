"""Tests for the midi_codec module."""

from __future__ import annotations

from jammy.midi_codec import (
    get_beat_resolution,
    get_event,
    get_text,
    int_dec_base_to_beat,
    int_dec_base_to_delta,
    split_dots,
    time_delta_to_beat,
    time_delta_to_int_dec_base,
)
from jammy.tokens import BAR_END, INST, NOTE_ON, PIECE_START, TIME_DELTA


class TestGetEvent:
    """Tests for get_event."""

    def test_get_event_time_delta_zero_returns_none(self) -> None:
        """Test that TIME_DELTA=0 is skipped (returns None)."""
        result = get_event(TIME_DELTA, "0")
        assert result is None

    def test_get_event_piece_start(self) -> None:
        """Test converting PIECE_START token to event."""
        event = get_event(PIECE_START)
        assert event is not None
        assert event.type == "Piece-Start"

    def test_get_event_note_on(self) -> None:
        """Test converting NOTE_ON token to event."""
        event = get_event(NOTE_ON, "60")
        assert event is not None
        assert event.type == "Note-On"
        assert event.value == "60"

    def test_get_event_inst_drums(self) -> None:
        """Test that INST=DRUMS maps value to 'Drums'."""
        event = get_event(INST, "DRUMS")
        assert event is not None
        assert event.value == "Drums"

    def test_get_event_unknown_returns_none(self) -> None:
        """Test that an unknown token returns None."""
        assert get_event("UNKNOWN_TOKEN") is None


class TestGetText:
    """Tests for get_text."""

    def test_get_text_piece_start(self) -> None:
        """Test encoding Piece-Start event to text."""
        from miditok import Event

        event = Event("Piece-Start", None)
        assert get_text(event) == f"{PIECE_START} "

    def test_get_text_bar_end(self) -> None:
        """Test encoding Bar-End event to text."""
        from miditok import Event

        event = Event("Bar-End", None)
        assert get_text(event) == f"{BAR_END} "

    def test_get_text_unknown_returns_empty(self) -> None:
        """Test that an unknown event type returns empty string."""
        from miditok import Event

        event = Event("Unknown-Type", None)
        assert get_text(event) == ""


class TestSplitDots:
    """Tests for split_dots."""

    def test_split_dots_three_parts(self) -> None:
        """Test splitting a standard 'integer.decimal.base' string."""
        assert split_dots("0.4.8") == [0, 4, 8]

    def test_split_dots_zeros(self) -> None:
        """Test splitting all zeros."""
        assert split_dots("0.0.8") == [0, 0, 8]


class TestIntDecBaseToBeat:
    """Tests for int_dec_base_to_beat."""

    def test_int_dec_base_to_beat_half_beat(self) -> None:
        """Test that 0.4.8 equals 0.5 beats."""
        assert int_dec_base_to_beat("0.4.8") == 0.5

    def test_int_dec_base_to_beat_zero(self) -> None:
        """Test that 0.0.8 equals 0.0 beats."""
        assert int_dec_base_to_beat("0.0.8") == 0.0

    def test_int_dec_base_to_beat_one_beat(self) -> None:
        """Test that 1.0.8 equals 1.0 beats."""
        assert int_dec_base_to_beat("1.0.8") == 1.0


class TestGetBeatResolution:
    """Tests for get_beat_resolution."""

    def test_get_beat_resolution_drums(self) -> None:
        """Test that drums returns DRUMS_BEAT_QUANTIZATION."""
        assert get_beat_resolution("drums") == 4

    def test_get_beat_resolution_drums_case_insensitive(self) -> None:
        """Test that matching is case-insensitive."""
        assert get_beat_resolution("Drums") == 4
        assert get_beat_resolution("DRUMS") == 4

    def test_get_beat_resolution_other_instrument(self) -> None:
        """Test that non-drums returns NONE_DRUMS_BEAT_QUANTIZATION."""
        assert get_beat_resolution("piano") == 4


class TestTimeDeltaToBeat:
    """Tests for time_delta_to_beat."""

    def test_time_delta_to_beat_one_step(self) -> None:
        """Test converting 1 time delta to beats."""
        assert time_delta_to_beat(1, "drums") == 0.25

    def test_time_delta_to_beat_four_steps(self) -> None:
        """Test converting 4 time deltas (one full beat)."""
        assert time_delta_to_beat(4, "drums") == 1.0


class TestTimeDeltaToIntDecBase:
    """Tests for time_delta_to_int_dec_base."""

    def test_time_delta_to_int_dec_base_roundtrip(self) -> None:
        """Test that encoding then decoding produces consistent values."""
        result = time_delta_to_int_dec_base(4, "drums")
        beat = int_dec_base_to_beat(result)
        assert beat == 1.0


class TestIntDecBaseToDelta:
    """Tests for int_dec_base_to_delta."""

    def test_int_dec_base_to_delta_half_beat(self) -> None:
        """Test that 0.4.8 converts to 2 delta steps."""
        assert int_dec_base_to_delta("0.4.8") == 2

    def test_int_dec_base_to_delta_zero(self) -> None:
        """Test that 0.0.8 converts to 0 delta."""
        assert int_dec_base_to_delta("0.0.8") == 0
