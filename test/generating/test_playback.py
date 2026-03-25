"""Tests for the playback module."""

from __future__ import annotations

import shutil

import pytest

from jammy.generating.playback import get_music


@pytest.mark.skipif(
    shutil.which("fluidsynth") is None,
    reason="FluidSynth not installed — skip audio tests",
)
class TestGetMusic:
    """Tests for get_music."""

    def test_get_music_returns_midi_and_audio(self) -> None:
        """Test loading a MIDI file and synthesizing audio.

        Uses the Reptilia MIDI file (git-tracked test fixture).
        """
        midi, waveform = get_music("midi/the_strokes-reptilia.mid")
        assert midi is not None
        assert len(midi.instruments) > 0
        assert waveform is not None
        assert len(waveform) > 0
