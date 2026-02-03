"""Helper functions for comparing MIDI text sequences in tests.

These utilities are extracted from test_tosort.py to be reusable across test modules.
They provide comparison capabilities for generated vs encoded MIDI text sequences.
"""

from __future__ import annotations


def check_for_duplicated_subsequent_tokens(generated_text: str) -> list[tuple[str, int]]:
    """Check if there are duplicated subsequent tokens in the generated sequence.

    Args:
        generated_text: The generated MIDI text to check.

    Returns:
        List of tuples containing (duplicated_token, position) for each duplicate found.
    """
    duplicates: list[tuple[str, int]] = []
    tokens = generated_text.split(" ")
    for i, text in enumerate(tokens):
        if i < len(tokens) - 1 and text == tokens[i + 1]:
            duplicates.append((text, i))
    return duplicates


def simplify_events_for_comparison(generated_event: str, encoded_event: str) -> tuple[str, str]:
    """Simplify NOTE events for comparison by removing note values.

    When the sequence is encoded as midi with pretty midi, the order of sequences
    of NOTE_OFF or NOTE_ON can be changed. This does not change the music, but
    then the text sequences will be different and won't match.

    Args:
        generated_event: The generated event token.
        encoded_event: The encoded event token.

    Returns:
        Tuple of simplified event names (without note values).
    """
    generated_word = generated_event.split("=")[0] if "NOTE" in generated_event else generated_event
    encoded_word = encoded_event.split("=")[0] if "NOTE" in encoded_event else encoded_event

    return generated_word, encoded_word


def check_sequence_word_by_word(
    generated_text: str, encoded_text: str
) -> tuple[bool, list[dict[str, str | int]]]:
    """Check if generated and encoded sequences match word by word.

    Compares tokens at each position, simplifying NOTE events for comparison
    since pretty_midi may reorder simultaneous NOTE_ON/NOTE_OFF events.

    Args:
        generated_text: The generated MIDI text sequence.
        encoded_text: The encoded MIDI text sequence.

    Returns:
        Tuple of (is_similar, differences) where differences is a list of dicts
        containing position, generated_token, and encoded_token for each mismatch.

    Note:
        Both sequences must have the same number of tokens. Use
        compare_generated_encoded() for safe comparison that checks length first.
    """
    generated_tokens = generated_text.split(" ")
    encoded_tokens = encoded_text.split(" ")
    differences: list[dict[str, str | int]] = []

    # Compare up to the shorter sequence length to avoid IndexError
    min_len = min(len(generated_tokens), len(encoded_tokens))
    for i in range(min_len):
        generated_word, encoded_word = simplify_events_for_comparison(
            generated_tokens[i], encoded_tokens[i]
        )

        if generated_word != encoded_word:
            differences.append(
                {
                    "position": i,
                    "generated": generated_tokens[i],
                    "encoded": encoded_tokens[i],
                }
            )

    return len(differences) == 0, differences


def compare_generated_encoded(generated_text: str, encoded_text: str) -> dict[str, bool | int]:
    """Compare generated MIDI text sequence with encoded sequence.

    Args:
        generated_text: The generated MIDI text sequence.
        encoded_text: The encoded MIDI text sequence.

    Returns:
        Dict with comparison results:
        - identical: True if texts are exactly the same
        - same_length: True if token counts match
        - word_match: True if tokens match (ignoring NOTE value order)
        - generated_length: Number of tokens in generated text
        - encoded_length: Number of tokens in encoded text
    """
    result: dict[str, bool | int] = {
        "identical": generated_text == encoded_text,
        "same_length": False,
        "word_match": False,
        "generated_length": len(generated_text.split(" ")),
        "encoded_length": len(encoded_text.split(" ")),
    }

    result["same_length"] = result["generated_length"] == result["encoded_length"]

    if result["identical"]:
        result["word_match"] = True
    elif result["same_length"]:
        result["word_match"], _ = check_sequence_word_by_word(generated_text, encoded_text)

    return result
