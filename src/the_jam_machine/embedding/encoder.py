"""MIDI to text encoding module.

This module provides functionality to convert MIDI files into a text token
representation suitable for training and generation with transformer models.
"""

from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING

import numpy as np
from miditok import Event
from scipy import stats

from ..constants import BEATS_PER_BAR
from ..utils import (
    beat_to_int_dec_base,
    chain,
    get_miditok,
    get_text,
    int_dec_base_to_beat,
    split_dots,
    writeToFile,
)
from .familizer import Familizer

if TYPE_CHECKING:
    from miditok import MIDILike
    from miditoolkit import Instrument, MidiFile

logger = logging.getLogger(__name__)

# TODO HIGH PRIORITY
# TODO: The Density calculation does not match that of Tristan's Encoding.
#       Ask Tristan about it.
# TODO: Data augmentation:
#   - hopping K bars and re-encode almost same notes: needs to keep track of
#     sequence length
#   - computing track key
#       - octave shifting
#       - pitch shifting
# TODO: Solve the one-instrument tracks problem -> needs an external function
#       that converts the one track midi to multi-track midi based on the
#       "channel information"
# TODO: Solve the one instrument spread to many channels problem -> it creates
#       several instruments instead of one

# LOW PRIORITY
# TODO: Improve method comments
# TODO: Density Bins - Calculation Done - Not sure if it the best way - MMM
#       paper uses a normalized density based on the entire instrument density
#       in the dataset. They say that density for a given instrument does not
#       mean the same for another. However, I am expecting that the instrument
#       token is already implicitly taking care of that.
# Question: How to determine difference between 8 very long notes in 8 bar and
#           6 empty bar + 8 very short notes in last 2 bar?
# TODO: Should empty sections be filled with bar start and bar end events?
# TODO: changing the methods to avoid explicit loops and use the map function
#       instead?

# NEW IDEAS
# TODO: Changing Generation approach: encoding all tracks in the same key and
#       choose the key while generating, so we just shift the key after
#       generation.


class MIDIEncoder:
    """Encoder for converting MIDI files to text token representation.

    This class handles the conversion of MIDI events to a text format suitable
    for training transformer models. It processes velocity, time shifts, bars,
    density, and sections.

    Attributes:
        tokenizer: The MIDILike tokenizer instance.
        familized: Whether to familize instruments.
    """

    def __init__(self, tokenizer: MIDILike, familized: bool = False) -> None:
        """Initialize the MIDI encoder.

        Args:
            tokenizer: The MIDILike tokenizer instance for MIDI processing.
            familized: Whether to group instruments by family. Defaults to False.
        """
        self.tokenizer = tokenizer
        self.familized = familized

    @staticmethod
    def remove_velocity(midi_events: list[list[Event]]) -> list[list[Event]]:
        """Remove velocity events from MIDI events.

        Args:
            midi_events: List of instrument event lists.

        Returns:
            MIDI events with velocity events removed.
        """
        return [
            [event for event in inst_events if event.type != "Velocity"]
            for inst_events in midi_events
        ]

    @staticmethod
    def set_timeshifts_to_min_length(
        midi_events: list[list[Event]],
    ) -> list[list[Event]]:
        """Convert time-shift events to multiple minimal time-shift events.

        This simplifies the bar encoding process by breaking down time shifts
        into their smallest components.

        Args:
            midi_events: List of instrument event lists.

        Returns:
            MIDI events with time shifts converted to minimal length.
        """
        new_midi_events = []
        for inst_events in midi_events:
            new_inst_events = []
            for event in inst_events:
                if event.type == "Time-Shift":
                    values = split_dots(event.value)
                    # transfer values[0] to values[1]
                    values[1] += values[0] * values[2]
                    values[0] = 0
                    # generating and appending new time-shift events
                    while values[1] > 1:
                        values[1] -= 1
                        new_inst_events.append(Event("Time-Shift", "0.1." + str(values[2])))
                    event.value = ".".join(map(str, values))

                new_inst_events.append(event)
            new_midi_events.append(new_inst_events)
        return new_midi_events

    @staticmethod
    def add_bars(midi_events: list[list[Event]]) -> list[list[Event]]:
        """Add bar-start and bar-end events to MIDI events.

        Uses BEATS_PER_BAR constant to determine the bar length.

        Args:
            midi_events: List of instrument event lists.

        Returns:
            MIDI events with bar markers added.
        """
        new_midi_events = []
        for inst_events in midi_events:
            new_inst_events = [Event("Bar-Start", 0)]
            bar_index, beat_count = 0, 0
            bar_end = False
            for i, event in enumerate(inst_events):
                # when bar_end reached, adding the remainder note-off events
                # adding bar end event and bar start event
                # only if event is not the last event of the track
                if bar_end and i != len(inst_events) - 1:
                    if event.type == "Note-Off":
                        new_inst_events.append(event)
                        continue

                    else:
                        new_inst_events.append(Event("Bar-End", bar_index))
                        bar_index += 1
                        new_inst_events.append(Event("Bar-Start", bar_index))
                        bar_end = False

                # keeping track of the beat count within the bar
                if event.type == "Time-Shift":
                    beat_count += int_dec_base_to_beat(event.value)
                    if beat_count == BEATS_PER_BAR:
                        beat_count = 0
                        bar_end = True
                # default
                new_inst_events.append(event)
                # adding the last bar-end event
                if i == len(inst_events) - 1:
                    new_inst_events.append(Event("Bar-End", bar_index))

            new_midi_events.append(new_inst_events)
        return new_midi_events

    @staticmethod
    def combine_timeshifts_in_bar(midi_events: list[list[Event]]) -> list[list[Event]]:
        """Combine adjacent time-shifts within the same bar.

        Args:
            midi_events: List of instrument event lists.

        Returns:
            MIDI events with combined time shifts.
        """
        new_midi_events = []
        for inst_events in midi_events:
            new_inst_events = []
            aggregated_beats = 0
            for event in inst_events:
                # aggregating adjacent time-shifts and skipping them
                if event.type == "Time-Shift":
                    aggregated_beats += int_dec_base_to_beat(event.value)
                    continue
                # writting the aggregating time shift as a new event
                if aggregated_beats > 0:
                    new_inst_events.append(
                        Event("Time-Shift", beat_to_int_dec_base(aggregated_beats))
                    )
                    aggregated_beats = 0
                # default
                new_inst_events.append(event)
            new_midi_events.append(new_inst_events)
        return new_midi_events

    @staticmethod
    def remove_timeshifts_preceeding_bar_end(
        midi_events: list[list[Event]],
    ) -> list[list[Event]]:
        """Remove useless time-shifts preceding bar end events.

        Removes time-shifts when bars are empty or after the last event of a
        bar if there is a remainder time-shift. This helps reduce sequence length.

        Args:
            midi_events: List of instrument event lists.

        Returns:
            MIDI events with unnecessary time shifts removed.
        """
        verbose = False
        new_midi_events = []
        for inst_events in midi_events:
            new_inst_events = []
            for i, event in enumerate(inst_events):
                if (
                    i <= len(inst_events) - 1
                    and event.type == "Time-Shift"
                    and inst_events[i + 1].type == "Bar-End"
                ):
                    if verbose:
                        logger.debug("---- %d - %s ----", i, event)
                        for a in inst_events[i - 3 : i + 3]:
                            logger.debug("%s", a)
                    continue

                new_inst_events.append(event)
            new_midi_events.append(new_inst_events)

        return new_midi_events

    @staticmethod
    def add_density_to_bar(midi_events: list[list[Event]]) -> list[list[Event]]:
        """Add note density to each bar.

        For each bar, calculates the note density as the number of note onsets
        divided by the number of beats per bar, then adds it as a Bar-Density event.

        Args:
            midi_events: List of instrument event lists.

        Returns:
            MIDI events with density information added to each bar.
        """
        new_midi_events = []
        for inst_events in midi_events:
            new_inst_events = []
            for event in inst_events:
                if event.type == "Bar-Start":
                    note_onset_count_in_bar = 0  # initialize not count
                    new_inst_events.append(event)  # append Bar-Start event
                    temp_event_list = []  # initialize the temporary event list
                else:
                    temp_event_list.append(event)

                if event.type == "Note-On":
                    note_onset_count_in_bar += 1

                if event.type == "Bar-End":
                    new_inst_events.append(
                        Event(
                            "Bar-Density",
                            round(note_onset_count_in_bar / BEATS_PER_BAR),
                        )
                    )
                    for temp_event in temp_event_list:
                        new_inst_events.append(temp_event)

            new_midi_events.append(new_inst_events)
        return new_midi_events

    @staticmethod
    def define_instrument(midi_tok_instrument: Instrument, familize: bool = False) -> int | str:
        """Define the instrument token from the MIDI token instrument.

        Args:
            midi_tok_instrument: The miditoolkit Instrument object.
            familize: Whether the instrument needs to be familized.

        Returns:
            The instrument identifier (program number, family number, or "Drums").
        """
        # get program number
        instrument: int | str = (
            midi_tok_instrument.program if not midi_tok_instrument.is_drum else "Drums"
        )
        # familize instrument
        if familize and not midi_tok_instrument.is_drum:
            familizer = Familizer()
            family_number = familizer.get_family_number(int(instrument))
            if family_number is not None:
                instrument = family_number

        return instrument

    @staticmethod
    def initiate_track_in_section(instrument: int | str, track_index: int) -> list[Event]:
        """Initialize a track section with start and instrument events.

        Args:
            instrument: The instrument identifier (program number or "Drums").
            track_index: The index of the track.

        Returns:
            List of events starting a new track section.
        """
        section = [
            Event("Track-Start", track_index),
            Event("Instrument", instrument),
        ]
        return section

    @staticmethod
    def terminate_track_in_section(
        section: list[Event], track_index: int
    ) -> tuple[list[Event], int]:
        """Terminate a track section with an end event.

        Args:
            section: The current section event list.
            track_index: The current track index.

        Returns:
            Tuple of (updated section, incremented track index).
        """
        section.append(Event("Track-End", track_index))
        track_index += 1
        return section, track_index

    def make_sections(
        self,
        midi_events: list[list[Event]],
        instruments: list[Instrument],
        n_bar: int = 8,
    ) -> list[list[list[Event]]]:
        """Make sections of n_bar bars for each instrument.

        Creates midi_sections[inst_sections][sections] structure because files
        can be encoded in many sections of n_bar.

        Args:
            midi_events: List of instrument event lists.
            instruments: List of miditoolkit Instrument objects.
            n_bar: Number of bars per section. Defaults to 8.

        Returns:
            Nested list of sections per instrument.
        """
        midi_sections = []
        for i, inst_events in enumerate(midi_events):
            inst_section = []
            track_index = 0
            instrument = self.define_instrument(instruments[i], familize=self.familized)
            section = self.initiate_track_in_section(instrument, track_index)
            for ev_idx, event in enumerate(inst_events):
                section.append(event)
                if ev_idx == len(inst_events) - 1 or (
                    event.type == "Bar-End" and int(event.value + 1) % n_bar == 0
                ):
                    # finish the section with track-end event
                    section, track_index = self.terminate_track_in_section(section, track_index)
                    # append the section to the section list
                    inst_section.append(section)

                    # start new section if not the last event
                    if ev_idx < len(inst_events) - 1:
                        section = self.initiate_track_in_section(instrument, track_index)

            midi_sections.append(inst_section)

        return midi_sections

    @staticmethod
    def add_density_to_sections(
        midi_sections: list[list[list[Event]]],
    ) -> list[list[list[Event]]]:
        """Add density to each section as the mode of bar density.

        Args:
            midi_sections: Nested list of sections per instrument.

        Returns:
            Sections with density information added.
        """
        new_midi_sections = []
        for inst_sections in midi_sections:
            new_inst_sections = []
            for section in inst_sections:
                note_count_distribution = []
                for i, event in enumerate(section):
                    if event.type == "Instrument":
                        instrument_token_location = i
                    if event.type == "Bar-Density":
                        note_count_distribution.append(event.value)

                # add section density -> set to mode of bar density within that section
                density = stats.mode(
                    np.array(note_count_distribution).astype(np.int16), keepdims=False
                )[0]
                section.insert(instrument_token_location + 1, Event("Density", density))
                new_inst_sections.append(section)

            new_midi_sections.append(new_inst_sections)

        return new_midi_sections

    @staticmethod
    def sections_to_piece(midi_events: list[list[list[Event]]]) -> list[Event]:
        """Combine all sections into one piece.

        Sections are combined as follows:
        'Piece_Start
        Section 1 Instrument 1
        Section 1 Instrument 2
        Section 1 Instrument 3
        Section 2 Instrument 1
        ...'

        Args:
            midi_events: Nested list of sections per instrument.

        Returns:
            Flat list of events representing the complete piece.
        """
        piece: list[Event] = []
        max_total_sections = max(map(len, midi_events))
        for i in range(max_total_sections):
            # adding piece start event at the beggining of each section
            piece += [Event("Piece-Start", 1)]
            for inst_events in midi_events:
                nb_inst_section = len(inst_events)
                if i < nb_inst_section:
                    piece += inst_events[i]
        return piece

    @staticmethod
    def events_to_text(events: list[Event]) -> str:
        """Convert miditok events to text.

        Args:
            events: List of miditok Event objects.

        Returns:
            Text representation of the events.
        """
        text = ""
        current_instrument = "undefined"
        for event in events:
            # keeping track of the instrument to set the quantization in get_text()
            if event.type == "Instrument":
                current_instrument = str(event.value)

            text += get_text(event, current_instrument)
        return text

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

    def get_piece_sections(self, midi: MidiFile) -> list[list[list[Event]]]:
        """Get piece sections from a MIDI file.

        Modifies the miditok events to our needs: removes velocity, adds bars,
        density and makes sections for training and generation.

        Args:
            midi: The MidiFile object to process.

        Returns:
            List (instruments) of lists (sections) of miditok events.
        """
        midi_events = self.get_midi_events(midi)

        piece_sections = chain(
            midi_events,
            [
                self.remove_velocity,
                self.set_timeshifts_to_min_length,
                self.add_bars,
                self.combine_timeshifts_in_bar,
                self.remove_timeshifts_preceeding_bar_end,
                self.add_density_to_bar,
                self.make_sections,
                self.add_density_to_sections,
            ],
            midi.instruments,
        )

        return piece_sections

    def get_piece_text(self, midi: MidiFile) -> str:
        """Convert a MIDI file to text representation.

        The text is organized in sections of 8 bars of instrument.

        Args:
            midi: The MidiFile object to process.

        Returns:
            Text representation of the MIDI piece.
        """
        piece_text = chain(
            midi,
            [
                self.get_piece_sections,
                self.sections_to_piece,
                self.events_to_text,
            ],
            midi.instruments,
        )

        return piece_text

    def get_text_by_section(self, midi: MidiFile) -> list[str]:
        """Get text representation organized by section.

        Args:
            midi: The MidiFile object to process.

        Returns:
            List of text strings, one per section.
        """
        sectioned_instruments = self.get_piece_sections(midi)
        max_sections = max(list(map(len, sectioned_instruments)))
        sections_as_text = ["" for _ in range(max_sections)]

        for sections in sectioned_instruments:
            for idx in range(max_sections):
                with contextlib.suppress(IndexError):
                    sections_as_text[idx] += self.events_to_text(sections[idx])

        return sections_as_text


def from_midi_to_sectioned_text(midi_filename: str, familized: bool = False) -> str:
    """Convert a MIDI file to a MidiText input prompt.

    Args:
        midi_filename: Path to the MIDI file (without .mid extension).
        familized: Whether to familize instruments. Defaults to False.

    Returns:
        Text representation of the MIDI file.
    """
    from miditoolkit import MidiFile

    midi = MidiFile(f"{midi_filename}.mid")
    midi_like = get_miditok()
    piece_text = MIDIEncoder(midi_like, familized=familized).get_piece_text(midi)
    return piece_text


# Backward compatibility alias (deprecated, use from_midi_to_sectioned_text instead)
_from_midi_to_sectionned_text = from_midi_to_sectioned_text


if __name__ == "__main__":
    # Encode Strokes for debugging purposes:
    # midi_filename = "midi/the_strokes-reptilia"
    midi_filename = "source/tests/20230306_140430"
    piece_text = from_midi_to_sectioned_text(f"{midi_filename}")
    writeToFile(f"{midi_filename}.txt", piece_text)
