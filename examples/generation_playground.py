# ruff: noqa: T201
"""Example script demonstrating MIDI generation with The Jam Machine."""

from __future__ import annotations

from pathlib import Path

from jammy.embedding.decoder import TextDecoder
from jammy.generating.config import GenerationConfig, TrackConfig
from jammy.generating.generate import GenerateMidiText
from jammy.generating.playback import get_music
from jammy.generating.utils import (
    WriteTextMidiToFile,
    check_if_prompt_inst_in_tokenizer_vocab,
    define_generation_dir,
    plot_piano_roll,
)
from jammy.preprocessing.load import LoadModel
from jammy.utils import get_miditok

# Instrument family mapping:
# DRUMS = drums, 0 = piano, 1 = chromatic percussion, 2 = organ, 3 = guitar,
# 4 = bass, 5 = strings, 6 = ensemble, 7 = brass, 8 = reed, 9 = pipe,
# 10 = synth lead, 11 = synth pad, 12 = synth effects, 13 = ethnic,
# 14 = percussive, 15 = sound effects

MODEL_REPO = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
USE_FAMILIZED_MODEL = True
N_FILES = 1
N_BARS = 8
TEMPERATURES = [0.7]
TRACK_PRESETS: list[tuple[str, int]] = [
    ("DRUMS", 3),
    ("4", 2),
    ("3", 2),
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
    print("========================================")

    generator.generate_piece(tracks)
    generator.generated_piece = generator.get_whole_piece_from_bar_dict()

    print("=========================================")
    print(generator.generated_piece)
    print("=========================================")

    # Write to JSON file
    json_path = WriteTextMidiToFile(generator, output_dir).text_midi_to_file()
    base_path = Path(json_path).with_suffix("")

    # Decode to MIDI
    midi_path = str(base_path.with_suffix(".mid"))
    decode_tokenizer = get_miditok()
    TextDecoder(decode_tokenizer, USE_FAMILIZED_MODEL).get_midi(
        generator.generated_piece, filename=midi_path
    )

    # Generate piano roll visualization
    inst_midi, _ = get_music(midi_path)
    piano_roll_fig = plot_piano_roll(inst_midi)
    piano_roll_fig.savefig(str(base_path) + "_piano_roll.png", bbox_inches="tight")
    piano_roll_fig.clear()

    print("Et voilà! Your MIDI file is ready! GO JAM!")


def main() -> None:
    """Run the MIDI generation example."""
    output_dir = define_generation_dir(f"midi/generated/{MODEL_REPO}")

    model, tokenizer = LoadModel(MODEL_REPO, from_huggingface=True).load_model_and_tokenizer()

    instruments = [inst for inst, _ in TRACK_PRESETS]
    check_if_prompt_inst_in_tokenizer_vocab(tokenizer, instruments)

    config = GenerationConfig(n_bars=N_BARS)

    for temperature in TEMPERATURES:
        print(f"================= TEMPERATURE {temperature} =======================")
        tracks = [
            TrackConfig(instrument=inst, density=dens, temperature=temperature)
            for inst, dens in TRACK_PRESETS
        ]
        for _ in range(N_FILES):
            generator = GenerateMidiText(model, tokenizer, config=config)
            generate_and_save(generator, tracks, output_dir)


if __name__ == "__main__":
    main()
