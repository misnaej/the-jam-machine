"""Validation utilities for MIDI generation."""

from __future__ import annotations

import logging
from typing import Any

from jammy.constants import INSTRUMENT_CLASSES
from jammy.tokens import BAR_END, INST, TRACK_END

logger = logging.getLogger(__name__)


def bar_count_check(sequence: str, n_bars: int) -> tuple[bool, int]:
    """Check if the sequence contains the right number of bars.

    Args:
        sequence: The MIDI text sequence to check.
        n_bars: Expected number of bars.

    Returns:
        Tuple of (matches, actual_count).
    """
    tokens = sequence.split(" ")
    bar_count = sum(1 for token in tokens if token == BAR_END)
    bar_count_matches = bar_count == n_bars
    if not bar_count_matches:
        logger.info("Bar count is %d - but should be %d", bar_count, n_bars)
    return bar_count_matches, bar_count


def check_if_prompt_inst_in_tokenizer_vocab(
    tokenizer: Any,  # noqa: ANN401
    inst_prompt_list: list[str],
) -> None:
    """Check if the prompt instruments are in the tokenizer vocab.

    Args:
        tokenizer: The tokenizer to check against.
        inst_prompt_list: List of instruments to validate.

    Raises:
        ValueError: If an instrument is not in the tokenizer vocabulary.
    """
    for inst in inst_prompt_list:
        if f"{INST}={inst}" not in tokenizer.vocab:
            instruments_in_dataset = sorted(
                tok.split("=")[-1] for tok in tokenizer.vocab if INST in tok
            )
            for classe in INSTRUMENT_CLASSES:
                logger.info("%s", classe)
            raise ValueError(
                f"The instrument {inst} is not in the tokenizer vocabulary. "
                f"Available Instruments: {instruments_in_dataset}"
            )


def forcing_bar_count(
    input_prompt: str,
    generated: str,
    bar_count: int,
    expected_length: int,
) -> tuple[str, bool]:
    """Force the generated sequence to have the expected length.

    Args:
        input_prompt: The original input prompt.
        generated: The generated sequence (without prompt).
        bar_count: Actual number of bars generated.
        expected_length: Expected number of bars.

    Returns:
        Tuple of (full_piece, bar_count_checks).
    """
    if bar_count - expected_length > 0:  # Cut the sequence if too long
        bars = generated.split(f"{BAR_END} ")
        truncated = f"{BAR_END} ".join(bars[:expected_length]) + f"{BAR_END} {TRACK_END} "
        full_piece = input_prompt + truncated
        logger.info("Generated sequence truncated at %d bars", expected_length)
        bar_count_checks = True

    else:  # bar_count - expected_length < 0: Sequence is too short
        full_piece = input_prompt + generated
        bar_count_checks = False
        logger.info("Generated sequence is too short - Force Regeneration")

    return full_piece, bar_count_checks
