"""Utility functions for MIDI generation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from jammy.constants import INSTRUMENT_CLASSES
from jammy.utils import get_datetime, writeToFile

if TYPE_CHECKING:
    import pretty_midi

    from .generate import GenerateMidiText

# matplotlib settings
matplotlib.use("Agg")  # for server
matplotlib.rcParams["xtick.major.size"] = 0
matplotlib.rcParams["ytick.major.size"] = 0
matplotlib.rcParams["axes.facecolor"] = "none"
matplotlib.rcParams["axes.edgecolor"] = "grey"

logger = logging.getLogger(__name__)


class WriteTextMidiToFile:
    """Utility for saving MIDI text from GenerateMidiText to file."""

    def __init__(self, generate_midi: GenerateMidiText, output_path: str) -> None:
        """Initialize the writer.

        Args:
            generate_midi: The generator containing the piece data.
            output_path: Directory path to save files.
        """
        self.generated_midi = generate_midi.generated_piece
        self.output_path = output_path
        self.hyperparameter_and_bars = generate_midi.piece.piece_by_track
        self.current_time: str = ""
        self.output_path_filename: str = ""

    def hashing_seq(self) -> None:
        """Generate a timestamped filename."""
        self.current_time = get_datetime()
        self.output_path_filename = f"{self.output_path}/{self.current_time}.json"

    def wrapping_seq_hyperparameters_in_dict(self) -> dict[str, Any]:
        """Wrap the sequence and hyperparameters in a dictionary.

        Returns:
            Dictionary containing the generated MIDI and hyperparameters.
        """
        return {
            "generated_midi": self.generated_midi,
            "hyperparameters_and_bars": self.hyperparameter_and_bars,
        }

    def text_midi_to_file(self) -> str:
        """Save the MIDI text to a JSON file.

        Returns:
            Path to the saved file.
        """
        self.hashing_seq()
        output_dict = self.wrapping_seq_hyperparameters_in_dict()
        logger.info("Token generate_midi written: %s", self.output_path_filename)
        writeToFile(self.output_path_filename, output_dict)
        return self.output_path_filename


def define_generation_dir(generation_dir: str) -> str:
    """Create generation directory if it doesn't exist.

    Args:
        generation_dir: Path to the generation directory.

    Returns:
        The same directory path.
    """
    Path(generation_dir).mkdir(parents=True, exist_ok=True)
    return generation_dir


def bar_count_check(sequence: str, n_bars: int) -> tuple[bool, int]:
    """Check if the sequence contains the right number of bars.

    Args:
        sequence: The MIDI text sequence to check.
        n_bars: Expected number of bars.

    Returns:
        Tuple of (matches, actual_count).
    """
    tokens = sequence.split(" ")
    bar_count = sum(1 for token in tokens if token == "BAR_END")  # noqa: S105
    bar_count_matches = bar_count == n_bars
    if not bar_count_matches:
        logger.info("Bar count is %d - but should be %d", bar_count, n_bars)
    return bar_count_matches, bar_count


def print_inst_classes(instrument_classes: list[dict]) -> None:
    """Log the instrument classes.

    Args:
        instrument_classes: List of instrument class definitions.
    """
    for classe in instrument_classes:
        logger.info("%s", classe)


def check_if_prompt_inst_in_tokenizer_vocab(
    tokenizer: Any,  # noqa: ANN401
    inst_prompt_list: list[str],
) -> None:
    """Check if the prompt instruments are in the tokenizer vocab.

    Args:
        tokenizer: The tokenizer to check against.
        inst_prompt_list: List of instruments to validate.

    Raises:
        ValueError: If an instrument is not in the tokenizer vocabulary.
    """
    for inst in inst_prompt_list:
        if f"INST={inst}" not in tokenizer.vocab:
            instruments_in_dataset = np.sort(
                [tok.split("=")[-1] for tok in tokenizer.vocab if "INST" in tok]
            )
            print_inst_classes(INSTRUMENT_CLASSES)
            raise ValueError(
                f"The instrument {inst} is not in the tokenizer vocabulary. "
                f"Available Instruments: {instruments_in_dataset}"
            )


def check_if_prompt_density_in_tokenizer_vocab(
    tokenizer: Any,  # noqa: ANN401
    density_prompt_list: list[int],
) -> None:
    """Check if the prompt densities are in the tokenizer vocab.

    Args:
        tokenizer: The tokenizer to check against.
        density_prompt_list: List of densities to validate.
    """
    # TODO: Implement density validation
    pass


def forcing_bar_count(
    input_prompt: str,
    generated: str,
    bar_count: int,
    expected_length: int,
) -> tuple[str, bool]:
    """Force the generated sequence to have the expected length.

    Args:
        input_prompt: The original input prompt.
        generated: The generated sequence (without prompt).
        bar_count: Actual number of bars generated.
        expected_length: Expected number of bars.

    Returns:
        Tuple of (full_piece, bar_count_checks).
    """
    if bar_count - expected_length > 0:  # Cut the sequence if too long
        full_piece = ""
        splited = generated.split("BAR_END ")
        for count, spl in enumerate(splited):
            if count < expected_length:
                full_piece += spl + "BAR_END "

        full_piece += "TRACK_END "
        full_piece = input_prompt + full_piece
        logger.info("Generated sequence truncated at %d bars", expected_length)
        bar_count_checks = True

    else:  # bar_count - expected_length < 0: Sequence is too short
        full_piece = input_prompt + generated
        bar_count_checks = False
        logger.info("Generated sequence is too short - Force Regeneration")

    return full_piece, bar_count_checks


def get_max_time(inst_midi: pretty_midi.PrettyMIDI) -> float:
    """Get the maximum end time across all instruments.

    Args:
        inst_midi: PrettyMIDI object.

    Returns:
        Maximum end time in seconds.
    """
    max_time = 0.0
    for inst in inst_midi.instruments:
        max_time = max(max_time, inst.get_end_time())
    return max_time


def plot_piano_roll(inst_midi: pretty_midi.PrettyMIDI) -> plt.Figure:
    """Generate a piano roll visualization of the MIDI.

    Args:
        inst_midi: PrettyMIDI object to visualize.

    Returns:
        Matplotlib figure containing the piano roll.
    """
    piano_roll_fig = plt.figure(figsize=(25, 3 * len(inst_midi.instruments)))
    piano_roll_fig.tight_layout()
    piano_roll_fig.patch.set_alpha(0)
    beats_per_bar = 4
    sec_per_beat = 0.5
    next_beat = max(inst_midi.get_beats()) + np.diff(inst_midi.get_beats())[0]
    bars_time = np.append(inst_midi.get_beats(), (next_beat))[::beats_per_bar].astype(int)

    for inst_count, inst in enumerate(inst_midi.instruments, start=1):
        # hardcoded colors for now
        if inst.name == "Drums":
            color = "purple"
        elif inst.name == "Synth Bass 1":
            color = "orange"
        else:
            color = "green"

        plt.subplot(len(inst_midi.instruments), 1, inst_count)

        for bar in bars_time:
            plt.axvline(bar, color="grey", linewidth=0.5)
        octaves = np.arange(0, 128, 12)
        for octave in octaves:
            plt.axhline(octave, color="grey", linewidth=0.5)
        plt.yticks(octaves, visible=False)

        p_midi_note_list = inst.notes
        note_time = []
        note_pitch = []
        for note in p_midi_note_list:
            note_time.append([note.start, note.end])
            note_pitch.append([note.pitch, note.pitch])
        note_pitch = np.array(note_pitch)
        note_time = np.array(note_time)

        plt.plot(
            note_time.T,
            note_pitch.T,
            color=color,
            linewidth=4,
            solid_capstyle="butt",
        )
        plt.ylim(0, 128)
        xticks = np.array(bars_time)[:-1]
        plt.tight_layout()
        plt.xlim(min(bars_time), max(bars_time))
        plt.ylim(max([note_pitch.min() - 5, 0]), note_pitch.max() + 5)
        plt.xticks(
            xticks + 0.5 * beats_per_bar * sec_per_beat,
            labels=xticks.argsort() + 1,
            visible=False,
        )
        plt.text(
            0.2,
            note_pitch.max() + 4,
            inst.name,
            fontsize=20,
            color=color,
            horizontalalignment="left",
            verticalalignment="top",
        )

    return piano_roll_fig
