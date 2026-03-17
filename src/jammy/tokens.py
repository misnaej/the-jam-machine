"""MIDI text token constants.

These tokens define the text representation of MIDI sequences and must
match the model's tokenizer vocabulary.
"""

from __future__ import annotations

# Structure tokens
PIECE_START = "PIECE_START"
TRACK_START = "TRACK_START"
TRACK_END = "TRACK_END"
BAR_START = "BAR_START"
BAR_END = "BAR_END"

# Note token prefixes
NOTE_ON = "NOTE_ON"
NOTE_OFF = "NOTE_OFF"
TIME_DELTA = "TIME_DELTA"

# Legacy token from raw MidiTok output (distinct from TIME_DELTA which is our
# quantized encoding). Only encountered when processing MidiTok-native data.
TIME_SHIFT = "TIME_SHIFT"

# Metadata prefixes
INST = "INST"
DENSITY = "DENSITY"

# Special values
DRUMS = "DRUMS"
UNK = "UNK"
