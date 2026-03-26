"""Visualization utilities for MIDI piano roll display."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from jammy.constants import BEATS_PER_BAR

if TYPE_CHECKING:
    import pretty_midi

# matplotlib settings
matplotlib.use("Agg")  # for server
matplotlib.rcParams["xtick.major.size"] = 0
matplotlib.rcParams["ytick.major.size"] = 0
matplotlib.rcParams["axes.facecolor"] = "none"
matplotlib.rcParams["axes.edgecolor"] = "grey"


_INSTRUMENT_COLORS: dict[str, str] = {
    "Drums": "purple",
    "Synth Bass 1": "orange",
}
_DEFAULT_COLOR = "green"
_SEC_PER_BEAT = 0.5


def _get_instrument_color(name: str) -> str:
    """Return the display color for an instrument.

    Args:
        name: Instrument name.

    Returns:
        Color string for matplotlib.
    """
    return _INSTRUMENT_COLORS.get(name, _DEFAULT_COLOR)


def _plot_instrument_subplot(
    inst: pretty_midi.Instrument,
    subplot_index: int,
    total_instruments: int,
    bars_time: np.ndarray,
) -> None:
    """Plot a single instrument's notes as a piano roll subplot.

    Args:
        inst: PrettyMIDI instrument to plot.
        subplot_index: 1-based subplot index.
        total_instruments: Total number of subplots.
        bars_time: Array of bar boundary times.
    """
    color = _get_instrument_color(inst.name)
    plt.subplot(total_instruments, 1, subplot_index)

    for bar in bars_time:
        plt.axvline(bar, color="grey", linewidth=0.5)
    octaves = np.arange(0, 128, 12)
    for octave in octaves:
        plt.axhline(octave, color="grey", linewidth=0.5)
    plt.yticks(octaves, visible=False)

    note_time = []
    note_pitch = []
    for note in inst.notes:
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
    xticks = np.array(bars_time)[:-1]
    plt.tight_layout()
    plt.xlim(min(bars_time), max(bars_time))
    plt.ylim(max([note_pitch.min() - 5, 0]), note_pitch.max() + 5)
    plt.xticks(
        xticks + 0.5 * BEATS_PER_BAR * _SEC_PER_BEAT,
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
    next_beat = max(inst_midi.get_beats()) + np.diff(inst_midi.get_beats())[0]
    bars_time = np.append(inst_midi.get_beats(), (next_beat))[::BEATS_PER_BAR].astype(int)

    for inst_count, inst in enumerate(inst_midi.instruments, start=1):
        _plot_instrument_subplot(inst, inst_count, len(inst_midi.instruments), bars_time)

    return piano_roll_fig
