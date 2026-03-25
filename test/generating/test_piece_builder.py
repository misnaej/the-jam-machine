"""Tests for the piece builder module."""

from __future__ import annotations

import pytest

from jammy.generating.config import TrackConfig
from jammy.generating.piece_builder import PieceBuilder
from jammy.tokens import BAR_START, PIECE_START, TRACK_END, TRACK_START


@pytest.fixture
def empty_builder() -> PieceBuilder:
    """Create an empty PieceBuilder."""
    return PieceBuilder()


@pytest.fixture
def builder_with_track() -> PieceBuilder:
    """Create a PieceBuilder with one initialized track."""
    pb = PieceBuilder()
    pb.init_track("DRUMS", 3, 0.7)
    return pb


@pytest.fixture
def builder_with_bars() -> PieceBuilder:
    """Create a PieceBuilder with a track that has bars."""
    pb = PieceBuilder()
    pb.init_track("DRUMS", 3, 0.7)
    bars = (
        f"{TRACK_START} INST=DRUMS DENSITY=3 "
        f"{BAR_START} NOTE_ON=36 TIME_DELTA=4 NOTE_OFF=36 BAR_END "
        f"{BAR_START} NOTE_ON=38 TIME_DELTA=4 NOTE_OFF=38 BAR_END "
        f"{TRACK_END} "
    )
    pb.add_bars_to_track(-1, bars)
    return pb


class TestInitTrack:
    """Tests for PieceBuilder.init_track."""

    def test_init_track_adds_to_empty_builder(self, empty_builder: PieceBuilder) -> None:
        """Test adding a track to an empty builder."""
        empty_builder.init_track("DRUMS", 3, 0.7)
        assert empty_builder.get_track_count() == 1

    def test_init_track_sets_correct_fields(self, empty_builder: PieceBuilder) -> None:
        """Test that initialized track has all expected fields."""
        empty_builder.init_track("4", 2, 0.5)
        track = empty_builder.get_track(0)
        assert track["instrument"] == "4"
        assert track["density"] == 2
        assert track["temperature"] == 0.5
        assert track["bars"] == []
        assert track["label"] == "track_0"

    def test_init_track_assigns_sequential_labels(self, empty_builder: PieceBuilder) -> None:
        """Test that multiple tracks get sequential labels."""
        empty_builder.init_track("DRUMS", 3, 0.7)
        empty_builder.init_track("4", 2, 0.5)
        assert empty_builder.get_track(0)["label"] == "track_0"
        assert empty_builder.get_track(1)["label"] == "track_1"
        assert empty_builder.get_track_count() == 2


class TestAddBarsToTrack:
    """Tests for PieceBuilder.add_bars_to_track."""

    def test_add_bars_to_track_appends_bars(self, builder_with_track: PieceBuilder) -> None:
        """Test that bars are added to the track."""
        bars = f"{BAR_START} NOTE_ON=36 BAR_END {BAR_START} NOTE_ON=38 BAR_END "
        builder_with_track.add_bars_to_track(0, bars)
        assert len(builder_with_track.get_track_bars(0)) == 2

    def test_add_bars_to_track_strips_track_end(self, builder_with_track: PieceBuilder) -> None:
        """Test that TRACK_END is stripped from bars text."""
        bars = f"{BAR_START} NOTE_ON=36 BAR_END {TRACK_END} "
        builder_with_track.add_bars_to_track(0, bars)
        for bar in builder_with_track.get_track_bars(0):
            assert TRACK_END not in bar

    def test_add_bars_to_track_negative_index_uses_last(self, empty_builder: PieceBuilder) -> None:
        """Test that track_id=-1 adds to the last track."""
        empty_builder.init_track("DRUMS", 3, 0.7)
        empty_builder.init_track("4", 2, 0.5)
        bars = f"{BAR_START} NOTE_ON=40 BAR_END "
        empty_builder.add_bars_to_track(-1, bars)
        assert len(empty_builder.get_track_bars(1)) == 1
        assert len(empty_builder.get_track_bars(0)) == 0


class TestDeleteTrack:
    """Tests for PieceBuilder.delete_track."""

    def test_delete_track_removes_by_index(self, empty_builder: PieceBuilder) -> None:
        """Test that delete_track removes the specified track."""
        empty_builder.init_track("DRUMS", 3, 0.7)
        empty_builder.init_track("4", 2, 0.5)
        empty_builder.delete_track(0)
        assert empty_builder.get_track_count() == 1
        assert empty_builder.get_track(0)["instrument"] == "4"


class TestGetTrackConfig:
    """Tests for PieceBuilder.get_track_config."""

    def test_get_track_config_returns_matching(self, builder_with_track: PieceBuilder) -> None:
        """Test that get_track_config returns a matching TrackConfig."""
        config = builder_with_track.get_track_config(0)
        assert isinstance(config, TrackConfig)
        assert config.instrument == "DRUMS"
        assert config.density == 3
        assert config.temperature == 0.7


class TestSetTrackTemperature:
    """Tests for PieceBuilder.set_track_temperature."""

    def test_set_track_temperature_updates_value(self, builder_with_track: PieceBuilder) -> None:
        """Test that temperature is updated correctly."""
        builder_with_track.set_track_temperature(0, 0.3)
        assert builder_with_track.get_track_temperature(0) == 0.3


class TestBuildText:
    """Tests for build_track_text and build_piece_text."""

    def test_build_track_text_ends_with_track_end(self, builder_with_bars: PieceBuilder) -> None:
        """Test that track text ends with TRACK_END."""
        text = builder_with_bars.build_track_text(0)
        assert text.rstrip().endswith(TRACK_END)

    def test_build_track_text_contains_bars(self, builder_with_bars: PieceBuilder) -> None:
        """Test that track text contains the bar content."""
        text = builder_with_bars.build_track_text(0)
        assert "NOTE_ON=36" in text
        assert "NOTE_ON=38" in text

    def test_build_piece_text_starts_with_piece_start(
        self,
        builder_with_bars: PieceBuilder,
    ) -> None:
        """Test that piece text starts with PIECE_START."""
        text = builder_with_bars.build_piece_text()
        assert text.startswith(f"{PIECE_START} ")

    def test_build_piece_text_contains_all_tracks(self, empty_builder: PieceBuilder) -> None:
        """Test that piece text contains all tracks."""
        empty_builder.init_track("DRUMS", 3, 0.7)
        empty_builder.init_track("4", 2, 0.5)
        bars = f"{BAR_START} NOTE_ON=36 BAR_END "
        empty_builder.add_bars_to_track(0, bars)
        empty_builder.add_bars_to_track(1, bars)
        text = empty_builder.build_piece_text()
        assert text.count(TRACK_END) == 2


class TestRestoreState:
    """Tests for restoring state from existing piece_by_track."""

    def test_init_with_existing_state(self) -> None:
        """Test that PieceBuilder can be initialized with existing state."""
        state = [
            {
                "label": "track_0",
                "instrument": "DRUMS",
                "density": 3,
                "temperature": 0.7,
                "bars": ["bar1"],
            },
        ]
        pb = PieceBuilder(state)
        assert pb.get_track_count() == 1
        assert pb.get_track(0)["instrument"] == "DRUMS"
        assert pb.get_track_bars(0) == ["bar1"]

    def test_init_with_none(self) -> None:
        """Test that PieceBuilder with None creates empty state."""
        pb = PieceBuilder(None)
        assert pb.get_track_count() == 0
