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
