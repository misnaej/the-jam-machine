"""Tests for the text to MIDI decoder."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from jammy.embedding.decoder import TextDecoder
from jammy.generating.playback import get_music
from jammy.generating.utils import plot_piano_roll
from jammy.utils import read_from_file
from test.conftest import USE_FAMILIZED_MODEL

if TYPE_CHECKING:
    from pathlib import Path

    from miditok import MIDILike


def test_decode_midi_text(miditok: MIDILike, fixtures_dir: Path, tmp_path: Path) -> None:
    """Test decoding a generated MIDI text file back to MIDI format.

    Verifies that:
    - The decoder successfully creates a MIDI file from text
    - The resulting MIDI file exists on disk

    Args:
        miditok: The MIDILike tokenizer fixture.
        fixtures_dir: Path to the test fixtures directory.
        tmp_path: Temporary directory for test outputs.
    """
    fixture_file = fixtures_dir / "sample_midi_text.json"
    if not fixture_file.exists():
        pytest.skip(f"Missing test fixture file: {fixture_file}")

    generated_piece = read_from_file(str(fixture_file), is_json=True)["generated_midi"]

    output_midi = tmp_path / "decoded_test.mid"
    TextDecoder(miditok, USE_FAMILIZED_MODEL).get_midi(generated_piece, filename=str(output_midi))

    assert output_midi.exists()

    # Verify the MIDI can be loaded and visualized
    inst_midi, _ = get_music(str(output_midi))
    piano_roll_fig = plot_piano_roll(inst_midi)

    output_png = tmp_path / "decoded_test_piano_roll.png"
    piano_roll_fig.savefig(str(output_png), bbox_inches="tight")
    piano_roll_fig.clear()

    assert output_png.exists()
