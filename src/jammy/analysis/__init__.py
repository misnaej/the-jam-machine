"""Model analysis and visualization tools.

Educational visualizations for understanding how the GPT-2 model
represents and generates MIDI music.
"""

from __future__ import annotations

TOKEN_COLORS: dict[str, str] = {
    "structure": "#9C27B0",  # purple
    "instrument": "#2196F3",  # blue
    "note": "#212121",  # near-black
    "time": "#F44336",  # red
    "density": "#4CAF50",  # green
    "special": "#9E9E9E",  # grey
}

TOKEN_CATEGORY_ORDER = ["structure", "instrument", "density", "note", "time", "special"]

# All plotly charts rely on the CDN script loaded in the page header
PLOTLY_JS: bool = False

# Default sequences for visualizations (different lengths for different plots)
DEFAULT_SEQUENCE_SHORT = "PIECE_START TRACK_START INST=DRUMS DENSITY=2 BAR_START"

DEFAULT_SEQUENCE_MEDIUM = (
    "PIECE_START TRACK_START INST=DRUMS DENSITY=2 BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36"
)

DEFAULT_SEQUENCE_LONG = (
    "PIECE_START TRACK_START INST=DRUMS DENSITY=2"
    " BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36"
    " NOTE_ON=42 TIME_DELTA=4 NOTE_OFF=42 BAR_END"
)


def categorize_token(token: str) -> str:
    """Categorize a token string into its type.

    Args:
        token: Token string (e.g. "NOTE_ON=60", "INST=DRUMS", "BAR_START").

    Returns:
        Category name: "structure", "instrument", "density", "note", "time", or "special".
    """
    if any(prefix in token for prefix in ("PIECE", "TRACK", "BAR")):
        return "structure"
    if "INST" in token:
        return "instrument"
    if "DENSITY" in token:
        return "density"
    if "NOTE" in token:
        return "note"
    if "TIME" in token or "DELTA" in token:
        return "time"
    return "special"
