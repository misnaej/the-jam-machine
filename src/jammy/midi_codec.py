"""MIDI text encoding and decoding functions.

Converts between miditok Event objects and the text token format
used by the GPT-2 model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from miditok import Event


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
    match event.type:
        case "Piece-Start":
            return f"{PIECE_START} "
        case "Track-Start":
            return f"{TRACK_START} "
        case "Track-End":
            return f"{TRACK_END} "
        case "Instrument":
            if str(event.value).lower() == "drums":
                return f"{INST}={DRUMS} "
            else:
                return f"{INST}={event.value} "
        case "Density":
            return f"{DENSITY}={event.value} "
        case "Bar-Start":
            return f"{BAR_START} "
        case "Bar-End":
            return f"{BAR_END} "
        case "Time-Shift":
            return f"{TIME_DELTA}={int_dec_base_to_delta(event.value, instrument)} "
        case "Note-On":
            return f"{NOTE_ON}={event.value} "
        case "Note-Off":
            return f"{NOTE_OFF}={event.value} "
        case _:
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
    beats = float(time_delta) / beat_res
    return beats


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
    """Convert a midi-text like event into a miditok like event.

    Uses if/elif instead of match/case because the comparisons are against
    imported module variables (e.g. PIECE_START), which match/case treats
    as capture patterns rather than value comparisons.

    Args:
        text: The event type text (e.g., "PIECE_START", "NOTE_ON").
        value: The optional value associated with the event.
        instrument: The instrument type for time delta conversion.

    Returns:
        A miditok Event object, or None if the text is not recognized.
    """
    from miditok import Event

    if text == PIECE_START:
        return Event("Piece-Start", value)
    elif text == TRACK_START:
        return Event("Track-Start", value)
    elif text == TRACK_END:
        return Event("Track-End", value)
    elif text == INST:
        if value == DRUMS:
            value = "Drums"
        return Event("Instrument", value)
    elif text == BAR_START:
        return Event("Bar-Start", value)
    elif text == BAR_END:
        return Event("Bar-End", value)
    elif text == TIME_SHIFT:
        return Event("Time-Shift", value)
    elif text == TIME_DELTA:
        return Event("Time-Shift", time_delta_to_int_dec_base(value, instrument))
    elif text == NOTE_ON:
        return Event("Note-On", value)
    elif text == NOTE_OFF:
        return Event("Note-Off", value)
    else:
        return None
