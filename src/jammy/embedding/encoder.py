"""MIDI to text encoding module.

This module provides the main orchestrator for converting MIDI files into a text
token representation suitable for training and generation with transformer models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from miditoolkit import MidiFile

from jammy.embedding import bar_processing, time_processing, track_setup
from jammy.midi_codec import get_text
from jammy.utils import get_miditok

if TYPE_CHECKING:
    from miditok import Event, MIDILike


class MIDIEncoder:
    """Encoder for converting MIDI files to text token representation.

    This class orchestrates the full encoding pipeline: extracting MIDI events,
    processing time shifts, adding bar markers and density, building sections,
    and converting to text.

    Attributes:
        tokenizer: The MIDILike tokenizer instance.
        familized: Whether to familize instruments.
    """

    def __init__(self, tokenizer: MIDILike, *, familized: bool = False) -> None:
        """Initialize the MIDI encoder.

        Args:
            tokenizer: The MIDILike tokenizer instance for MIDI processing.
            familized: Whether to group instruments by family. Defaults to False.
        """
        self.tokenizer = tokenizer
        self.familized = familized

    def get_midi_events(self, midi: MidiFile) -> list[list[Event]]:
        """Get MIDI events from a MIDI file.

        Args:
            midi: The MidiFile object to process.

        Returns:
            List of event lists, one per instrument.
        """
        return [
            self.tokenizer.tokens_to_events(inst_tokens)
            for inst_tokens in self.tokenizer.midi_to_tokens(midi)
        ]

    def get_piece_text(self, midi: MidiFile) -> str:
        """Convert a MIDI file to text representation.

        Orchestrates the full encoding pipeline:
        1. Extract events from MIDI
        2. Process time shifts
        3. Add bar markers and density
        4. Build sections
        5. Convert to text

        Args:
            midi: The MidiFile object to process.

        Returns:
            Text representation of the MIDI piece.
        """
        midi_events = self.get_midi_events(midi)

        # Time processing
        midi_events = time_processing.remove_velocity(midi_events)
        midi_events = time_processing.normalize_timeshifts(midi_events)

        # Bar processing
        midi_events = bar_processing.add_bars(midi_events)
        midi_events = time_processing.combine_timeshifts_in_bar(midi_events)
        midi_events = time_processing.remove_timeshifts_preceding_bar_end(midi_events)
        midi_events = bar_processing.add_density_to_bar(midi_events)

        # Section building
        sections = track_setup.make_sections(
            midi_events,
            midi.instruments,
            familized=self.familized,
        )
        sections = bar_processing.add_density_to_sections(sections)

        # Convert to text
        piece = track_setup.sections_to_piece(sections)
        return events_to_text(piece)


def events_to_text(events: list[Event]) -> str:
    """Convert miditok events to text.

    Args:
        events: List of miditok Event objects.

    Returns:
        Text representation of the events.
    """
    parts: list[str] = []
    current_instrument = "undefined"
    for event in events:
        if event.type == "Instrument":
            current_instrument = str(event.value)
        parts.append(get_text(event, current_instrument))
    return "".join(parts)


def from_midi_to_sectioned_text(midi_filename: str, *, familized: bool = False) -> str:
    """Convert a MIDI file to a MidiText input prompt.

    Args:
        midi_filename: Path to the MIDI file (without .mid extension).
        familized: Whether to familize instruments. Defaults to False.

    Returns:
        Text representation of the MIDI file.
    """
    midi = MidiFile(f"{midi_filename}.mid")
    midi_like = get_miditok()
    return MIDIEncoder(midi_like, familized=familized).get_piece_text(midi)
