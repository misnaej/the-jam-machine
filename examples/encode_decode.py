"""Example: Encode a MIDI file to text tokens and decode back to MIDI.

Demonstrates the encoding/decoding pipeline using The Strokes - Reptilia
as a reference MIDI file. This is the same pipeline used to prepare
training data for the GPT-2 model.

Setup:
    pipenv install -e "."

Usage:
    pipenv run python examples/encode_decode.py
"""

from __future__ import annotations

import logging
from pathlib import Path

from jammy.embedding.decoder import TextDecoder
from jammy.embedding.encoder import MIDIEncoder
from jammy.file_utils import write_to_file
from jammy.generating.playback import get_music
from jammy.generating.visualization import plot_piano_roll
from jammy.logging_config import setup_logging
from jammy.utils import get_miditok

logger = logging.getLogger(__name__)

MIDI_INPUT = Path("midi/the_strokes-reptilia.mid")
USE_FAMILIZED = True
DEFAULT_OUTPUT_DIR = Path("output/examples/encode_decode")


def main(output_dir: Path = DEFAULT_OUTPUT_DIR) -> None:
    """Run the encode/decode roundtrip example.

    Args:
        output_dir: Directory for output files. Defaults to
            ``output/examples/encode_decode/``.
    """
    setup_logging(log_to_file=False)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Encode MIDI to text ---
    logger.info("Loading MIDI file: %s", MIDI_INPUT)
    # Runtime import — miditoolkit is heavy
    from miditoolkit import MidiFile

    midi = MidiFile(str(MIDI_INPUT))
    logger.info(
        "MIDI loaded: %d instruments, %d ticks per beat",
        len(midi.instruments),
        midi.ticks_per_beat,
    )

    tokenizer = get_miditok()
    encoder = MIDIEncoder(tokenizer, familized=USE_FAMILIZED)
    piece_text = encoder.get_piece_text(midi)

    logger.info("Encoded text length: %d characters", len(piece_text))
    logger.info("Preview: %s...", piece_text[:200])

    # Save encoded text
    text_path = output_dir / "the_strokes-reptilia_encoded.txt"
    write_to_file(text_path, piece_text)
    logger.info("Encoded text saved to: %s", text_path)

    # --- Decode text back to MIDI ---
    decoder = TextDecoder(tokenizer, familized=USE_FAMILIZED)
    midi_path = output_dir / "the_strokes-reptilia_decoded.mid"
    try:
        decoded_midi = decoder.get_midi(piece_text, filename=str(midi_path))
        logger.info("Decoded MIDI saved to: %s", midi_path)
        decoded_instrument_count = len(decoded_midi.instruments)
    except KeyError as e:
        # Some MIDI files produce tokens (e.g. zero time shifts) that aren't
        # in the tokenizer vocabulary. This is a known limitation.
        logger.warning("Decoding failed on token %s — skipping MIDI output", e)
        decoded_instrument_count = 0

    # --- Generate piano roll from original MIDI ---
    inst_midi, _ = get_music(str(MIDI_INPUT))
    piano_roll = plot_piano_roll(inst_midi)
    piano_roll_path = output_dir / "the_strokes-reptilia_piano_roll.png"
    piano_roll.savefig(str(piano_roll_path), bbox_inches="tight")
    piano_roll.clear()
    logger.info("Piano roll saved to: %s", piano_roll_path)

    # --- Summary ---
    logger.info("--- Roundtrip Summary ---")
    logger.info("Original instruments: %d", len(midi.instruments))
    logger.info("Decoded instruments:  %d", decoded_instrument_count)
    logger.info("Output directory:     %s", output_dir)


if __name__ == "__main__":
    main()
