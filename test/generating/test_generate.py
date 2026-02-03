"""Tests for the music generation engine."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jammy.generating.config import TrackConfig
from jammy.generating.generate import GenerateMidiText
from jammy.generating.utils import (
    WriteTextMidiToFile,
    check_if_prompt_inst_in_tokenizer_vocab,
    define_generation_dir,
)

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast


# Generation parameters
N_BAR_GENERATED = 8


def test_generate_midi_text(
    model: GPT2LMHeadModel,
    tokenizer: GPT2TokenizerFast,
    tmp_path: Path,
) -> None:
    """Test generating a MIDI text sequence.

    Verifies that:
    - Generation produces non-empty output
    - Output contains expected structural tokens (PIECE_START, TRACK_END)
    - Output is successfully written to a JSON file

    Args:
        model: The GPT-2 model fixture.
        tokenizer: The GPT-2 tokenizer fixture.
        tmp_path: Temporary directory for test outputs.
    """
    # Generation parameters
    temperature = 0.7
    # DRUMS = drums, 0 = piano, 1 = chromatic percussion, 2 = organ, 3 = guitar,
    # 4 = bass, 5 = strings, 6 = ensemble, 7 = brass, 8 = reed, 9 = pipe,
    # 10 = synth lead, 11 = synth pad, 12 = synth effects, 13 = ethnic,
    # 14 = percussive, 15 = sound effects
    instrument_prompt_list = ["DRUMS", "4", "3"]
    density_list = [3, 2, 3]

    # Verify prompt makes sense
    check_if_prompt_inst_in_tokenizer_vocab(tokenizer, instrument_prompt_list)

    # Set up output directory
    test_dir = define_generation_dir(str(tmp_path / "results"))

    # Instantiate generator
    piece_by_track: list[str] = []
    generate_midi = GenerateMidiText(model, tokenizer, piece_by_track)

    # Configure and generate
    generate_midi.set_nb_bars_generated(n_bars=N_BAR_GENERATED)
    tracks = [
        TrackConfig(instrument=inst, density=dens, temperature=temperature)
        for inst, dens in zip(instrument_prompt_list, density_list, strict=True)
    ]
    generate_midi.generate_piece(tracks)
    generate_midi.generated_piece = generate_midi.get_whole_piece_from_bar_dict()

    # Write output
    filename = WriteTextMidiToFile(
        generate_midi,
        test_dir,
    ).text_midi_to_file()

    # Assertions
    assert generate_midi.generated_piece is not None
    assert "PIECE_START" in generate_midi.generated_piece
    assert "TRACK_END" in generate_midi.generated_piece
    assert Path(filename).exists()
