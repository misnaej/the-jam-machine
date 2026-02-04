"""Prompt construction and length management for generation."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .piece_builder import PieceBuilder

logger = logging.getLogger(__name__)


class PromptHandler:
    """Handles prompt construction and length management.

    This class is responsible for building generation prompts from
    the current piece state and managing prompt length to stay within
    model limits.

    Attributes:
        n_bars: Number of bars the model was trained on.
        max_length: Maximum prompt length in tokens.
    """

    def __init__(self, n_bars: int = 8, max_length: int = 1500) -> None:
        """Initialize the prompt handler.

        Args:
            n_bars: Number of bars per generation (model-dependent).
            max_length: Maximum prompt length in tokens.
        """
        self.n_bars = n_bars
        self.max_length = max_length

    def build_next_bar_prompt(
        self,
        piece: PieceBuilder,
        track_idx: int,
        verbose: bool = True,
    ) -> str:
        """Build a prompt for generating the next bar of a track.

        The prompt contains:
        - Context from other tracks (if they have more bars)
        - The track initialization (TRACK_START INST=... DENSITY=...)
        - The last (n_bars-1) bars of the track
        - BAR_START to trigger generation

        Args:
            piece: The PieceBuilder containing current piece state.
            track_idx: Index of the track to generate for.
            verbose: Whether to log status messages.

        Returns:
            The constructed prompt for generation.
        """
        track = piece.get_track(track_idx)
        track_bars = track["bars"]

        # Build pre-prompt from other tracks
        pre_prompt = "PIECE_START "
        for i in range(piece.get_track_count()):
            if i != track_idx:
                other_track = piece.get_track(i)
                other_bars = other_track["bars"]
                len_diff = len(other_bars) - len(track_bars)

                if len_diff > 0:
                    if verbose:
                        logger.info(
                            "Adding bars - %d selected from SIDE track: %d for prompt",
                            len(track_bars[-self.n_bars :]),
                            i,
                        )
                    # If other track is longer, this one should catch up
                    pre_prompt += other_bars[0]
                    for bar in track_bars[-self.n_bars :]:
                        pre_prompt += bar
                    pre_prompt += "TRACK_END "

        # Build main prompt from track to extend
        processed_prompt = track_bars[0]  # Track initialization
        if verbose:
            logger.info(
                "Adding bars - %d selected from MAIN track: %d for prompt",
                len(track_bars[-(self.n_bars - 1) :]),
                track_idx,
            )
        for bar in track_bars[-(self.n_bars - 1) :]:
            processed_prompt += bar

        processed_prompt += "BAR_START "

        # Enforce length limit on pre-prompt
        pre_prompt = self.enforce_length_limit(pre_prompt)

        logger.info("prompt length = %d", len((pre_prompt + processed_prompt).split(" ")))

        return pre_prompt + processed_prompt

    def enforce_length_limit(
        self,
        prompt: str,
        max_length: int | None = None,
    ) -> str:
        """Truncate prompt to fit within token limit.

        If the prompt is too long, removes a random track from it.

        Args:
            prompt: The prompt to potentially truncate.
            max_length: Maximum length in tokens (uses default if None).

        Returns:
            Truncated prompt if needed, otherwise original.
        """
        if max_length is None:
            max_length = self.max_length

        if len(prompt.split(" ")) < max_length:
            return prompt

        # Extract tracks and remove one randomly
        tracks = self._extract_tracks_from_prompt(prompt)
        if len(tracks) <= 1:
            return prompt

        selected_tracks = random.sample(tracks, len(tracks) - 1)
        truncated = "PIECE_START "
        for track in selected_tracks:
            truncated += track
        logger.info("Prompt too long - deleting one track")
        return truncated

    def _extract_tracks_from_prompt(self, prompt: str) -> list[str]:
        """Extract track strings from a prompt.

        Args:
            prompt: Prompt text containing tracks.

        Returns:
            List of track strings.
        """
        parts = prompt.split("TRACK_START ")[1:]
        tracks = []
        for part in parts:
            if "TRACK_END" in part:
                part = part.rstrip(" ").rstrip("TRACK_END")
            tracks.append(f"TRACK_START {part}TRACK_END ")
        return tracks
