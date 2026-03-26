"""Track statistics for MIDI encoding analysis.

Loads a MIDI file and computes per-instrument statistics useful for
understanding track structure before encoding.
"""

from __future__ import annotations

import logging

import matplotlib.pyplot as plt
import numpy as np
from miditoolkit import MidiFile

logger = logging.getLogger(__name__)


def _compute_instrument_stats(
    instruments: list,
    ticks_per_beat: int,
    max_tick: int,
) -> dict[str, list]:
    """Compute per-instrument note statistics.

    Args:
        instruments: List of miditoolkit Instrument objects.
        ticks_per_beat: MIDI ticks per beat.
        max_tick: Maximum tick in the file.

    Returns:
        Dict with lists of note counts, coverage, start/end times per instrument.
    """
    result: dict[str, list] = {
        "note_counts": [],
        "coverage": [],
        "coverage_true": [],
        "min_starts": [],
        "max_ends": [],
        "names": [],
    }

    for inst in instruments:
        result["names"].append(inst.name)
        result["note_counts"].append(len(inst.notes))

        total_duration = sum(n.end - n.start for n in inst.notes)
        result["coverage"].append(100 * (total_duration / max_tick) if max_tick else 0)

        unique_ticks = set()
        for note in inst.notes:
            unique_ticks.update(range(note.start, note.end))
        result["coverage_true"].append(100 * (len(unique_ticks) / max_tick) if max_tick else 0)

        if inst.notes:
            result["min_starts"].append(inst.notes[0].start / ticks_per_beat)
            result["max_ends"].append(inst.notes[-1].end / ticks_per_beat)
        else:
            result["min_starts"].append(0)
            result["max_ends"].append(0)

    return result


def stats_on_track(
    midi_filename: str = "the_strokes-reptilia",
    verbose: bool = True,
) -> dict[str, int | float | list[int] | list[float]]:
    """Analyze track statistics for MIDI encoding.

    Args:
        midi_filename: Name of the MIDI file (without .mid extension) in ./midi/.
        verbose: If True, logs detailed statistics for each instrument.

    Returns:
        A dictionary containing track statistics.
    """
    path_midi = f"./midi/{midi_filename}.mid"
    midi = MidiFile(path_midi)

    logger.info("Instruments: %d", len(midi.instruments))

    beat_count = midi.max_tick / midi.ticks_per_beat
    inst_stats = _compute_instrument_stats(midi.instruments, midi.ticks_per_beat, midi.max_tick)

    if verbose:
        for i, name in enumerate(inst_stats["names"]):
            logger.info(
                "%s: %d notes, %.0f%% coverage, starts at %.1f beats, ends at %.1f beats",
                name,
                inst_stats["note_counts"][i],
                inst_stats["coverage_true"][i],
                inst_stats["min_starts"][i],
                inst_stats["max_ends"][i],
            )

    stats = {
        "instrument_count": len(midi.instruments),
        "beat_count": beat_count,
        "note_counts": inst_stats["note_counts"],
        "coverage": inst_stats["coverage"],
        "coverage_true": inst_stats["coverage_true"],
        "min_starts": inst_stats["min_starts"],
        "max_ends": inst_stats["max_ends"],
    }

    # Plot split instruments (same name across multiple tracks)
    for unique_name in set(inst_stats["names"]):
        indices = [i for i, n in enumerate(inst_stats["names"]) if n == unique_name]
        if len(indices) > 1:
            logger.info("%s is split across tracks %s", unique_name, indices)
            all_starts = []
            all_track_ids = []
            for track_idx, inst_idx in enumerate(indices):
                for note in midi.instruments[inst_idx].notes:
                    all_starts.append(note.start)
                    all_track_ids.append(track_idx)

            order = np.argsort(all_starts)
            plt.figure()
            plt.plot(all_starts, all_track_ids, "o")
            plt.plot(np.array(all_starts)[order], np.array(all_track_ids)[order], "-")
            plt.title(f"Split instrument: {unique_name}")
            plt.show()

    return stats


if __name__ == "__main__":
    stats_on_track()
