"""Configuration dataclasses for MIDI generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrackConfig:
    """Configuration for a single track generation.

    Attributes:
        instrument: Instrument identifier ("DRUMS" or family number like "4").
        density: Note density level (1-3 typical).
        temperature: Sampling temperature (0.1-1.0).
    """

    instrument: str
    density: int
    temperature: float


@dataclass
class GenerationConfig:
    """Configuration for the generation engine.

    Attributes:
        n_bars: Number of bars to generate per section.
        force_sequence_length: Whether to regenerate until correct length.
        improvisation_level: N-gram penalty size (0 = no penalty).
        max_prompt_length: Maximum tokens in prompt before truncation.
        generate_until_token: Token that signals end of generation.
        max_retries: Maximum regeneration attempts before giving up.
    """

    n_bars: int = 8
    force_sequence_length: bool = True
    improvisation_level: int = 0
    max_prompt_length: int = 1500
    generate_until_token: str = "TRACK_END"  # noqa: S105
    max_retries: int = 2
