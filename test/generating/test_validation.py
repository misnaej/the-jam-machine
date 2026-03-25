"""Tests for the validation module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jammy.generating.validation import (
    bar_count_check,
    check_if_prompt_inst_in_tokenizer_vocab,
    forcing_bar_count,
)
from jammy.tokens import BAR_END, INST, TRACK_END


class TestBarCountCheck:
    """Tests for bar_count_check."""

    def test_exact_match(self) -> None:
        """Test that exact bar count returns True."""
        sequence = f"NOTE_ON=36 {BAR_END} NOTE_ON=38 {BAR_END} "
        matches, count = bar_count_check(sequence, 2)
        assert matches is True
        assert count == 2

    def test_too_many_bars(self) -> None:
        """Test that too many bars returns False."""
        sequence = f"{BAR_END} {BAR_END} {BAR_END} "
        matches, count = bar_count_check(sequence, 2)
        assert matches is False
        assert count == 3

    def test_too_few_bars(self) -> None:
        """Test that too few bars returns False."""
        sequence = f"NOTE_ON=36 {BAR_END} "
        matches, count = bar_count_check(sequence, 3)
        assert matches is False
        assert count == 1

    def test_zero_bars(self) -> None:
        """Test sequence with no bars."""
        sequence = "NOTE_ON=36 NOTE_OFF=36 "
        matches, count = bar_count_check(sequence, 0)
        assert matches is True
        assert count == 0


class TestForcingBarCount:
    """Tests for forcing_bar_count."""

    def test_truncates_when_too_long(self) -> None:
        """Test that extra bars are trimmed when sequence is too long."""
        prompt = "PROMPT "
        generated = f"NOTE_ON=36 {BAR_END} NOTE_ON=38 {BAR_END} NOTE_ON=40 {BAR_END} "
        full_piece, checks = forcing_bar_count(prompt, generated, bar_count=3, expected_length=2)
        assert checks is True
        # Should contain exactly 2 BAR_END tokens
        assert full_piece.count(BAR_END) == 2
        assert TRACK_END in full_piece

    def test_returns_false_when_too_short(self) -> None:
        """Test that too-short sequence triggers regeneration."""
        prompt = "PROMPT "
        generated = f"NOTE_ON=36 {BAR_END} "
        full_piece, checks = forcing_bar_count(prompt, generated, bar_count=1, expected_length=3)
        assert checks is False
        assert full_piece == prompt + generated


class TestCheckIfPromptInstInTokenizerVocab:
    """Tests for check_if_prompt_inst_in_tokenizer_vocab."""

    def test_valid_instruments_pass(self) -> None:
        """Test that valid instruments don't raise."""
        tokenizer = MagicMock()
        tokenizer.vocab = {f"{INST}=DRUMS": 0, f"{INST}=4": 1, f"{INST}=3": 2}
        # Should not raise
        check_if_prompt_inst_in_tokenizer_vocab(tokenizer, ["DRUMS", "4", "3"])

    def test_invalid_instrument_raises(self) -> None:
        """Test that an invalid instrument raises ValueError."""
        tokenizer = MagicMock()
        tokenizer.vocab = {f"{INST}=DRUMS": 0, f"{INST}=4": 1}
        with pytest.raises(ValueError, match="not in the tokenizer vocabulary"):
            check_if_prompt_inst_in_tokenizer_vocab(tokenizer, ["DRUMS", "99"])
