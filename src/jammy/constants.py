from __future__ import annotations

# fmt: off
# Instrument mapping and mapping functions
INSTRUMENT_CLASSES = [
    {"name": "Piano", "program_range": range(8), "family_number": 0},
    {"name": "Chromatic Percussion", "program_range": range(8, 16), "family_number": 1},
    {"name": "Organ", "program_range": range(16, 24), "family_number": 2},
    {"name": "Guitar", "program_range": range(24, 32), "family_number": 3},
    {"name": "Bass", "program_range": range(32, 40), "family_number": 4},
    {"name": "Strings", "program_range": range(40, 48), "family_number": 5},
    {"name": "Ensemble", "program_range": range(48, 56), "family_number": 6},
    {"name": "Brass", "program_range": range(56, 64), "family_number": 7},
    {"name": "Reed", "program_range": range(64, 72), "family_number": 8},
    {"name": "Pipe", "program_range": range(72, 80), "family_number": 9},
    {"name": "Synth Lead", "program_range": range(80, 88), "family_number": 10},
    {"name": "Synth Pad", "program_range": range(88, 96), "family_number": 11},
    {"name": "Synth Effects", "program_range": range(96, 104), "family_number": 12},
    {"name": "Ethnic", "program_range": range(104, 112), "family_number": 13},
    {"name": "Percussive", "program_range": range(112, 120), "family_number": 14},
    {"name": "Sound Effects", "program_range": range(120, 128), "family_number": 15},
]
# fmt: on

# Instrument mapping for decodiing our midi sequence into midi instruments of our choice
INSTRUMENT_TRANSFER_CLASSES = [
    {
        "name": "Piano",
        "program_range": [4],
        "family_number": 0,
        "transfer_to": "Electric Piano 1",
    },
    {
        "name": "Chromatic Percussion",
        "program_range": [11],
        "family_number": 1,
        "transfer_to": "Vibraphone",
    },
    {
        "name": "Organ",
        "program_range": [17],
        "family_number": 2,
        "transfer_to": "Percussive Organ",
    },
    {
        "name": "Guitar",
        "program_range": [80],
        "family_number": 3,
        "transfer_to": "Synth Lead Square",
    },
    {
        "name": "Bass",
        "program_range": [38],
        "family_number": 4,
        "transfer_to": "Synth Bass 1",
    },
    {
        "name": "Strings",
        "program_range": [50],
        "family_number": 5,
        "transfer_to": "Synth Strings 1",
    },
    {
        "name": "Ensemble",
        "program_range": [51],
        "family_number": 6,
        "transfer_to": "Synth Strings 2",
    },
    {
        "name": "Brass",
        "program_range": [63],
        "family_number": 7,
        "transfer_to": "Synth Brass 1",
    },
    {
        "name": "Reed",
        "program_range": [64],
        "family_number": 8,
        "transfer_to": "Synth Brass 2",
    },
    {
        "name": "Pipe",
        "program_range": [82],
        "family_number": 9,
        "transfer_to": "Synth Lead Calliope",
    },
    {
        "name": "Synth Lead",
        "program_range": [81],  # Synth Lead Sawtooth
        "family_number": 10,
        "transfer_to": "Synth Lead Sawtooth",
    },
    {
        "name": "Synth Pad",
        "program_range": range(88, 96),
        "family_number": 11,
        "transfer_to": "Synth Pad",
    },
    {
        "name": "Synth Effects",
        "program_range": range(96, 104),
        "family_number": 12,
        "transfer_to": "Synth Effects",
    },
    {
        "name": "Ethnic",
        "program_range": range(104, 112),
        "family_number": 13,
        "transfer_to": "Ethnic",
    },
    {
        "name": "Percussive",
        "program_range": range(112, 120),
        "family_number": 14,
        "transfer_to": "Percussive",
    },
    {
        "name": "Sound Effects",
        "program_range": range(120, 128),
        "family_number": 15,
        "transfer_to": "Sound Effects",
    },
]


def get_instrument_class(program_number: int) -> dict | None:
    """Look up the instrument class for a MIDI program number.

    Args:
        program_number: MIDI program number (0-127).

    Returns:
        The matching instrument class dict, or None if not found.
    """
    for cls in INSTRUMENT_CLASSES:
        if program_number in cls["program_range"]:
            return cls
    return None


# Encoding and decoding constants

# NOTE: Both quantization values are currently identical (4).
# The distinction is preserved in case they need to diverge in the future.
DRUMS_BEAT_QUANTIZATION = 4  # 8th notes per beat
NONE_DRUMS_BEAT_QUANTIZATION = 4  # 4th notes per beat
BEATS_PER_BAR = 4  # 4/4 time

# HuggingFace model — the familized GPT-2 model trained on electronic music
MODEL_REPO = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
MODEL_REVISION = "95b3c0905f6a97fdc147776a5b53edaf651916e4"  # pinned 2022-12-17
