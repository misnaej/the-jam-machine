"""Piece state management for multi-track music generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from jammy.tokens import BAR_START, PIECE_START, TRACK_END, TRACK_START

from .track_builder import strip_track_ends

if TYPE_CHECKING:
    from .config import TrackConfig


class PieceBuilder:
    """Manages the piece_by_track state dictionary.

    This class handles the storage and manipulation of track data
    during the music generation process.

    Attributes:
        piece_by_track: List of track dictionaries containing instrument,
            density, temperature, and bars data.
    """

    def __init__(self, piece_by_track: list[dict[str, Any]] | None = None) -> None:
        """Initialize the piece builder.

        Args:
            piece_by_track: Optional existing piece state to restore.
        """
        self.piece_by_track: list[dict[str, Any]] = piece_by_track if piece_by_track else []

    def init_track(
        self,
        instrument: str,
        density: int,
        temperature: float,
    ) -> None:
        """Initialize a new track in the piece.

        Args:
            instrument: The instrument identifier.
            density: Note density level (1-3).
            temperature: Generation temperature for this track.
        """
        label = len(self.piece_by_track)
        self.piece_by_track.append(
            {
                "label": f"track_{label}",
                "instrument": instrument,
                "density": density,
                "temperature": temperature,
                "bars": [],
            }
        )

    def add_bars_to_track(self, track_id: int, bars_text: str) -> None:
        """Add generated bars to an existing track.

        Args:
            track_id: Index of the track to add bars to.
            bars_text: Text containing one or more bars.
        """
        stripped = strip_track_ends(bars_text)
        for bar in stripped.split(f"{BAR_START} "):
            if bar == "":
                continue
            if TRACK_START in bar:
                self.piece_by_track[track_id]["bars"].append(bar)
            else:
                self.piece_by_track[track_id]["bars"].append(f"{BAR_START} " + bar)

    def get_track(self, track_id: int) -> dict[str, Any]:
        """Get a single track by ID.

        Args:
            track_id: Index of the track.

        Returns:
            Track dictionary with instrument, density, temperature, and bars.
        """
        return self.piece_by_track[track_id]

    def get_track_bars(self, track_id: int) -> list[str]:
        """Get all bars for a track.

        Args:
            track_id: Index of the track.

        Returns:
            List of bar strings.
        """
        return self.piece_by_track[track_id]["bars"]

    def get_track_temperature(self, track_id: int) -> float:
        """Get the temperature for a track.

        Args:
            track_id: Index of the track.

        Returns:
            Temperature value.
        """
        return self.piece_by_track[track_id]["temperature"]

    def get_track_config(self, track_id: int) -> TrackConfig:
        """Get the TrackConfig for a track.

        Args:
            track_id: Index of the track.

        Returns:
            TrackConfig with instrument, density, and temperature.
        """
        from .config import TrackConfig

        track = self.piece_by_track[track_id]
        return TrackConfig(
            instrument=track["instrument"],
            density=track["density"],
            temperature=track["temperature"],
        )

    def set_track_temperature(self, track_id: int, temperature: float) -> None:
        """Set the temperature for a track.

        Args:
            track_id: Index of the track.
            temperature: New temperature value.
        """
        self.piece_by_track[track_id]["temperature"] = temperature

    def get_track_count(self) -> int:
        """Get the number of tracks.

        Returns:
            Number of tracks in the piece.
        """
        return len(self.piece_by_track)

    def delete_track(self, track_id: int) -> None:
        """Delete a track from the piece.

        Args:
            track_id: Index of the track to delete.
        """
        self.piece_by_track.pop(track_id)

    def build_track_text(self, track_id: int) -> str:
        """Build the full text for a single track.

        Args:
            track_id: Index of the track.

        Returns:
            Full track text ending with TRACK_END.
        """
        bars = "".join(self.piece_by_track[track_id]["bars"])
        return f"{bars}{TRACK_END} "

    def build_piece_text(self) -> str:
        """Combine all tracks into final piece text.

        Returns:
            Full piece text starting with PIECE_START.
        """
        tracks = "".join(self.build_track_text(i) for i in range(len(self.piece_by_track)))
        return f"{PIECE_START} {tracks}"
