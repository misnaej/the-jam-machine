"""Tests for the validation module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jammy.generating.validation import (
    bar_count_check,
    check_instruments_in_vocab,
    force_bar_count,
)
from jammy.tokens import BAR_END, INST, TRACK_END


class TestBarCountCheck:
    """Tests for bar_count_check."""

    def test_bar_count_check_exact_match_returns_true(self) -> None:
        """Test that exact bar count returns True."""
        sequence = f"NOTE_ON=36 {BAR_END} NOTE_ON=38 {BAR_END} "
        matches, count = bar_count_check(sequence, 2)
        assert matches is True
        assert count == 2

    def test_bar_count_check_too_many_returns_false(self) -> None:
        """Test that too many bars returns False."""
        sequence = f"{BAR_END} {BAR_END} {BAR_END} "
        matches, count = bar_count_check(sequence, 2)
        assert matches is False
        assert count == 3

    def test_bar_count_check_too_few_returns_false(self) -> None:
        """Test that too few bars returns False."""
        sequence = f"NOTE_ON=36 {BAR_END} "
        matches, count = bar_count_check(sequence, 3)
        assert matches is False
        assert count == 1

    def test_bar_count_check_zero_bars(self) -> None:
        """Test sequence with no bars."""
        sequence = "NOTE_ON=36 NOTE_OFF=36 "
        matches, count = bar_count_check(sequence, 0)
        assert matches is True
        assert count == 0


class TestForceBarCount:
    """Tests for force_bar_count."""

    def test_force_bar_count_truncates_extra_bars(self) -> None:
        """Test that extra bars are trimmed when sequence is too long."""
        prompt = "PROMPT "
        generated = f"NOTE_ON=36 {BAR_END} NOTE_ON=38 {BAR_END} NOTE_ON=40 {BAR_END} "
        full_piece, checks = force_bar_count(prompt, generated, bar_count=3, expected_length=2)
        assert checks is True
        # Should contain exactly 2 BAR_END tokens
        assert full_piece.count(BAR_END) == 2
        assert TRACK_END in full_piece

    def test_force_bar_count_returns_false_when_short(self) -> None:
        """Test that too-short sequence triggers regeneration."""
        prompt = "PROMPT "
        generated = f"NOTE_ON=36 {BAR_END} "
        full_piece, checks = force_bar_count(prompt, generated, bar_count=1, expected_length=3)
        assert checks is False
        assert full_piece == prompt + generated


class TestCheckInstrumentsInVocab:
    """Tests for check_instruments_in_vocab."""

    def test_check_instruments_in_vocab_valid_passes(self) -> None:
        """Test that valid instruments don't raise."""
        # Mock: tokenizer — only .vocab dict is accessed
        # Avoids loading the real HF tokenizer (~8s model download)
        # The function only does dict key lookup, so a fake vocab is equivalent
        tokenizer = MagicMock()
        tokenizer.vocab = {f"{INST}=DRUMS": 0, f"{INST}=4": 1, f"{INST}=3": 2}
        check_instruments_in_vocab(tokenizer, ["DRUMS", "4", "3"])

    def test_check_instruments_in_vocab_invalid_raises(self) -> None:
        """Test that an invalid instrument raises ValueError."""
        # Mock: tokenizer — same rationale as test_valid_instruments_pass
        tokenizer = MagicMock()
        tokenizer.vocab = {f"{INST}=DRUMS": 0, f"{INST}=4": 1}
        with pytest.raises(ValueError, match="not in the tokenizer vocabulary"):
            check_instruments_in_vocab(tokenizer, ["DRUMS", "99"])
