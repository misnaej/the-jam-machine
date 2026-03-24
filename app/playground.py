"""Gradio web interface for The Jam Machine."""

from __future__ import annotations

import sys
from typing import Any, NamedTuple

import gradio as gr
import matplotlib
import numpy as np  # noqa: TC002 - needed at runtime for Gradio type introspection
from matplotlib import pylab
from matplotlib.figure import (
    Figure,  # noqa: TC002 - needed at runtime for Gradio type introspection
)

from jammy.constants import INSTRUMENT_TRANSFER_CLASSES
from jammy.embedding.decoder import TextDecoder
from jammy.generating.config import TrackConfig
from jammy.generating.generate import GenerateMidiText
from jammy.generating.playback import get_music
from jammy.generating.visualization import plot_piano_roll
from jammy.logging_config import setup_logging
from jammy.preprocessing.load import LoadModel
from jammy.tokens import PIECE_START
from jammy.utils import get_miditok

matplotlib.use("Agg")

# Configure logging - logs will be saved to ./output/logs/
setup_logging(output_dir="./output")

sys.modules["pylab"] = pylab

MODEL_REPO = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
N_BAR_GENERATED = 8
SAMPLE_RATE = 44100

model, tokenizer = LoadModel(
    MODEL_REPO,
    from_huggingface=True,
).load_model_and_tokenizer()

miditok = get_miditok()
decoder = TextDecoder(miditok)


class GeneratorResult(NamedTuple):
    """Result from the _generator function.

    This is a NamedTuple (not a dataclass) because Gradio's event system
    unpacks return values positionally into output components. NamedTuple
    supports tuple unpacking natively, while dataclass would not.

    Attributes:
        inst_text: Generated text for the individual instrument track.
        inst_audio: Tuple of (sample_rate, waveform) for the instrument.
        piano_roll: Matplotlib figure of the piano roll visualization.
        state: Updated list of track state dictionaries.
        mixed_audio: Tuple of (sample_rate, waveform) for the full mix.
        regenerate: Whether the track can be regenerated.
        piece_by_track: Updated piece data organized by track.
        output_file: Path to the output MIDI file.
    """

    inst_text: str
    inst_audio: tuple[int, np.ndarray]
    piano_roll: Figure
    state: list[dict[str, Any]]
    mixed_audio: tuple[int, np.ndarray]
    regenerate: bool
    piece_by_track: list[dict[str, Any]]
    output_file: str


def _define_prompt(state: list[dict[str, Any]], genesis: GenerateMidiText) -> str:
    """Get the current prompt based on state.

    Args:
        state: List of track state dictionaries.
        genesis: The generator instance.

    Returns:
        The prompt string to use for generation.
    """
    if len(state) == 0:
        return f"{PIECE_START} "
    return genesis.get_piece_text()


def _generator(
    label: int,
    regenerate: bool,
    temp: float,
    density: int,
    instrument: str,
    state: list[dict[str, Any]],
    piece_by_track: list[dict[str, Any]],
    add_bars: bool = False,
    add_bar_count: int = 1,
) -> GeneratorResult:
    """Generate music based on the given parameters.

    Args:
        label: Track label/index.
        regenerate: Whether to regenerate an existing track.
        temp: Temperature for generation.
        density: Note density level.
        instrument: Instrument name.
        state: Current state of all tracks.
        piece_by_track: Piece data by track.
        add_bars: Whether to add bars instead of new track.
        add_bar_count: Number of bars to add.

    Returns:
        GeneratorResult with generated text, audio, piano roll, and updated state.
    """
    genesis = GenerateMidiText(model, tokenizer, piece_by_track)
    track = {
        "label": label,
        "instrument": instrument,
        "temperature": temp,
        "density": density,
    }
    inst = next(
        (inst for inst in INSTRUMENT_TRANSFER_CLASSES if inst["transfer_to"] == instrument),
        {"family_number": "DRUMS"},
    )["family_number"]

    inst_index = -1  # default to last generated
    if piece_by_track != []:
        for index, instrum in enumerate(state):
            if instrum["label"] == track["label"]:
                inst_index = index  # changing if exists

    # Generate
    if not add_bars:
        # Regenerate
        if regenerate:
            state.pop(inst_index)
            genesis.delete_track(inst_index)
            genesis.get_piece_text()  # refresh state
            inst_index = -1  # reset to last generated

        # NEW TRACK
        input_prompt = _define_prompt(state, genesis)
        track_config = TrackConfig(instrument=inst, density=density, temperature=temp)
        genesis.generate_one_new_track(track_config, input_prompt=input_prompt)

        regenerate = True  # set generate to true
    else:
        # NEW BARS
        genesis.generate_n_more_bars(add_bar_count)  # for all instruments

    # save the mix midi and get the mix audio
    generated_text = genesis.get_piece_text()
    decoder.get_midi(generated_text, "mixed.mid")
    mixed_inst_midi, mixed_audio = get_music("mixed.mid")
    # get the instrument text MIDI
    inst_text = genesis.get_track_text(inst_index)
    # save the instrument midi and get the instrument audio
    decoder.get_midi(inst_text, f"{instrument}.mid")
    _, inst_audio = get_music(f"{instrument}.mid")
    # generate the piano roll
    piano_roll = plot_piano_roll(mixed_inst_midi)
    track["text"] = inst_text
    state.append(track)
    return GeneratorResult(
        inst_text=inst_text,
        inst_audio=(SAMPLE_RATE, inst_audio),
        piano_roll=piano_roll,
        state=state,
        mixed_audio=(SAMPLE_RATE, mixed_audio),
        regenerate=regenerate,
        piece_by_track=genesis.piece.piece_by_track,
        output_file="./mixed.mid",
    )


def _generated_text_from_state(state: list[dict[str, Any]]) -> str:
    """Combine all track texts from state into a full piece.

    Args:
        state: List of track state dictionaries.

    Returns:
        Combined piece text.
    """
    result = f"{PIECE_START} "
    for track in state:
        result += track["text"]
    return result


def _instrument_col(default_inst: str, col_id: int) -> None:
    """Create a column UI for instrument controls.

    Args:
        default_inst: Default instrument name.
        col_id: Column ID (0-indexed).
    """
    inst_label = gr.State(col_id)
    with gr.Column(scale=1, min_width=100):
        gr.Markdown(f"""## TRACK {col_id + 1}""")
        inst = gr.Dropdown(
            [*sorted(inst["transfer_to"] for inst in INSTRUMENT_TRANSFER_CLASSES), "Drums"],
            value=default_inst,
            label="Instrument",
        )
        temp = gr.Dropdown(
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1],
            value=0.7,
            label="Creativity",
        )
        density = gr.Dropdown([1, 2, 3], value=3, label="Note Density")
        regenerate = gr.State(value=False)
        gen_btn = gr.Button("Generate")
        inst_audio = gr.Audio(label="TRACK Audio", show_label=True)
        output_txt = gr.Textbox(
            label="output", lines=10, max_lines=10, show_label=False, visible=False
        )

    gen_btn.click(
        fn=_generator,
        inputs=[inst_label, regenerate, temp, density, inst, state, piece_by_track],
        outputs=[
            output_txt,
            inst_audio,
            piano_roll,
            state,
            mixed_audio,
            regenerate,
            piece_by_track,
            output_file,
        ],
    )


DESCRIPTION = """
For each **TRACK**, choose your **instrument** along with **creativity**
(temperature) and **note density**.
Then, hit the **Generate** Button, and after a few seconds a track should
have been generated.
Check the **piano roll** and listen to the TRACK! If you don't like it,
hit the generate button to regenerate it.
You can then generate more tracks and listen to the **mixed audio**!

Does it sound nice? Maybe a little robotic and lacking some depth...
Well, you can download the MIDI file and import it in your favorite DAW
to edit the instruments and add some effects!

Note: Do not try to generate several tracks simultaneously as it will
crash the app; wait for one track to be generated before generating another one.
"""

with gr.Blocks() as demo:
    piece_by_track = gr.State([])
    state = gr.State([])
    gr.Markdown(
        """# Demo-App of The-Jam-Machine
## A Generative AI trained on text transcription of MIDI music"""
    )

    gr.Markdown(DESCRIPTION)

    gr.Markdown("""## Mixed Audio, Piano Roll and MIDI Download""")
    with gr.Row(variant="default"):
        mixed_audio = gr.Audio(label="Mixed Audio", show_label=False)
        output_file = gr.File(
            label="Download",
            show_label=False,
        )
    with gr.Row(variant="compact"):
        piano_roll = gr.Plot(label="Piano Roll", show_label=False)

    with gr.Row(variant="default"):
        _instrument_col("Drums", 0)
        _instrument_col("Synth Bass 1", 1)
        _instrument_col("Synth Lead Square", 2)

demo.launch(debug=True, server_name="0.0.0.0", share=False)  # noqa: S104

# TODO: add improvise button
# TODO: cleanup input output of generator
# TODO: add a way to add bars
