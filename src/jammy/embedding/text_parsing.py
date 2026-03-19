"""Text-to-event parsing for MIDI token sequences."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from miditok import Event

from jammy.midi_codec import get_beat_resolution, get_event
from jammy.tokens import BAR_START, INST, NOTE_ON, TIME_DELTA

logger = logging.getLogger(__name__)


def text_to_events(text: str, verbose: bool = False) -> list[Event]:
    """Convert text tokens to a list of MidiTok events.

    Args:
        text: Text token string to parse.
        verbose: Whether to log detailed quantization information.

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
        value = _event[1] if len(_event) > 1 else None
        beyond_quantization = False  # needs to be reset for each event

        if _event[0] == INST:
            bar_value = 0  # reset bar count for new instrument
            # get the instrument for passing in get_event when time_delta
            # for proper quantization
            instrument = get_event(_event[0], value).value

            # how much delta can be added before over quantization
            max_cumul_time_delta = get_beat_resolution(instrument) * 4

        if _event[0] == BAR_START:
            bar_value += 1
            value = bar_value
            # resetting cumul_time_delta
            cumul_time_delta = 0

        # ----- hack to prevent over quantization -----
        # NOT IDEAL - the model should not output these events
        if _event[0] == TIME_DELTA:
            cumul_time_delta += int(_event[1])
            if cumul_time_delta > max_cumul_time_delta:
                beyond_quantization = True
                cumul_time_delta -= int(_event[1])

        if _event[0] == NOTE_ON and cumul_time_delta >= max_cumul_time_delta:
            beyond_quantization = True

        if beyond_quantization and verbose:
            logger.debug(
                "instrument %s - bar %s - skipping %s because of over quantization",
                instrument,
                bar_value,
                _event[0],
            )
        # ---------------------------------------------

        # getting event
        event = get_event(_event[0], value, instrument)
        if event and not beyond_quantization:
            if event.type == "Bar-End":
                if verbose:
                    logger.debug(
                        "instrument %s - bar %s - Cumulated TIME_DELTA = %s",
                        instrument,
                        bar_value,
                        cumul_time_delta,
                    )
                cumul_time_delta = 0

            # appending event
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
        # creates a new entry in the dictionary when "Track-Start" event is encountered
        if event.type == "Track-Start":
            current_track = event.value
            if len(inst_events) == event.value:
                inst_events.append({})
                inst_events[current_track]["channel"] = current_track
                inst_events[current_track]["events"] = []
        # append event to the track
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
