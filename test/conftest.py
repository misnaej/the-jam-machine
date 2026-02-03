"""Shared pytest fixtures for the test suite.

This module provides session-scoped fixtures for expensive operations like
loading the HuggingFace model and tokenizer. Use these fixtures instead of
creating new instances in each test to improve test performance.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from jammy.preprocessing.load import LoadModel
from jammy.utils import get_miditok

if TYPE_CHECKING:
    from miditok import MIDILike
    from transformers import GPT2LMHeadModel, GPT2TokenizerFast


# Default model configuration
MODEL_REPO = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
USE_FAMILIZED_MODEL = True


@pytest.fixture(scope="session")
def model_and_tokenizer() -> tuple[GPT2LMHeadModel, GPT2TokenizerFast]:
    """Load the GPT-2 model and tokenizer once per test session.

    This is a session-scoped fixture to avoid reloading the model for each test,
    which is expensive.

    Returns:
        Tuple of (model, tokenizer) from HuggingFace.
    """
    loader = LoadModel(MODEL_REPO, from_huggingface=True)
    return loader.load_model_and_tokenizer()


@pytest.fixture(scope="session")
def model(model_and_tokenizer: tuple[GPT2LMHeadModel, GPT2TokenizerFast]) -> GPT2LMHeadModel:
    """Get just the model from the loaded model/tokenizer pair.

    Args:
        model_and_tokenizer: The session-scoped model and tokenizer fixture.

    Returns:
        The GPT-2 model.
    """
    return model_and_tokenizer[0]


@pytest.fixture(scope="session")
def tokenizer(model_and_tokenizer: tuple[GPT2LMHeadModel, GPT2TokenizerFast]) -> GPT2TokenizerFast:
    """Get just the tokenizer from the loaded model/tokenizer pair.

    Args:
        model_and_tokenizer: The session-scoped model and tokenizer fixture.

    Returns:
        The GPT-2 tokenizer.
    """
    return model_and_tokenizer[1]


@pytest.fixture(scope="session")
def miditok() -> MIDILike:
    """Get the MIDILike tokenizer for encoding/decoding.

    Returns:
        The MIDILike tokenizer instance.
    """
    return get_miditok()


@pytest.fixture
def sample_piece_text() -> str:
    """Provide a sample MIDI text piece for unit tests.

    This is a minimal valid piece with guitar, drums, and bass tracks.

    Returns:
        A sample MIDI text string.
    """
    return (
        "PIECE_START TRACK_START INST=3 DENSITY=1 "
        "BAR_START NOTE_ON=64 TIME_DELTA=16 NOTE_OFF=64 BAR_END "
        "TRACK_END TRACK_START INST=DRUMS DENSITY=2 "
        "BAR_START NOTE_ON=36 TIME_DELTA=4 NOTE_OFF=36 BAR_END "
        "TRACK_END TRACK_START INST=4 DENSITY=3 "
        "BAR_START NOTE_ON=40 TIME_DELTA=4 NOTE_OFF=40 BAR_END "
        "TRACK_END"
    )


@pytest.fixture
def test_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test outputs.

    Args:
        tmp_path: pytest's built-in temp directory fixture.

    Returns:
        Path to a temporary directory for test file outputs.
    """
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def fixtures_dir() -> Path:
    """Get the path to the test fixtures directory.

    Returns:
        Path to test/fixtures directory.
    """
    return Path(__file__).parent / "fixtures"
