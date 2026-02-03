"""Tests for the MIDI to text encoder."""

from __future__ import annotations

from jammy.embedding.encoder import from_midi_to_sectioned_text
from jammy.utils import write_to_file
from test.conftest import USE_FAMILIZED_MODEL


def test_encode_midi_file() -> None:
    """Test encoding a MIDI file to text representation.

    Verifies that:
    - The encoding produces non-empty output
    - The output contains expected structural tokens (PIECE_START, TRACK_START)
    """
    midi_filename = "midi/the_strokes-reptilia"

    piece_text = from_midi_to_sectioned_text(midi_filename, familized=USE_FAMILIZED_MODEL)
    write_to_file(f"{midi_filename}_from_midi.txt", piece_text)

    assert piece_text is not None
    assert "PIECE_START" in piece_text
    assert "TRACK_START" in piece_text
