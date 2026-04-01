"""MIDI text encoding and decoding functions.

Converts between miditok Event objects and the text token format
used by the GPT-2 model.

Note: Encoding quantizes time to a fixed resolution (see
``DRUMS_BEAT_QUANTIZATION`` and ``NONE_DRUMS_BEAT_QUANTIZATION`` in
``constants.py``). Time offsets smaller than one quantization step
(e.g. near-simultaneous notes in guitar strums) are rounded to zero
and discarded. This is a lossy transformation — the decoded MIDI will
not perfectly reproduce the original timing at sub-quantization
resolution.
"""

from __future__ import annotations

from miditok import Event

from jammy.constants import DRUMS_BEAT_QUANTIZATION, NONE_DRUMS_BEAT_QUANTIZATION
from jammy.tokens import (
    BAR_END,
    BAR_START,
    DENSITY,
    DRUMS,
    INST,
    NOTE_OFF,
    NOTE_ON,
    PIECE_START,
    TIME_DELTA,
    TIME_SHIFT,
    TRACK_END,
    TRACK_START,
)

# --- Encoding mappings (Event type → text token) ---

# Event types that produce a bare token with no value (e.g. "PIECE_START ")
_EVENT_NO_VALUE: dict[str, str] = {
    "Piece-Start": PIECE_START,
    "Track-Start": TRACK_START,
    "Track-End": TRACK_END,
    "Bar-Start": BAR_START,
    "Bar-End": BAR_END,
}

# Event types that produce "TOKEN=value " format
_EVENT_WITH_VALUE: dict[str, str] = {
    "Density": DENSITY,
    "Note-On": NOTE_ON,
    "Note-Off": NOTE_OFF,
}

# --- Decoding mappings (text token → Event type) ---

# Simple token-to-event-type mapping (value passed through unchanged)
_TEXT_TO_EVENT_TYPE: dict[str, str] = {
    PIECE_START: "Piece-Start",
    TRACK_START: "Track-Start",
    TRACK_END: "Track-End",
    BAR_START: "Bar-Start",
    BAR_END: "Bar-End",
    TIME_SHIFT: "Time-Shift",
    NOTE_ON: "Note-On",
    NOTE_OFF: "Note-Off",
}


def get_beat_resolution(instrument: str) -> int:
    """Get the beat quantization resolution for an instrument.

    Args:
        instrument: The instrument type (case-insensitive "drums" or other).

    Returns:
        The beat quantization resolution.
    """
    if instrument.lower() == "drums":
        return DRUMS_BEAT_QUANTIZATION
    return NONE_DRUMS_BEAT_QUANTIZATION


def split_dots(value: str) -> list[int]:
    """Split a string separated by dots into a list of integers.

    Args:
        value: A dot-separated string like "a.b.c".

    Returns:
        A list of integers parsed from the string, e.g., [a, b, c].
    """
    return list(map(int, value.split(".")))


# Encoding functions


def int_dec_base_to_beat(beat_str: str) -> float:
    """Convert "integer.decimal.base" format to beats.

    Converts a string in miditok format to a float representing beats.
    For example, "0.4.8" = 0 + 4/8 = 0.5 beats.

    Args:
        beat_str: A string in "integer.decimal.base" format.

    Returns:
        The beat value as a float.
    """
    integer, decimal, base = split_dots(beat_str)
    return integer + decimal / base


def int_dec_base_to_delta(beat_str: str, instrument: str = "drums") -> int:
    """Convert time shift to time_delta according to encoding scheme.

    Drums TIME_DELTA are quantized according to DRUMS_BEAT_QUANTIZATION.
    Other instrument TIME_DELTA are quantized according to NONE_DRUMS_BEAT_QUANTIZATION.

    Args:
        beat_str: A string in "integer.decimal.base" format.
        instrument: The instrument type, used to determine quantization.

    Returns:
        The quantized time delta as an integer.
    """
    beat_res = get_beat_resolution(instrument)
    time_delta = int_dec_base_to_beat(beat_str) * beat_res
    return int(time_delta)


def get_text(event: Event, instrument: str = "drums") -> str:
    """Convert an event into a string for the midi-text format.

    Args:
        event: A miditok Event object to convert.
        instrument: The instrument type for time delta quantization.

    Returns:
        The text representation of the event.
    """
    # Bare tokens (no value)
    if event.type in _EVENT_NO_VALUE:
        return f"{_EVENT_NO_VALUE[event.type]} "

    # Tokens with "TOKEN=value" format
    if event.type in _EVENT_WITH_VALUE:
        return f"{_EVENT_WITH_VALUE[event.type]}={event.value} "

    # Special cases requiring custom logic
    if event.type == "Instrument":
        value = DRUMS if str(event.value).lower() == "drums" else event.value
        return f"{INST}={value} "

    if event.type == "Time-Shift":
        delta = int_dec_base_to_delta(event.value, instrument)
        return f"{TIME_DELTA}={delta} " if delta else ""

    return ""


# Decoding functions


def time_delta_to_beat(time_delta: int | str, instrument: str = "drums") -> float:
    """Convert TIME_DELTA to beats according to encoding scheme.

    Args:
        time_delta: The time delta value from midi-text.
        instrument: The instrument type ("Drums" or other), used to determine
            the quantization resolution defined in constants.py.

    Returns:
        The beat value as a float.
    """
    beat_res = get_beat_resolution(instrument)
    return float(time_delta) / beat_res


def beat_to_int_dec_base(beat: float, beat_res: int = 8) -> str:
    """Convert beats into "integer.decimal.base" format for miditok.

    Args:
        beat: The beat value as a float.
        beat_res: The beat resolution (default 8).

    Returns:
        A string in "integer.decimal.base" format.
        For example, 0.5 beats with resolution 8 becomes "0.4.8".
    """
    int_dec_base = [
        int((beat * beat_res) // beat_res),
        int((beat * beat_res) % beat_res),
        beat_res,
    ]
    return ".".join(map(str, int_dec_base))


def time_delta_to_int_dec_base(time_delta: int | str, instrument: str = "drums") -> str:
    """Convert TIME_DELTA to "integer.decimal.base" format.

    Args:
        time_delta: The time delta value from midi-text.
        instrument: The instrument type for quantization.

    Returns:
        A string in "integer.decimal.base" format.
    """
    beat = time_delta_to_beat(time_delta, instrument)
    return beat_to_int_dec_base(beat)


def get_event(text: str, value: str | None = None, instrument: str = "drums") -> Event | None:
    """Convert a midi-text token into a miditok Event.

    Args:
        text: The event type text (e.g., "PIECE_START", "NOTE_ON").
        value: The optional value associated with the event.
        instrument: The instrument type for time delta conversion.

    Returns:
        A miditok Event object, or None if the text is not recognized.
    """
    # Simple mappings (value passed through unchanged)
    if text in _TEXT_TO_EVENT_TYPE:
        return Event(_TEXT_TO_EVENT_TYPE[text], value)

    # Special cases requiring custom logic
    if text == INST:
        if value == DRUMS:
            value = "Drums"
        return Event("Instrument", value)

    if text == TIME_DELTA:
        if value is not None and int(value) == 0:
            return None  # skip zero time shifts
        if value is None:
            return None
        return Event("Time-Shift", time_delta_to_int_dec_base(value, instrument))

    return None
