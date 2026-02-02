"""Track-level text manipulation utilities."""

from __future__ import annotations


class TrackBuilder:
    """Handles track-level text operations for MIDI text format.

    This class provides static methods for parsing and manipulating
    track text in the MIDI text format used by the generation model.
    """

    @staticmethod
    def strip_track_ends(text: str) -> str:
        """Remove TRACK_END token from text.

        Args:
            text: Track text that may contain TRACK_END.

        Returns:
            Text with TRACK_END removed.
        """
        if "TRACK_END" in text:
            text = text.rstrip(" ").rstrip("TRACK_END")
        return text

    @staticmethod
    def extract_tracks(piece_text: str) -> list[str]:
        """Split piece text into individual tracks.

        Args:
            piece_text: Full piece text with multiple tracks.

        Returns:
            List of track strings with TRACK_START/TRACK_END tokens.
        """
        stripped = TrackBuilder.strip_track_ends(piece_text.split("TRACK_START ")[1::])
        return [f"TRACK_START {track}TRACK_END " for track in stripped]

    @staticmethod
    def get_last_track(piece_text: str) -> str:
        """Get the last track from a piece.

        Args:
            piece_text: Full piece text with multiple tracks.

        Returns:
            The last track as a string.
        """
        return TrackBuilder.extract_tracks(piece_text)[-1]

    @staticmethod
    def combine_tracks(track_list: list[str]) -> str:
        """Combine track list into a piece.

        Args:
            track_list: List of track strings.

        Returns:
            Combined piece text starting with PIECE_START.
        """
        piece = "PIECE_START "
        for track in track_list:
            piece += track
        return piece

    @staticmethod
    def get_new_content(full_text: str, prompt: str) -> str:
        """Extract newly generated content (full minus prompt).

        Args:
            full_text: Full generated text including prompt.
            prompt: The original prompt.

        Returns:
            Only the newly generated portion.
        """
        return full_text[len(prompt) :]

    @staticmethod
    def extract_new_bar(prompt_plus_bar: str) -> str:
        """Extract the newly generated bar from generation output.

        Args:
            prompt_plus_bar: Full generation output with prompt and new bar.

        Returns:
            The new bar with BAR_START prefix.
        """
        stripped = TrackBuilder.strip_track_ends(prompt_plus_bar.split("BAR_START ")[-1])
        return "BAR_START " + stripped
