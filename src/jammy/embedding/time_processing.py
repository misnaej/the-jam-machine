"""Time-shift processing for MIDI event sequences."""

from __future__ import annotations

import logging

from miditok import Event

from jammy.midi_codec import beat_to_int_dec_base, int_dec_base_to_beat, split_dots

logger = logging.getLogger(__name__)


def remove_velocity(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Remove velocity events from MIDI events.

    Args:
        midi_events: List of instrument event lists.

    Returns:
        MIDI events with velocity events removed.
    """
    return [
        [event for event in inst_events if event.type != "Velocity"] for inst_events in midi_events
    ]


def normalize_timeshifts(midi_events: list[list[Event]]) -> list[list[Event]]:
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
                # split_dots returns [integer_part, decimal_part, base]
                # Convert integer beats into decimal units: e.g., 1.2.8 -> 0.10.8
                values = split_dots(str(event.value))
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
        aggregated_beats: float = 0
        for event in inst_events:
            # aggregating adjacent time-shifts and skipping them
            if event.type == "Time-Shift":
                aggregated_beats += int_dec_base_to_beat(str(event.value))
                continue
            # writing the aggregated time shift as a new event
            if aggregated_beats > 0:
                new_inst_events.append(Event("Time-Shift", beat_to_int_dec_base(aggregated_beats)))
                aggregated_beats = 0
            # default
            new_inst_events.append(event)
        new_midi_events.append(new_inst_events)
    return new_midi_events


def remove_timeshifts_preceding_bar_end(
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
    new_midi_events = []
    for inst_events in midi_events:
        new_inst_events = []
        for i, event in enumerate(inst_events):
            if (
                i < len(inst_events) - 1
                and event.type == "Time-Shift"
                and inst_events[i + 1].type == "Bar-End"
            ):
                continue

            new_inst_events.append(event)
        new_midi_events.append(new_inst_events)

    return new_midi_events
