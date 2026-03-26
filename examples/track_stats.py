"""Example: Analyze MIDI track statistics.

Loads a MIDI file and prints per-instrument statistics: note counts,
coverage, start/end times. Useful for understanding track structure
before encoding.

Setup:
    pipenv install -e "."

Usage:
    pipenv run python examples/track_stats.py
"""

from __future__ import annotations

from jammy.logging_config import setup_logging
from jammy.preprocessing.track_stats_for_encoding import stats_on_track

DEFAULT_OUTPUT_DIR = "output/examples/track_stats"


def main(output_dir: str = DEFAULT_OUTPUT_DIR) -> None:
    """Run track statistics on The Strokes - Reptilia.

    Args:
        output_dir: Directory for output plots.
    """
    setup_logging(log_to_file=False)
    stats_on_track(midi_filename="the_strokes-reptilia", output_dir=output_dir)


if __name__ == "__main__":
    main()
