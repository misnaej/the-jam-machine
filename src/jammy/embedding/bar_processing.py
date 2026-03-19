"""Bar marker and density processing for MIDI event sequences."""

from __future__ import annotations

import numpy as np
from miditok import Event
from scipy import stats

from jammy.constants import BEATS_PER_BAR
from jammy.midi_codec import int_dec_base_to_beat


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


def add_density_to_bar(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Add note density to each bar.

    For each bar, calculates the note density as the number of note onsets
    divided by the number of beats per bar, then adds it as a Bar-Density event.

    Each instrument's event list must begin with a Bar-Start event (as produced
    by ``add_bars``).

    Args:
        midi_events: List of instrument event lists.

    Returns:
        MIDI events with density information added to each bar.
    """
    new_midi_events = []
    for inst_events in midi_events:
        new_inst_events = []
        note_onset_count_in_bar = 0
        temp_event_list: list[Event] = []
        for event in inst_events:
            if event.type == "Bar-Start":
                note_onset_count_in_bar = 0
                new_inst_events.append(event)
                temp_event_list = []
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


def add_density_to_sections(
    midi_sections: list[list[list[Event]]],
) -> list[list[list[Event]]]:
    """Add density to each section as the mode of bar density.

    Each section must contain at least one Instrument event and one
    Bar-Density event (as produced by ``section_building.make_sections``
    and ``add_density_to_bar``).

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
            instrument_token_location: int | None = None
            for i, event in enumerate(section):
                if event.type == "Instrument":
                    instrument_token_location = i
                if event.type == "Bar-Density":
                    note_count_distribution.append(event.value)

            if instrument_token_location is None:
                new_inst_sections.append(section)
                continue

            # add section density -> set to mode of bar density within that section
            density = stats.mode(
                np.array(note_count_distribution).astype(np.int16), keepdims=False
            )[0]
            new_section = [
                *section[: instrument_token_location + 1],
                Event("Density", density),
                *section[instrument_token_location + 1 :],
            ]
            new_inst_sections.append(new_section)

        new_midi_sections.append(new_inst_sections)

    return new_midi_sections
