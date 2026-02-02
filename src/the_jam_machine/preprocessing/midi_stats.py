"""MIDI file statistics computation module.

This module provides functions to extract various statistical features from MIDI files,
including instrument counts, note characteristics, tempo, and time signature information.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from joblib import Parallel, delayed
from pretty_midi import PrettyMIDI, program_to_instrument_name

from ..constants import INSTRUMENT_CLASSES
from ..utils import compute_list_average, get_files

if TYPE_CHECKING:
    import pandas as pd

# TODO: add data enrichment
# TODO: include types
# TODO: count most common combinations of instruments / instrument families
#       (pairwise and trackwise)

logger = logging.getLogger(__name__)


def categorize_midi_instrument(program_number: int) -> str | None:
    """Categorize a MIDI instrument by its program number.

    Args:
        program_number: The MIDI program number (0-127).

    Returns:
        The instrument class name, or None if not found.
    """
    for instrument_class in INSTRUMENT_CLASSES:
        if program_number in instrument_class["program_range"]:
            return instrument_class["name"]
    return None


def track_name(midi_file: str | Path) -> str:
    """Extract the track name from a MIDI file path.

    Args:
        midi_file: Path to the MIDI file.

    Returns:
        The file stem (filename without extension).
    """
    return Path(midi_file).stem


def n_instruments(pm: PrettyMIDI) -> int | None:
    """Count the total number of instruments in a MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of instruments, or None if no instruments exist.
    """
    if pm.instruments:
        return len(pm.instruments)
    return None


def n_unique_instruments(pm: PrettyMIDI) -> int | None:
    """Count the number of unique instruments by program number.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of unique instrument programs, or None if no instruments exist.
    """
    if pm.instruments:
        return len({instrument.program for instrument in pm.instruments})
    return None


def instrument_names(pm: PrettyMIDI) -> list[list[str]] | None:
    """Get the unique instrument names from a MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        A nested list containing unique instrument names, or None if no instruments.
    """
    if pm.instruments:
        return [
            list({program_to_instrument_name(instrument.program) for instrument in pm.instruments})
        ]
    return None


def instrument_families(pm: PrettyMIDI) -> list[list[str | None]] | None:
    """Get the unique instrument families from a MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        A nested list containing unique instrument family names, or None if no instruments.
    """
    if pm.instruments:
        return [
            list({categorize_midi_instrument(instrument.program) for instrument in pm.instruments})
        ]
    return None


def number_of_instrument_families(pm: PrettyMIDI) -> int | None:
    """Count the number of unique instrument families.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of unique instrument families, or None if no instruments exist.
    """
    if pm.instruments:
        return len(
            {categorize_midi_instrument(instrument.program) for instrument in pm.instruments}
        )
    return None


def number_of_notes(pm: PrettyMIDI) -> int | None:
    """Count the total number of notes across all instruments.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The total note count, or None if no instruments exist.
    """
    if pm.instruments:
        return sum(len(instrument.notes) for instrument in pm.instruments)
    return None


def number_of_unique_notes(pm: PrettyMIDI) -> int | None:
    """Count the number of unique note pitches across all instruments.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of unique pitches, or None if no instruments exist.
    """
    if pm.instruments:
        return len({note.pitch for instrument in pm.instruments for note in instrument.notes})
    return None


def avg_number_of_unique_notes_per_instrument(pm: PrettyMIDI) -> float | None:
    """Calculate the average number of unique notes per instrument.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The average unique note count per instrument, or None if no instruments exist.
    """
    if pm.instruments:
        return compute_list_average(
            [len({note.pitch for note in instrument.notes}) for instrument in pm.instruments]
        )
    return None


def average_note_duration(pm: PrettyMIDI) -> float | None:
    """Calculate the average duration of all notes.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The average note duration in seconds, or None if no instruments exist.
    """
    if pm.instruments:
        return compute_list_average(
            [note.end - note.start for instrument in pm.instruments for note in instrument.notes]
        )
    return None


def average_note_velocity(pm: PrettyMIDI) -> float | None:
    """Calculate the average velocity of all notes.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The average note velocity (0-127), or None if no instruments exist.
    """
    if pm.instruments:
        return compute_list_average(
            [note.velocity for instrument in pm.instruments for note in instrument.notes]
        )
    return None


def average_note_pitch(pm: PrettyMIDI) -> float | None:
    """Calculate the average pitch of all notes.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The average note pitch (0-127), or None if no instruments exist.
    """
    if pm.instruments:
        return compute_list_average(
            [note.pitch for instrument in pm.instruments for note in instrument.notes]
        )
    return None


def range_of_note_pitches(pm: PrettyMIDI) -> int | None:
    """Calculate the range between the highest and lowest note pitches.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The pitch range, or None if no instruments exist.
    """
    if pm.instruments:
        pitches = [note.pitch for instrument in pm.instruments for note in instrument.notes]
        return max(pitches) - min(pitches)
    return None


def average_range_of_note_pitches_per_instrument(pm: PrettyMIDI) -> float | None:
    """Calculate the average pitch range per instrument.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The average pitch range per instrument, or None if no instruments exist.
    """
    if pm.instruments:
        return compute_list_average(
            [
                max(note.pitch for note in instrument.notes)
                - min(note.pitch for note in instrument.notes)
                for instrument in pm.instruments
            ]
        )
    return None


def number_of_note_pitch_classes(pm: PrettyMIDI) -> int | None:
    """Count the number of unique pitch classes (0-11) used.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of unique pitch classes, or None if no instruments exist.
    """
    if pm.instruments:
        return len({note.pitch % 12 for instrument in pm.instruments for note in instrument.notes})
    return None


def average_number_of_note_pitch_classes_per_instrument(pm: PrettyMIDI) -> float | None:
    """Calculate the average number of pitch classes per instrument.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The average pitch class count per instrument, or None if no instruments exist.
    """
    if pm.instruments:
        return compute_list_average(
            [len({note.pitch % 12 for note in instrument.notes}) for instrument in pm.instruments]
        )
    return None


def number_of_octaves(pm: PrettyMIDI) -> int | None:
    """Count the number of unique octaves used.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of unique octaves, or None if no instruments exist.
    """
    if pm.instruments:
        return len({note.pitch // 12 for instrument in pm.instruments for note in instrument.notes})
    return None


def average_number_of_octaves_per_instrument(pm: PrettyMIDI) -> float | None:
    """Calculate the average number of octaves per instrument.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The average octave count per instrument, or None if no instruments exist.
    """
    if pm.instruments:
        return compute_list_average(
            [len({note.pitch // 12 for note in instrument.notes}) for instrument in pm.instruments]
        )
    return None


def number_of_notes_per_second(pm: PrettyMIDI) -> float | None:
    """Calculate the note density (notes per second).

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The note density, or None if no instruments exist.
    """
    if pm.instruments:
        return (
            len([note for instrument in pm.instruments for note in instrument.notes])
            / pm.get_end_time()
        )
    return None


def shortest_note_length(pm: PrettyMIDI) -> float | None:
    """Find the duration of the shortest note.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The shortest note duration in seconds, or None if no instruments exist.
    """
    if pm.instruments:
        return min(
            note.end - note.start for instrument in pm.instruments for note in instrument.notes
        )
    return None


def longest_note_length(pm: PrettyMIDI) -> float | None:
    """Find the duration of the longest note.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The longest note duration in seconds, or None if no instruments exist.
    """
    if pm.instruments:
        return max(
            note.end - note.start for instrument in pm.instruments for note in instrument.notes
        )
    return None


def main_key_signature(pm: PrettyMIDI) -> int | None:
    """Get the main (first) key signature.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The key number of the first key signature, or None if none exist.
    """
    if pm.key_signature_changes:
        return pm.key_signature_changes[0].key_number
    return None


def n_key_changes(pm: PrettyMIDI) -> int | None:
    """Count the number of key signature changes.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of key changes, or None if no key signatures exist.
    """
    if pm.key_signature_changes:
        return len(pm.key_signature_changes)
    return None


def n_tempo_changes(pm: PrettyMIDI) -> int:
    """Count the number of tempo changes.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of tempo changes.
    """
    return len(pm.get_tempo_changes())


def average_tempo(pm: PrettyMIDI) -> int | None:
    """Estimate the average tempo of the MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The estimated tempo in BPM, or None if estimation fails.
    """
    try:
        return round(pm.estimate_tempo())
    except Exception:
        logger.debug("Failed to estimate tempo for MIDI file")
        return None


def tempo_changes(pm: PrettyMIDI) -> list[list[Any]]:
    """Get all tempo changes from the MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        A nested list containing tempo change information.
    """
    return [[pm.get_tempo_changes()]]


def main_time_signature(pm: PrettyMIDI) -> str | None:
    """Get the main (first) time signature.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The first time signature as a string (e.g., "4/4"), or None if none exist.
    """
    if pm.time_signature_changes:
        ts = pm.time_signature_changes[0]
        return f"{ts.numerator}/{ts.denominator}"
    return None


def n_time_signature_changes(pm: PrettyMIDI) -> int | None:
    """Count the number of time signature changes.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of time signature changes, or None if none exist.
    """
    if pm.time_signature_changes:
        return len(pm.time_signature_changes)
    return None


def all_time_signatures(pm: PrettyMIDI) -> list[list[str]] | None:
    """Get all time signatures from the MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        A nested list of time signature strings, or None if none exist.
    """
    if pm.time_signature_changes:
        return [[f"{ts.numerator}/{ts.denominator}" for ts in pm.time_signature_changes]]
    return None


def four_to_the_floor(pm: PrettyMIDI) -> bool | None:
    """Check if the MIDI file uses exclusively 4/4 time signature.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        True if exclusively 4/4, False otherwise, or None if no time signatures exist.
    """
    if pm.time_signature_changes:
        time_signatures = [f"{ts.numerator}/{ts.denominator}" for ts in pm.time_signature_changes]
        # check if time_signatures contains exclusively '4/4'
        return all(ts == "4/4" for ts in time_signatures) and len(time_signatures) == 1
    return None


def track_length_in_seconds(pm: PrettyMIDI) -> float:
    """Get the total duration of the MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The track length in seconds.
    """
    return pm.get_end_time()


def lyrics_number_of_words(pm: PrettyMIDI) -> int | None:
    """Count the number of lyric words in the MIDI file.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of lyric words, or None if no lyrics exist.
    """
    if pm.lyrics:
        return len([lyric.text for lyric in pm.lyrics])
    return None


def lyrics_number_of_unique_words(pm: PrettyMIDI) -> int | None:
    """Count the number of unique lyric words.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        The number of unique lyric words, or None if no lyrics exist.
    """
    if pm.lyrics:
        return len({lyric.text for lyric in pm.lyrics})
    return None


def lyrics_boolean(pm: PrettyMIDI) -> bool:
    """Check if the MIDI file contains lyrics.

    Args:
        pm: A PrettyMIDI object.

    Returns:
        True if lyrics exist, False otherwise.
    """
    return bool(pm.lyrics)


class MidiStats:
    """Class for computing statistics from MIDI files."""

    def single_file_statistics(self, midi_file: str | Path) -> dict[str, Any] | None:
        """Compute statistics for a single MIDI file.

        Args:
            midi_file: Path to the MIDI file.

        Returns:
            A dictionary of statistics, or None if the file cannot be parsed.
        """
        # Some Midi files are corrupted and cannot be parsed by PrettyMIDI
        try:
            pm = PrettyMIDI(str(midi_file))
        except Exception:
            logger.warning("Failed to parse MIDI file: %s", midi_file)
            return None

        # Compute statistics
        avg_pitch_range = average_range_of_note_pitches_per_instrument(pm)
        avg_pitch_classes = average_number_of_note_pitch_classes_per_instrument(pm)

        statistics = {
            # track md5 hash name without extension
            "md5": track_name(midi_file),
            # instruments
            "n_instruments": n_instruments(pm),
            "n_unique_instruments": n_unique_instruments(pm),
            "instrument_names": instrument_names(pm),
            "instrument_families": instrument_families(pm),
            "number_of_instrument_families": number_of_instrument_families(pm),
            # notes
            "n_notes": number_of_notes(pm),
            "n_unique_notes": number_of_unique_notes(pm),
            "average_n_unique_notes_per_instrument": (
                avg_number_of_unique_notes_per_instrument(pm)
            ),
            "average_note_duration": average_note_duration(pm),
            "average_note_velocity": average_note_velocity(pm),
            "average_note_pitch": average_note_pitch(pm),
            "range_of_note_pitches": range_of_note_pitches(pm),
            "average_range_of_note_pitches_per_instrument": avg_pitch_range,
            "number_of_note_pitch_classes": number_of_note_pitch_classes(pm),
            "average_number_of_note_pitch_classes_per_instrument": avg_pitch_classes,
            "number_of_octaves": number_of_octaves(pm),
            "average_number_of_octaves_per_instrument": (
                average_number_of_octaves_per_instrument(pm)
            ),
            "number_of_notes_per_second": number_of_notes_per_second(pm),
            "shortest_note_length": shortest_note_length(pm),
            "longest_note_length": longest_note_length(pm),
            # key signatures
            "main_key_signature": main_key_signature(pm),  # hacky
            "n_key_changes": n_key_changes(pm),
            # tempo
            "n_tempo_changes": n_tempo_changes(pm),
            "tempo_estimate": average_tempo(pm),  # hacky
            # time signatures
            "main_time_signature": main_time_signature(pm),  # hacky
            "all_time_signatures": all_time_signatures(pm),
            "four_to_the_floor": four_to_the_floor(pm),
            "n_time_signature_changes": n_time_signature_changes(pm),
            # track length
            "track_length_in_seconds": track_length_in_seconds(pm),
            # lyrics
            "lyrics_nb_words": lyrics_number_of_words(pm),
            "lyrics_unique_words": lyrics_number_of_unique_words(pm),
            "lyrics_bool": lyrics_boolean(pm),
        }
        return statistics

    def get_stats(
        self,
        input_directory: str | Path,
        recursive: bool = False,
        n_jobs: int = -1,
    ) -> list[dict[str, Any]]:
        """Compute statistics for a list of MIDI files.

        Args:
            input_directory: Path to the directory containing the MIDI files.
            recursive: If True, recursively search for MIDI files in subdirectories.
            n_jobs: Number of parallel jobs (-1 for all CPUs).

        Returns:
            A list of statistics dictionaries for each successfully parsed file.
        """
        midi_files = get_files(input_directory, "mid", recursive)

        statistics = Parallel(n_jobs, verbose=1)(
            delayed(self.single_file_statistics)(midi_file) for midi_file in midi_files
        )

        # Remove None values, where statistics could not be computed
        return [s for s in statistics if s is not None]


if __name__ == "__main__":
    import pandas as pd

    # Select the path to the MIDI files
    input_directory = Path("data/music_picks/electronic_artists").resolve()
    logger.info("Processing MIDI files from: %s", input_directory)

    # Select the path to save the statistics
    output_directory = Path("data/music_picks").resolve()

    # Compute statistics using parallel processing
    statistics = MidiStats().get_stats(input_directory, recursive=True)

    # export df to csv
    df = pd.DataFrame(statistics)
    df.to_csv(output_directory / "statistics.csv", index=False)
