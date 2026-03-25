"""Tests for the prompt handler module."""

from __future__ import annotations

import pytest

from jammy.generating.piece_builder import PieceBuilder
from jammy.generating.prompt_handler import PromptHandler
from jammy.tokens import BAR_START, PIECE_START, TRACK_END, TRACK_START


@pytest.fixture
def handler() -> PromptHandler:
    """Create a PromptHandler with default settings."""
    return PromptHandler(n_bars=8, max_length=1500)


@pytest.fixture
def piece_two_tracks() -> PieceBuilder:
    """Create a PieceBuilder with two tracks, each with bars."""
    pb = PieceBuilder()
    pb.init_track("DRUMS", 3, 0.7)
    pb.init_track("4", 2, 0.5)

    # Add bars to both tracks — track header + 3 bars each
    drums_bars = (
        f"{TRACK_START} INST=DRUMS DENSITY=3 "
        f"{BAR_START} NOTE_ON=36 BAR_END "
        f"{BAR_START} NOTE_ON=38 BAR_END "
        f"{BAR_START} NOTE_ON=42 BAR_END "
    )
    bass_bars = (
        f"{TRACK_START} INST=4 DENSITY=2 "
        f"{BAR_START} NOTE_ON=40 BAR_END "
        f"{BAR_START} NOTE_ON=43 BAR_END "
        f"{BAR_START} NOTE_ON=45 BAR_END "
    )
    pb.add_bars_to_track(0, drums_bars)
    pb.add_bars_to_track(1, bass_bars)
    return pb


class TestBuildNextBarPrompt:
    """Tests for PromptHandler.build_next_bar_prompt."""

    def test_prompt_starts_with_piece_start(
        self, handler: PromptHandler, piece_two_tracks: PieceBuilder
    ) -> None:
        """Test that prompt starts with PIECE_START."""
        prompt = handler.build_next_bar_prompt(piece_two_tracks, 0, verbose=False)
        assert prompt.startswith(f"{PIECE_START} ")

    def test_prompt_ends_with_bar_start(
        self, handler: PromptHandler, piece_two_tracks: PieceBuilder
    ) -> None:
        """Test that prompt ends with BAR_START to trigger generation."""
        prompt = handler.build_next_bar_prompt(piece_two_tracks, 0, verbose=False)
        assert prompt.rstrip().endswith(f"{BAR_START}")

    def test_prompt_contains_track_content(
        self, handler: PromptHandler, piece_two_tracks: PieceBuilder
    ) -> None:
        """Test that prompt contains content from the target track."""
        prompt = handler.build_next_bar_prompt(piece_two_tracks, 0, verbose=False)
        assert "NOTE_ON=36" in prompt or "NOTE_ON=38" in prompt or "NOTE_ON=42" in prompt


class TestEnforceLengthLimit:
    """Tests for PromptHandler.enforce_length_limit."""

    def test_short_prompt_unchanged(self, handler: PromptHandler) -> None:
        """Test that a short prompt is returned unchanged."""
        prompt = f"{PIECE_START} {TRACK_START} INST=DRUMS DENSITY=3 {TRACK_END} "
        result = handler.enforce_length_limit(prompt)
        assert result == prompt

    def test_long_prompt_truncated(self) -> None:
        """Test that a prompt exceeding max_length is truncated."""
        handler = PromptHandler(n_bars=8, max_length=20)
        # Build a prompt with two tracks, each long enough to exceed limit
        track1 = f"{TRACK_START} INST=DRUMS DENSITY=3 " + "NOTE_ON=36 " * 15 + f"{TRACK_END} "
        track2 = f"{TRACK_START} INST=4 DENSITY=2 " + "NOTE_ON=40 " * 15 + f"{TRACK_END} "
        prompt = f"{PIECE_START} {track1}{track2}"

        result = handler.enforce_length_limit(prompt)
        # Should have removed one track
        assert result.count(TRACK_END) == 1

    def test_single_track_not_truncated(self) -> None:
        """Test that a single-track prompt is not truncated even if long."""
        handler = PromptHandler(n_bars=8, max_length=5)
        track = f"{TRACK_START} INST=DRUMS DENSITY=3 " + "NOTE_ON=36 " * 20 + f"{TRACK_END} "
        prompt = f"{PIECE_START} {track}"

        result = handler.enforce_length_limit(prompt)
        # Can't remove the only track — returned as-is
        assert result == prompt

    def test_custom_max_length(self, handler: PromptHandler) -> None:
        """Test that custom max_length parameter is respected."""
        prompt = f"{PIECE_START} " + "TOKEN " * 10
        result = handler.enforce_length_limit(prompt, max_length=5)
        # Prompt has >5 tokens but no tracks to remove, so returned as-is
        assert result == prompt
