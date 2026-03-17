"""Visualization utilities for MIDI piano roll display."""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

if TYPE_CHECKING:
    import pretty_midi

# matplotlib settings
matplotlib.use("Agg")  # for server
matplotlib.rcParams["xtick.major.size"] = 0
matplotlib.rcParams["ytick.major.size"] = 0
matplotlib.rcParams["axes.facecolor"] = "none"
matplotlib.rcParams["axes.edgecolor"] = "grey"


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
