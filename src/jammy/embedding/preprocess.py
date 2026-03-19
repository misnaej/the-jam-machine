"""Encode MIDI files in a directory to text token representation."""

from __future__ import annotations

import logging
from pathlib import Path

from miditoolkit import MidiFile

from jammy.embedding.encoder import MIDIEncoder
from jammy.file_utils import write_to_file
from jammy.utils import get_miditok

logger = logging.getLogger(__name__)


def main() -> None:
    """Encode all MIDI files in the midi/ directory to text files."""
    tokenizer = get_miditok()
    encoder = MIDIEncoder(tokenizer)

    midi_files = [f"midi/{f.name}" for f in Path("midi/").iterdir() if f.suffix == ".mid"]

    for file in midi_files:
        try:
            midi = MidiFile(file)
        except (OSError, ValueError, KeyError):
            logger.warning("Failed to load %s", file)
            continue

        piece_text = encoder.get_piece_text(midi)

        file_path = Path(file)
        midi_filename = file_path.stem
        dirname = file_path.parent
        write_to_file(f"{dirname}/encoded_txts/{midi_filename}.txt", piece_text)


if __name__ == "__main__":
    main()
