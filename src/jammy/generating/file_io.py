"""File I/O utilities for MIDI generation output."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jammy.utils import get_datetime, writeToFile

logger = logging.getLogger(__name__)


def write_text_midi_to_file(
    generated_midi: str,
    piece_by_track: list[dict[str, Any]],
    output_path: str,
) -> str:
    """Save generated MIDI text and hyperparameters to a JSON file.

    Args:
        generated_midi: The generated MIDI text sequence.
        piece_by_track: Track hyperparameters and bar data.
        output_path: Directory path to save the file.

    Returns:
        Path to the saved JSON file.
    """
    filename = str(Path(output_path) / f"{get_datetime()}.json")
    output_dict = {
        "generated_midi": generated_midi,
        "hyperparameters_and_bars": piece_by_track,
    }
    logger.info("Generated MIDI text written to: %s", filename)
    writeToFile(filename, output_dict)
    return filename


def define_generation_dir(generation_dir: str) -> str:
    """Create generation directory if it doesn't exist.

    Args:
        generation_dir: Path to the generation directory.

    Returns:
        The same directory path.
    """
    Path(generation_dir).mkdir(parents=True, exist_ok=True)
    return generation_dir
