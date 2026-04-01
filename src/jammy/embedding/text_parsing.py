"""Text-to-event parsing for MIDI token sequences."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from miditok import Event

from jammy.midi_codec import get_beat_resolution, get_event
from jammy.tokens import BAR_START, INST, NOTE_ON, TIME_DELTA

logger = logging.getLogger(__name__)


def _is_beyond_quantization(
    event_type: str,
    event_value: str | None,
    cumul_time_delta: int,
    max_cumul_time_delta: int,
) -> tuple[bool, int]:
    """Check if an event exceeds the quantization limit for the current bar.

    Args:
        event_type: The token type (e.g. TIME_DELTA, NOTE_ON).
        event_value: The token value (e.g. "4").
        cumul_time_delta: Accumulated time delta in the current bar.
        max_cumul_time_delta: Maximum allowed cumulative time delta.

    Returns:
        Tuple of (beyond_quantization, updated_cumul_time_delta).
    """
    if event_type == TIME_DELTA and event_value is not None:
        delta = int(event_value)
        cumul_time_delta += delta
        if cumul_time_delta > max_cumul_time_delta:
            cumul_time_delta -= delta
            return True, cumul_time_delta

    if event_type == NOTE_ON and cumul_time_delta >= max_cumul_time_delta:
        return True, cumul_time_delta

    return False, cumul_time_delta


def text_to_events(text: str) -> list[Event]:
    """Convert text tokens to a list of MidiTok events.

    Args:
        text: Text token string to parse.

    Returns:
        List of MidiTok Event objects.
    """
    events: list[Event] = []
    instrument = "drums"
    bar_value = 0
    cumul_time_delta = 0
    max_cumul_time_delta = 0

    for word in text.split(" "):
        _event = word.split("=")
        raw_value = _event[1] if len(_event) > 1 else None
        value = raw_value

        if _event[0] == INST:
            bar_value = 0
            inst_event = get_event(_event[0], value)
            if inst_event is not None:
                instrument = str(inst_event.value)
            else:
                logger.debug("Unknown instrument token: %s", value)
            max_cumul_time_delta = get_beat_resolution(instrument) * 4

        if _event[0] == BAR_START:
            bar_value += 1
            value = str(bar_value)
            cumul_time_delta = 0

        beyond, cumul_time_delta = _is_beyond_quantization(
            _event[0],
            raw_value,
            cumul_time_delta,
            max_cumul_time_delta,
        )

        if beyond:
            logger.debug(
                "instrument %s - bar %s - skipping %s because of over quantization",
                instrument,
                bar_value,
                _event[0],
            )
            continue

        event = get_event(_event[0], value, instrument)
        if event:
            if event.type == "Bar-End":
                logger.debug(
                    "instrument %s - bar %s - Cumulated TIME_DELTA = %s",
                    instrument,
                    bar_value,
                    cumul_time_delta,
                )
                cumul_time_delta = 0
            events.append(event)

    return events


def get_track_ids(events: list[Event]) -> list[Event]:
    """Add track IDs to track start and end events.

    Args:
        events: List of MidiTok Event objects.

    Returns:
        Modified list of events with track IDs assigned.
    """
    track_id = 0
    for i, event in enumerate(events):
        if event.type == "Track-Start":
            events[i].value = track_id
        if event.type == "Track-End":
            events[i].value = track_id
            track_id += 1
    return events


def piece_to_inst_events(piece_events: list[Event]) -> list[dict[str, Any]]:
    """Convert piece events to instrument-grouped events.

    Args:
        piece_events: List of events with Notes, Timeshifts, Bars, Tracks.

    Returns:
        List of dictionaries, each containing 'Instrument', 'channel',
        and 'events' keys for one instrument.
    """
    inst_events: list[dict[str, Any]] = []
    current_track = -1  # so does not start before Track-Start is encountered
    for event in piece_events:
        if event.type == "Track-Start":
            current_track = event.value
            if len(inst_events) == event.value:
                inst_events.append({})
                inst_events[current_track]["channel"] = current_track
                inst_events[current_track]["events"] = []
        if current_track != -1:
            inst_events[current_track]["events"].append(event)

        if event.type == "Instrument":
            inst_events[current_track]["Instrument"] = event.value
    return inst_events


def get_bar_ids(inst_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Track bar index for each instrument and save them in the MidiTok Events.

    Args:
        inst_events: List of instrument event dictionaries.

    Returns:
        Modified list with bar IDs assigned to bar events.
    """
    for inst_index, inst_event in enumerate(inst_events):
        bar_idx = 0
        for event_index, event in enumerate(inst_event["events"]):
            if event.type in ("Bar-Start", "Bar-End"):
                inst_events[inst_index]["events"][event_index].value = bar_idx
            if event.type == "Bar-End":
                bar_idx += 1
    return inst_events
