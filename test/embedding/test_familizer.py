"""Tests for the familizer module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from jammy.embedding.familizer import Familizer
from jammy.tokens import INST

if TYPE_CHECKING:
    from pathlib import Path


class TestGetFamilyNumber:
    """Tests for Familizer.get_family_number."""

    def test_get_family_number_piano(self) -> None:
        """Test that program 0 maps to family 0 (piano)."""
        f = Familizer()
        assert f.get_family_number(0) == 0

    def test_get_family_number_bass(self) -> None:
        """Test that program 33 maps to family 4 (bass)."""
        f = Familizer()
        assert f.get_family_number(33) == 4

    def test_get_family_number_out_of_range(self) -> None:
        """Test that an out-of-range program returns None."""
        f = Familizer()
        assert f.get_family_number(999) is None


class TestGetProgramNumber:
    """Tests for Familizer.get_program_number."""

    def test_get_program_number_valid_family(self) -> None:
        """Test that a valid family number returns a program in range."""
        f = Familizer(arbitrary=True)
        program = f.get_program_number(0)
        assert 0 <= program < 8  # piano family range

    def test_get_program_number_invalid_raises(self) -> None:
        """Test that an invalid family number raises KeyError."""
        f = Familizer()
        with pytest.raises(KeyError, match="not found"):
            f.get_program_number(999)


class TestReplaceInstrumentToken:
    """Tests for Familizer.replace_instrument_token."""

    def test_replace_instrument_token_to_family(self) -> None:
        """Test converting a program token to family token."""
        f = Familizer()
        f.operation = "family"
        result = f.replace_instrument_token(f"{INST}=33")
        assert result == f"{INST}=4"  # program 33 → family 4 (bass)

    def test_replace_instrument_token_to_program(self) -> None:
        """Test converting a family token to program token."""
        f = Familizer(arbitrary=True)
        f.operation = "program"
        result = f.replace_instrument_token(f"{INST}=4")
        # Should return a valid program in the bass family (32-39)
        program = int(result.split("=")[1])
        assert 32 <= program < 40

    def test_replace_instrument_token_unknown_operation(self) -> None:
        """Test that unknown operation returns token unchanged."""
        f = Familizer()
        f.operation = "unknown"
        token = f"{INST}=33"
        assert f.replace_instrument_token(token) == token


class TestReplaceInstrumentInText:
    """Tests for Familizer.replace_instrument_in_text."""

    def test_replace_instrument_in_text_replaces_inst_tokens(self) -> None:
        """Test that INST tokens in text are replaced."""
        f = Familizer()
        f.operation = "family"
        text = f"TRACK_START {INST}=33 DENSITY=2 BAR_START NOTE_ON=40 BAR_END TRACK_END"
        result = f.replace_instrument_in_text(text)
        assert f"{INST}=4" in result
        assert f"{INST}=33" not in result

    def test_replace_instrument_in_text_drums_passthrough(self) -> None:
        """Test that DRUMS token is not modified."""
        f = Familizer()
        f.operation = "family"
        text = f"TRACK_START {INST}=DRUMS DENSITY=3 BAR_START BAR_END TRACK_END"
        result = f.replace_instrument_in_text(text)
        assert f"{INST}=DRUMS" in result


class TestReplaceInstrumentsInFile:
    """Tests for Familizer.replace_instruments_in_file."""

    def test_replace_instruments_in_file_modifies_content(self, tmp_path: Path) -> None:
        """Test that instrument tokens in a file are replaced in place."""
        f = Familizer()
        f.operation = "family"
        txt = tmp_path / "track.txt"
        txt.write_text(f"TRACK_START {INST}=33 DENSITY=2 BAR_START NOTE_ON=40 BAR_END TRACK_END")
        f.replace_instruments_in_file(txt)
        result = txt.read_text()
        assert f"{INST}=4" in result
        assert f"{INST}=33" not in result
