from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import librosa.display
import matplotlib.pyplot as plt
from pretty_midi import PrettyMIDI

if TYPE_CHECKING:
    import numpy as np

# Note: these functions are meant to be played within an interactive Python shell
# Please refer to the synth.ipynb for an example of how to use them

logger = logging.getLogger(__name__)


def get_music(midi_file: str) -> tuple[PrettyMIDI, np.ndarray]:
    """Load a MIDI file and return the PrettyMIDI object and the audio signal."""
    logger.info("Getting MIDI music from: %s", midi_file)
    music = PrettyMIDI(midi_file=midi_file)
    waveform = music.fluidsynth()
    return music, waveform


def show_piano_roll(music_notes: PrettyMIDI, fs: int = 100) -> None:
    """Show the piano roll of a music piece.

    All instruments are squashed onto a single 128xN matrix.

    Args:
        music_notes: PrettyMIDI object.
        fs: Sampling frequency.
    """
    # get the piano roll
    piano_roll = music_notes.get_piano_roll(fs)
    logger.info("Piano roll shape: %s", piano_roll.shape)

    # plot the piano roll
    plt.figure(figsize=(12, 4))
    librosa.display.specshow(piano_roll, sr=100, x_axis="time", y_axis="cqt_note")
    plt.colorbar()
    plt.title("Piano roll")
    plt.tight_layout()
    plt.show()
