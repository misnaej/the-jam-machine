# fmt: off
# Instrument mapping and mapping functions
INSTRUMENT_CLASSES = [
    {"name": "Piano", "program_range": range(0, 8), "family_number": 0},
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
    {"name": "Sound Effects", "program_range": range(120, 128), "family_number": 15,},
]
# fmt: on

# Instrument mapping for decodiing our midi sequence into midi instruments of our choice
INSTRUMENT_TRANSFER_CLASSES = [
    {
        "name": "Piano",
        "program_range": [4],  # Electric Piano 1
        "family_number": 0,
    },
    {
        "name": "Chromatic Percussion",
        "program_range": [11],  # Vibraphone
        "family_number": 1,
    },
    {"name": "Organ", "program_range": [17], "family_number": 2},  # Percussive Organ
    {
        "name": "Guitar",
        "program_range": [80],  # Synth Lead Square
        "family_number": 3,
    },
    {
        "name": "Bass",
        "program_range": [38],  # Synth bass 1,
        "family_number": 4,
    },
    {
        "name": "Strings",
        "program_range": [50],  # Synth Strings 1
        "family_number": 5,
    },
    {
        "name": "Ensemble",
        "program_range": [51],  # Synth Strings 2
        "family_number": 6,
    },
    {
        "name": "Brass",
        "program_range": [63],  # 63 Synth Brass 1,
        "family_number": 7,
    },
    {"name": "Reed", "program_range": [64], "family_number": 8},  # Synth Brass 2
    {"name": "Pipe", "program_range": [82], "family_number": 9},  #  Lead 3
    {
        "name": "Synth Lead",
        "program_range": [81],  # Synth Lead Sawtooth
        "family_number": 10,
    },
    {"name": "Synth Pad", "program_range": range(88, 96), "family_number": 11},
    {"name": "Synth Effects", "program_range": range(96, 104), "family_number": 12},
    {"name": "Ethnic", "program_range": range(104, 112), "family_number": 13},
    {"name": "Percussive", "program_range": range(112, 120), "family_number": 14},
    {
        "name": "Sound Effects",
        "program_range": range(120, 128),
        "family_number": 15,
    },
]
