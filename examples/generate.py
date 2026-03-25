"""Example: Generate new MIDI music with The Jam Machine.

Generates a multi-track piece using the GPT-2 model, then decodes it
to MIDI and saves a piano roll visualization.

Setup:
    pipenv install -e "."

Usage:
    pipenv run python examples/generate.py
"""

from __future__ import annotations

import logging
from pathlib import Path

from jammy.constants import MODEL_REPO, MODEL_REVISION
from jammy.embedding.decoder import TextDecoder
from jammy.generating.config import GenerationConfig, TrackConfig
from jammy.generating.file_io import define_generation_dir, write_text_midi_to_file
from jammy.generating.generate import GenerateMidiText
from jammy.generating.playback import get_music
from jammy.generating.validation import check_if_prompt_inst_in_tokenizer_vocab
from jammy.generating.visualization import plot_piano_roll
from jammy.logging_config import setup_logging
from jammy.preprocessing.load import LoadModel
from jammy.utils import get_miditok

logger = logging.getLogger(__name__)

# Instrument family numbers: see INSTRUMENT_CLASSES in jammy/constants.py
# DRUMS, 0=piano, 1=chromatic perc, 2=organ, 3=guitar, 4=bass, 5=strings,
# 6=ensemble, 7=brass, 8=reed, 9=pipe, 10=synth lead, 11=synth pad,
# 12=synth fx, 13=ethnic, 14=percussive, 15=sound fx

USE_FAMILIZED_MODEL = True
N_BARS = 8
TEMPERATURE = 0.7
DEFAULT_OUTPUT_DIR = "output/examples/generation"
TRACKS = [
    TrackConfig(instrument="DRUMS", density=3, temperature=TEMPERATURE),
    TrackConfig(instrument="4", density=2, temperature=TEMPERATURE),
    TrackConfig(instrument="3", density=2, temperature=TEMPERATURE),
]


def generate_and_save(
    generator: GenerateMidiText,
    tracks: list[TrackConfig],
    output_dir: str,
) -> None:
    """Generate a piece and save MIDI, piano roll, and JSON outputs.

    Args:
        generator: Configured MIDI text generator.
        tracks: Track configurations for the piece.
        output_dir: Directory for output files.
    """
    logger.info("Generating new piece...")

    generator.generate_piece(tracks)
    generated_piece = generator.get_piece_text()

    logger.info("Generated piece:\n%s", generated_piece)

    # Write to JSON file
    json_path = write_text_midi_to_file(generated_piece, generator.piece.piece_by_track, output_dir)
    base_path = Path(json_path).with_suffix("")

    # Decode to MIDI
    midi_path = str(base_path.with_suffix(".mid"))
    decode_tokenizer = get_miditok()
    TextDecoder(decode_tokenizer, USE_FAMILIZED_MODEL).get_midi(generated_piece, filename=midi_path)

    # Generate piano roll visualization
    inst_midi, _ = get_music(midi_path)
    piano_roll_fig = plot_piano_roll(inst_midi)
    piano_roll_fig.savefig(str(base_path) + "_piano_roll.png", bbox_inches="tight")
    piano_roll_fig.clear()

    logger.info("Done! MIDI saved to %s", midi_path)


def main(output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> None:
    """Run the MIDI generation example.

    Args:
        output_dir: Directory for output files. Defaults to
            ``output/examples/generation/``.
    """
    setup_logging(log_to_file=False)

    output_dir = define_generation_dir(output_dir)

    model, tokenizer = LoadModel(
        MODEL_REPO, from_huggingface=True, revision=MODEL_REVISION
    ).load_model_and_tokenizer()

    instruments = [t.instrument for t in TRACKS]
    check_if_prompt_inst_in_tokenizer_vocab(tokenizer, instruments)

    config = GenerationConfig(n_bars=N_BARS)
    generator = GenerateMidiText(model, tokenizer, config=config)
    generate_and_save(generator, TRACKS, output_dir)


if __name__ == "__main__":
    main()
