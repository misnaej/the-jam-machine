from __future__ import annotations

import logging
from pathlib import Path

from miditok import MIDILike
from miditoolkit import MidiFile

from ..utils import writeToFile
from .encoder import MIDIEncoder

logger = logging.getLogger(__name__)

pitch_range = range(21, 109)
beat_res = {(0, 400): 8}
tokenizer = MIDILike(pitch_range, beat_res)
encoder = MIDIEncoder(tokenizer)

midi_files = [f"midi/{f.name}" for f in Path("midi/").iterdir() if f.suffix == ".mid"]

# midi_files = []

for file in midi_files:
    try:
        midi = MidiFile(file)
    except Exception:
        logger.warning("Failed to load %s", file)
        continue

    piece_text = encoder.get_piece_text(midi)

    file_path = Path(file)
    midi_filename = file_path.stem
    dirname = file_path.parent
    writeToFile(f"{dirname}/encoded_txts/{midi_filename}.txt", piece_text)
