"""Tests for the music generation engine."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from jammy.generating.config import TrackConfig
from jammy.generating.file_io import define_generation_dir, write_text_midi_to_file
from jammy.generating.generate import GenerateMidiText
from jammy.tokens import PIECE_START, TRACK_END

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast


# Matches the model's training configuration
N_BAR_GENERATED = 8


@pytest.mark.slow
def test_generate_midi_text(
    model: GPT2LMHeadModel,
    tokenizer: GPT2TokenizerFast,
    tmp_path: Path,
) -> None:
    """Test generating a full MIDI piece end-to-end.

    This is an integration test that loads the real model and generates
    actual output. Marked slow (~10s) due to model inference.

    Args:
        model: Session-scoped GPT-2 model from HuggingFace.
        tokenizer: Session-scoped GPT-2 tokenizer from HuggingFace.
        tmp_path: Temporary directory for test outputs.
    """
    tracks = [
        TrackConfig(instrument="DRUMS", density=3, temperature=0.7),
        TrackConfig(instrument="4", density=2, temperature=0.7),
        TrackConfig(instrument="3", density=3, temperature=0.7),
    ]

    generator = GenerateMidiText(model, tokenizer)
    generator.set_n_bars_generated(n_bars=N_BAR_GENERATED)
    generator.generate_piece(tracks)
    generated_piece = generator.get_piece_text()

    assert generated_piece is not None
    assert PIECE_START in generated_piece
    assert TRACK_END in generated_piece

    # Verify output can be written to disk
    test_dir = define_generation_dir(str(tmp_path / "results"))
    filename = write_text_midi_to_file(generated_piece, generator.piece.piece_by_track, test_dir)
    assert Path(filename).exists()


def test_set_n_bars_generated(model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast) -> None:
    """Test that set_n_bars_generated propagates to config and prompts."""
    gen = GenerateMidiText(model, tokenizer)
    gen.set_n_bars_generated(4)
    assert gen.config.n_bars == 4
    assert gen.prompts.n_bars == 4


def test_set_force_sequence_length(model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast) -> None:
    """Test that set_force_sequence_length updates config."""
    gen = GenerateMidiText(model, tokenizer)
    gen.set_force_sequence_length(False)
    assert gen.config.force_sequence_length is False


def test_set_improvisation_level(model: GPT2LMHeadModel, tokenizer: GPT2TokenizerFast) -> None:
    """Test that set_improvisation_level updates config and engine."""
    gen = GenerateMidiText(model, tokenizer)
    gen.set_improvisation_level(3)
    assert gen.config.improvisation_level == 3
