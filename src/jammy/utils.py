"""Generic utility functions.

Domain-specific utilities have been moved to focused modules:
- MIDI encoding/decoding: ``jammy.midi_codec``
- File I/O and compression: ``jammy.file_utils``
"""

from __future__ import annotations

import functools
from datetime import datetime
from typing import TYPE_CHECKING

from miditok import MIDILike

if TYPE_CHECKING:
    from collections.abc import Sequence


def index_has_substring(items: Sequence[str], substring: str) -> int:
    """Find the index of the first item containing a substring.

    Args:
        items: A sequence of strings to search through.
        substring: The substring to search for.

    Returns:
        The index of the first item containing the substring, or -1 if not found.
    """
    for i, s in enumerate(items):
        if substring in s:
            return i
    return -1


@functools.lru_cache(maxsize=1)
def get_miditok() -> MIDILike:
    """Create and return a MIDILike tokenizer instance.

    Returns:
        A configured MIDILike tokenizer with full pitch range and 8th note resolution.
    """
    pitch_range = range(0, 127)  # was (21, 109)
    beat_res = {(0, 400): 8}
    return MIDILike(pitch_range, beat_res)


def compute_list_average(values: Sequence[float]) -> float:
    """Compute the arithmetic average of a sequence of numbers.

    Args:
        values: A sequence of numeric values.

    Returns:
        The arithmetic mean of the values.
    """
    return sum(values) / len(values)


def get_datetime() -> str:
    """Get the current datetime as a formatted string.

    Returns:
        The current datetime in YYYYMMDD_HHMMSS format.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")
