"""Track-level text manipulation utilities."""

from __future__ import annotations

from jammy.tokens import BAR_START, PIECE_START, TRACK_END, TRACK_START


def strip_track_ends(text: str) -> str:
    """Remove TRACK_END token from text.

    Args:
        text: Track text that may contain TRACK_END.

    Returns:
        Text with TRACK_END removed.
    """
    text = text.rstrip(" ")
    if text.endswith(TRACK_END):
        text = text[: -len(TRACK_END)]
    return text


def extract_tracks(piece_text: str) -> list[str]:
    """Split piece text into individual tracks.

    Args:
        piece_text: Full piece text with multiple tracks.

    Returns:
        List of track strings with TRACK_START/TRACK_END tokens.
    """
    parts = piece_text.split(f"{TRACK_START} ")[1:]
    return [f"{TRACK_START} {strip_track_ends(part)}{TRACK_END} " for part in parts]


def get_last_track(piece_text: str) -> str:
    """Get the last track from a piece.

    Args:
        piece_text: Full piece text with multiple tracks.

    Returns:
        The last track as a string.
    """
    return extract_tracks(piece_text)[-1]


def combine_tracks(track_list: list[str]) -> str:
    """Combine track list into a piece.

    Args:
        track_list: List of track strings.

    Returns:
        Combined piece text starting with PIECE_START.
    """
    piece = f"{PIECE_START} "
    for track in track_list:
        piece += track
    return piece


def get_new_content(full_text: str, prompt: str) -> str:
    """Extract newly generated content (full minus prompt).

    Args:
        full_text: Full generated text including prompt.
        prompt: The original prompt.

    Returns:
        Only the newly generated portion.
    """
    return full_text[len(prompt) :]


def extract_new_bar(prompt_plus_bar: str) -> str:
    """Extract the newly generated bar from generation output.

    Args:
        prompt_plus_bar: Full generation output with prompt and new bar.

    Returns:
        The new bar with BAR_START prefix.
    """
    stripped = strip_track_ends(prompt_plus_bar.split(f"{BAR_START} ")[-1])
    return f"{BAR_START} " + stripped
