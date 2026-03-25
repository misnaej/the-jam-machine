"""Tests for the music generation engine."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jammy.generating.config import TrackConfig
from jammy.generating.file_io import define_generation_dir, write_text_midi_to_file
from jammy.generating.generate import GenerateMidiText
from jammy.generating.validation import check_if_prompt_inst_in_tokenizer_vocab
from jammy.tokens import PIECE_START, TRACK_END

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
    generate_midi = GenerateMidiText(model, tokenizer)

    # Configure and generate
    generate_midi.set_n_bars_generated(n_bars=N_BAR_GENERATED)
    tracks = [
        TrackConfig(instrument=inst, density=dens, temperature=temperature)
        for inst, dens in zip(instrument_prompt_list, density_list, strict=True)
    ]
    generate_midi.generate_piece(tracks)
    generated_piece = generate_midi.get_piece_text()

    # Write output
    filename = write_text_midi_to_file(
        generated_piece,
        generate_midi.piece.piece_by_track,
        test_dir,
    )

    # Assertions
    assert generated_piece is not None
    assert PIECE_START in generated_piece
    assert TRACK_END in generated_piece
    assert Path(filename).exists()


class TestGenerateSetters:
    """Tests for GenerateMidiText configuration setters.

    These test the simple setter methods that don't require generation.
    """

    def test_set_n_bars_generated(
        self, model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast
    ) -> None:
        """Test that set_n_bars_generated updates config and prompts."""
        gen = GenerateMidiText(model, tokenizer)
        gen.set_n_bars_generated(4)
        assert gen.config.n_bars == 4
        assert gen.prompts.n_bars == 4

    def test_set_force_sequence_length(
        self, model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast
    ) -> None:
        """Test that set_force_sequence_length updates config."""
        gen = GenerateMidiText(model, tokenizer)
        gen.set_force_sequence_length(False)
        assert gen.config.force_sequence_length is False

    def test_set_improvisation_level(
        self, model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast
    ) -> None:
        """Test that set_improvisation_level updates config and engine."""
        gen = GenerateMidiText(model, tokenizer)
        gen.set_improvisation_level(3)
        assert gen.config.improvisation_level == 3

    def test_reset_temperature(self, model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast) -> None:
        """Test that reset_temperature updates the track temperature."""
        gen = GenerateMidiText(model, tokenizer)
        gen.piece.init_track("DRUMS", 3, 0.7)
        gen.reset_temperature(0, 0.3)
        assert gen.piece.get_track_temperature(0) == 0.3

    def test_delete_track(self, model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast) -> None:
        """Test that delete_track removes from piece state."""
        gen = GenerateMidiText(model, tokenizer)
        gen.piece.init_track("DRUMS", 3, 0.7)
        gen.piece.init_track("4", 2, 0.5)
        gen.delete_track(0)
        assert gen.piece.get_track_count() == 1
        assert gen.piece.get_track(0)["instrument"] == "4"
