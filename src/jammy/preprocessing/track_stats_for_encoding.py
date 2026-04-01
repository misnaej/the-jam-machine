"""Track statistics for MIDI encoding analysis.

Loads a MIDI file and computes per-instrument statistics useful for
understanding track structure before encoding.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from miditoolkit import MidiFile

if TYPE_CHECKING:
    from miditoolkit import Instrument

logger = logging.getLogger(__name__)


def _compute_instrument_stats(
    instruments: list[Instrument],
    ticks_per_beat: int,
    max_tick: int,
) -> dict[str, list[str | int | float]]:
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

        unique_ticks: set[int] = set()
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
    output_dir: str | None = None,
) -> dict[str, int | float | list[int] | list[float]]:
    """Analyze track statistics for MIDI encoding.

    Args:
        midi_filename: Name of the MIDI file (without .mid extension) in ./midi/.
        output_dir: If set, save plots to this directory instead of displaying.

    Returns:
        A dictionary with keys: instrument_count, beat_count, note_counts,
        coverage, coverage_true, min_starts, max_ends.
    """
    path_midi = f"./midi/{midi_filename}.mid"
    midi = MidiFile(path_midi)

    logger.info("Instruments: %d", len(midi.instruments))

    ticks_per_beat = midi.ticks_per_beat
    beat_count = midi.max_tick / ticks_per_beat
    inst_stats = _compute_instrument_stats(midi.instruments, ticks_per_beat, midi.max_tick)

    if logger.isEnabledFor(logging.DEBUG):
        for i, name in enumerate(inst_stats["names"]):
            logger.debug(
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

            fig, ax = plt.subplots(figsize=(12, 3))
            for track_idx, inst_idx in enumerate(indices):
                starts = [n.start / ticks_per_beat for n in midi.instruments[inst_idx].notes]
                ax.scatter(
                    starts,
                    [track_idx] * len(starts),
                    s=8,
                    alpha=0.6,
                    label=f"Track {inst_idx} ({len(starts)} notes)",
                )

            ax.set_title(f'Split instrument: "{unique_name}" across {len(indices)} tracks')
            ax.set_xlabel("Beat position")
            ax.set_ylabel("Track")
            ax.set_yticks(range(len(indices)))
            ax.set_yticklabels([f"Track {i}" for i in indices])
            ax.legend(loc="upper right", fontsize=8)
            fig.tight_layout()

            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                safe_name = str(unique_name).replace(" ", "_").lower()
                fig_path = Path(output_dir) / f"split_{safe_name}.png"
                fig.savefig(fig_path, bbox_inches="tight")
                logger.info("Saved plot: %s", fig_path)
                plt.close(fig)
            else:
                plt.show()
                plt.close(fig)

    return stats


if __name__ == "__main__":
    stats_on_track()
