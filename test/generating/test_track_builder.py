"""Tests for the track builder module."""

from __future__ import annotations

from jammy.generating.track_builder import (
    combine_tracks,
    extract_new_bar,
    extract_tracks,
    get_last_track,
    get_new_content,
    strip_track_ends,
)


class TestStripTrackEnds:
    """Tests for strip_track_ends."""

    def test_removes_track_end(self) -> None:
        """Test that TRACK_END is removed from text."""
        text = "INST=3 DENSITY=1 BAR_START NOTE_ON=64 BAR_END TRACK_END "
        result = strip_track_ends(text)
        assert "TRACK_END" not in result
        assert result.startswith("INST=3 DENSITY=1")

    def test_no_track_end_unchanged(self) -> None:
        """Test that text without TRACK_END keeps its content."""
        text = "INST=3 DENSITY=1 BAR_START NOTE_ON=64 BAR_END"
        result = strip_track_ends(text)
        assert result == text


class TestExtractTracks:
    """Tests for extract_tracks."""

    def test_multi_track_piece(self, sample_piece_text: str) -> None:
        """Test extracting multiple tracks from a piece."""
        tracks = extract_tracks(sample_piece_text)
        assert len(tracks) == 3
        assert all(t.startswith("TRACK_START ") for t in tracks)
        assert all("TRACK_END" in t for t in tracks)

    def test_single_track(self) -> None:
        """Test extracting a single track from a piece."""
        text = "PIECE_START TRACK_START INST=3 DENSITY=1 BAR_START NOTE_ON=64 BAR_END TRACK_END"
        tracks = extract_tracks(text)
        assert len(tracks) == 1
        assert tracks[0].startswith("TRACK_START ")

    def test_preserves_track_content(self) -> None:
        """Test that track content is preserved after extraction."""
        text = "PIECE_START TRACK_START INST=3 DENSITY=1 BAR_START NOTE_ON=64 BAR_END TRACK_END"
        tracks = extract_tracks(text)
        assert "INST=3" in tracks[0]
        assert "NOTE_ON=64" in tracks[0]


class TestGetLastTrack:
    """Tests for get_last_track."""

    def test_returns_last_track(self, sample_piece_text: str) -> None:
        """Test that the last track (INST=4) is returned."""
        last = get_last_track(sample_piece_text)
        assert "INST=4" in last
        assert last.startswith("TRACK_START ")


class TestCombineTracks:
    """Tests for combine_tracks."""

    def test_combines_tracks(self) -> None:
        """Test combining tracks into a piece with PIECE_START."""
        tracks = ["TRACK_START INST=3 TRACK_END ", "TRACK_START INST=4 TRACK_END "]
        result = combine_tracks(tracks)
        assert result.startswith("PIECE_START ")
        assert "TRACK_START INST=3 TRACK_END " in result
        assert "TRACK_START INST=4 TRACK_END " in result


class TestGetNewContent:
    """Tests for get_new_content."""

    def test_extracts_new_content(self) -> None:
        """Test extracting newly generated content beyond the prompt."""
        prompt = "PIECE_START TRACK_START INST=3 "
        full = "PIECE_START TRACK_START INST=3 BAR_START NOTE_ON=64 BAR_END TRACK_END "
        result = get_new_content(full, prompt)
        assert result == "BAR_START NOTE_ON=64 BAR_END TRACK_END "


class TestExtractNewBar:
    """Tests for extract_new_bar."""

    def test_extracts_last_bar(self) -> None:
        """Test extracting the last bar from generation output."""
        text = (
            "PIECE_START TRACK_START INST=3 "
            "BAR_START NOTE_ON=60 BAR_END "
            "BAR_START NOTE_ON=64 BAR_END TRACK_END "
        )
        result = extract_new_bar(text)
        assert result.startswith("BAR_START ")
        assert "NOTE_ON=64" in result
        assert "TRACK_END" not in result

    def test_strips_track_end(self) -> None:
        """Test that TRACK_END is stripped from extracted bar."""
        text = "BAR_START NOTE_ON=64 BAR_END TRACK_END "
        result = extract_new_bar(text)
        assert result.startswith("BAR_START ")
        assert "TRACK_END" not in result
        assert "NOTE_ON=64" in result
