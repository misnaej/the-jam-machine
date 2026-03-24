"""Tests for the MIDI to text encoder."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jammy.embedding.encoder import from_midi_to_sectioned_text
from jammy.tokens import PIECE_START, TRACK_START
from test.conftest import USE_FAMILIZED_MODEL

if TYPE_CHECKING:
    from pathlib import Path


def test_encode_midi_file(tmp_path: Path) -> None:
    """Test encoding a MIDI file to text representation.

    Verifies that:
    - The encoding produces non-empty output
    - The output contains expected structural tokens (PIECE_START, TRACK_START)
    """
    midi_filename = "midi/the_strokes-reptilia"

    piece_text = from_midi_to_sectioned_text(midi_filename, familized=USE_FAMILIZED_MODEL)

    assert piece_text is not None
    assert PIECE_START in piece_text
    assert TRACK_START in piece_text

    # Write output to tmp_path (not the repo root)
    output_file = tmp_path / "the_strokes-reptilia_from_midi.txt"
    output_file.write_text(piece_text)
