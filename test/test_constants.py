"""Tests for the constants module."""

from __future__ import annotations

from jammy.constants import get_instrument_class


class TestGetInstrumentClass:
    """Tests for get_instrument_class."""

    def test_get_instrument_class_piano(self) -> None:
        """Test that program 0 returns piano class."""
        cls = get_instrument_class(0)
        assert cls is not None
        assert cls["name"] == "Piano"
        assert cls["family_number"] == 0

    def test_get_instrument_class_bass(self) -> None:
        """Test that program 33 returns bass class."""
        cls = get_instrument_class(33)
        assert cls is not None
        assert cls["name"] == "Bass"
        assert cls["family_number"] == 4

    def test_get_instrument_class_out_of_range(self) -> None:
        """Test that out-of-range program returns None."""
        assert get_instrument_class(999) is None

    def test_get_instrument_class_boundary(self) -> None:
        """Test boundary between families (program 7 = last piano, 8 = first chromatic perc)."""
        piano = get_instrument_class(7)
        chromatic = get_instrument_class(8)
        assert piano is not None
        assert piano["name"] == "Piano"
        assert chromatic is not None
        assert chromatic["name"] == "Chromatic Percussion"
