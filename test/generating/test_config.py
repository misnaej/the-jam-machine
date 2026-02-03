"""Tests for generation configuration dataclasses."""

from __future__ import annotations

import pytest

from jammy.generating.config import GenerationConfig, TrackConfig


class TestTrackConfig:
    """Tests for TrackConfig dataclass."""

    def test_create_track_config(self) -> None:
        """Test creating a TrackConfig with valid parameters."""
        config = TrackConfig(instrument="DRUMS", density=3, temperature=0.7)

        assert config.instrument == "DRUMS"
        assert config.density == 3
        assert config.temperature == 0.7

    def test_track_config_is_frozen(self) -> None:
        """Test that TrackConfig is immutable (frozen)."""
        config = TrackConfig(instrument="4", density=2, temperature=0.5)

        with pytest.raises(AttributeError, match="cannot assign"):
            config.instrument = "5"  # type: ignore[misc]

        with pytest.raises(AttributeError, match="cannot assign"):
            config.density = 3  # type: ignore[misc]

        with pytest.raises(AttributeError, match="cannot assign"):
            config.temperature = 0.8  # type: ignore[misc]

    def test_track_config_equality(self) -> None:
        """Test that TrackConfig supports equality comparison."""
        config1 = TrackConfig(instrument="DRUMS", density=3, temperature=0.7)
        config2 = TrackConfig(instrument="DRUMS", density=3, temperature=0.7)
        config3 = TrackConfig(instrument="4", density=3, temperature=0.7)

        assert config1 == config2
        assert config1 != config3

    def test_track_config_hashable(self) -> None:
        """Test that TrackConfig is hashable (can be used as dict key)."""
        config1 = TrackConfig(instrument="DRUMS", density=3, temperature=0.7)
        config2 = TrackConfig(instrument="4", density=2, temperature=0.5)

        # Should be usable as dict keys
        config_dict = {config1: "drums", config2: "bass"}
        assert config_dict[config1] == "drums"
        assert config_dict[config2] == "bass"

        # Should be usable in sets
        config_set = {config1, config2, config1}  # duplicate should be ignored
        assert len(config_set) == 2


class TestGenerationConfig:
    """Tests for GenerationConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that GenerationConfig has correct default values."""
        config = GenerationConfig()

        assert config.n_bars == 8
        assert config.force_sequence_length is True
        assert config.improvisation_level == 0
        assert config.max_prompt_length == 1500
        assert config.generate_until_token == "TRACK_END"  # noqa: S105
        assert config.max_retries == 2

    def test_custom_values(self) -> None:
        """Test creating GenerationConfig with custom values."""
        config = GenerationConfig(
            n_bars=16,
            force_sequence_length=False,
            improvisation_level=3,
            max_prompt_length=2000,
            generate_until_token="BAR_END",  # noqa: S106
            max_retries=5,
        )

        assert config.n_bars == 16
        assert config.force_sequence_length is False
        assert config.improvisation_level == 3
        assert config.max_prompt_length == 2000
        assert config.generate_until_token == "BAR_END"  # noqa: S105
        assert config.max_retries == 5

    def test_generation_config_is_mutable(self) -> None:
        """Test that GenerationConfig is mutable."""
        config = GenerationConfig()

        # Should be able to modify attributes
        config.n_bars = 16
        assert config.n_bars == 16

        config.force_sequence_length = False
        assert config.force_sequence_length is False

        config.improvisation_level = 5
        assert config.improvisation_level == 5

        config.max_prompt_length = 2000
        assert config.max_prompt_length == 2000

        config.max_retries = 10
        assert config.max_retries == 10

    def test_partial_custom_values(self) -> None:
        """Test creating GenerationConfig with only some custom values."""
        config = GenerationConfig(n_bars=4, max_retries=5)

        # Custom values
        assert config.n_bars == 4
        assert config.max_retries == 5

        # Default values
        assert config.force_sequence_length is True
        assert config.improvisation_level == 0
        assert config.max_prompt_length == 1500
        assert config.generate_until_token == "TRACK_END"  # noqa: S105
