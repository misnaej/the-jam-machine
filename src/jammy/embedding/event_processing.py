"""Event processing and transformation for MIDI decoding."""

from __future__ import annotations

import logging
from typing import Any

from miditok import Event

from jammy.midi_codec import beat_to_int_dec_base, int_dec_base_to_beat

logger = logging.getLogger(__name__)


def check_for_duplicated_events(event_list: list[Event]) -> None:
    """Check for and log any duplicate consecutive events.

    Logs a warning for each pair of duplicate consecutive events found.
    Does not modify the event list or raise exceptions.

    Args:
        event_list: List of MidiTok Event objects to check.
    """
    for i, event in enumerate(event_list):
        if (
            i < len(event_list) - 1
            and event.type == event_list[i + 1].type
            and event.value == event_list[i + 1].value
        ):
            logger.warning("Duplicate event found at index %s : %s", i, event)


def add_missing_timeshifts_in_bar(
    inst_events: list[dict[str, Any]],
    beat_per_bar: int = 4,
    *,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Add missing time shifts in bar to ensure each bar has 4 beats.

    Handles the problem of a missing time shift if notes do not last until
    the end of the bar, and handles empty bars defined only by BAR_START BAR_END.

    Args:
        inst_events: List of instrument event dictionaries.
        beat_per_bar: Number of beats per bar (default 4).
        verbose: Whether to log detailed information.

    Returns:
        New list of instrument events with corrected time shifts.
    """
    new_inst_events: list[dict[str, Any]] = []
    for index, inst_event in enumerate(inst_events):
        new_inst_events.append({})
        new_inst_events[index]["Instrument"] = inst_event["Instrument"]
        new_inst_events[index]["channel"] = index
        new_inst_events[index]["events"] = []

        beat_count = 0
        for event in inst_event["events"]:
            if event.type == "Bar-Start":
                beat_count = 0

            if event.type == "Time-Shift":
                beat_count += int_dec_base_to_beat(event.value)

            if event.type == "Bar-End" and beat_count < beat_per_bar:
                time_shift_to_add = beat_to_int_dec_base(beat_per_bar - beat_count)
                new_inst_events[index]["events"].append(Event("Time-Shift", time_shift_to_add))
                beat_count += int_dec_base_to_beat(time_shift_to_add)

            if event.type == "Bar-End" and verbose:
                logger.debug(
                    "Instrument %s - %s - Bar %s - beat_count = %s",
                    index,
                    inst_event["Instrument"],
                    event.value,
                    beat_count,
                )
            if event.type == "Bar-End" and beat_count > beat_per_bar:
                logger.warning(
                    "Instrument %s - %s - Bar %s - Beat count exceeded",
                    index,
                    inst_event["Instrument"],
                    event.value,
                )
            new_inst_events[index]["events"].append(event)

    return new_inst_events


def remove_unwanted_tokens(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Remove structural tokens not needed for MIDI conversion.

    Removes Bar-Start, Bar-End, Track-Start, Track-End, Piece-Start,
    and Instrument events.

    Args:
        events: List of instrument event dictionaries.

    Returns:
        Modified list with unwanted tokens removed.
    """
    unwanted = {"Bar-Start", "Bar-End", "Track-Start", "Track-End", "Piece-Start", "Instrument"}
    for inst_index, inst_event in enumerate(events):
        events[inst_index]["events"] = [
            event for event in inst_event["events"] if event.type not in unwanted
        ]
    return events


def _add_timeshifts(beat_values1: str, beat_values2: str) -> str:
    """Add two beat values in integer.decimal.base format.

    Args:
        beat_values1: First beat value (e.g., "0.3.8").
        beat_values2: Second beat value (e.g., "1.7.8").

    Returns:
        Sum of beat values (e.g., "2.2.8" for the example values).
    """
    value1 = int_dec_base_to_beat(beat_values1)
    value2 = int_dec_base_to_beat(beat_values2)
    return beat_to_int_dec_base(value1 + value2)


def aggregate_timeshifts(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aggregate consecutive time shift events.

    Combines consecutive Time-Shift events into single events that may
    span more than a bar (e.g., Timeshift 4.0.8).

    Args:
        events: List of instrument event dictionaries.

    Returns:
        Modified list with aggregated time shifts.
    """
    for inst_index, inst_event in enumerate(events):
        new_inst_event = []
        for event in inst_event["events"]:
            if (
                event.type == "Time-Shift"
                and len(new_inst_event) > 0
                and new_inst_event[-1].type == "Time-Shift"
            ):
                new_inst_event[-1].value = _add_timeshifts(new_inst_event[-1].value, event.value)
            else:
                new_inst_event.append(event)

        events[inst_index]["events"] = new_inst_event
    return events


def add_velocity(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add default velocity to note events.

    Adds velocity 99 to note events since they are removed from text
    but needed to generate MIDI.

    Args:
        events: List of instrument event dictionaries.

    Returns:
        Modified list with velocity events added after Note-On events.
    """
    for inst_index, inst_event in enumerate(events):
        new_inst_event = []
        for event in inst_event["events"]:
            new_inst_event.append(event)
            if event.type == "Note-On":
                new_inst_event.append(Event("Velocity", 99))
        events[inst_index]["events"] = new_inst_event
    return events
