"""Tests for example scripts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from examples import encode_decode, generate

if TYPE_CHECKING:
    from pathlib import Path


def test_encode_decode_example(tmp_path: Path) -> None:
    """Test that the encode/decode example runs without errors."""
    encode_decode.main(output_dir=tmp_path)

    # Verify outputs were created
    assert (tmp_path / "the_strokes-reptilia_encoded.txt").exists()
    assert (tmp_path / "the_strokes-reptilia_decoded.mid").exists()
    assert (tmp_path / "the_strokes-reptilia_piano_roll.png").exists()


def test_generate_example(tmp_path: Path) -> None:
    """Test that the generation example runs without errors."""
    generate.main(output_dir=str(tmp_path))
