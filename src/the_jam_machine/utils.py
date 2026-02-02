"""Diverse utility functions for MIDI encoding/decoding and file operations."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, TypeVar
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from joblib import Parallel, delayed
from miditok import Event, MIDILike
from pydub import AudioSegment
from scipy.io.wavfile import write

from .constants import DRUMS_BEAT_QUANTIZATION, NONE_DRUMS_BEAT_QUANTIZATION

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

logger = logging.getLogger(__name__)

T = TypeVar("T")


def index_has_substring(items: Sequence[str], substring: str) -> int:
    """Find the index of the first item containing a substring.

    Args:
        items: A sequence of strings to search through.
        substring: The substring to search for.

    Returns:
        The index of the first item containing the substring, or -1 if not found.
    """
    for i, s in enumerate(items):
        if substring in s:
            return i
    return -1


# TODO: Make this singleton
def get_miditok() -> MIDILike:
    """Create and return a MIDILike tokenizer instance.

    Returns:
        A configured MIDILike tokenizer with full pitch range and 8th note resolution.
    """
    pitch_range = range(0, 127)  # was (21, 109)
    beat_res = {(0, 400): 8}
    return MIDILike(pitch_range, beat_res)


def timeit(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that logs the execution time of a function.

    Args:
        func: The function to wrap with timing.

    Returns:
        A wrapped function that logs execution time.
    """

    def wrapper(*args: object, **kwargs: object) -> T:
        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        logger.info("%s took %.2f seconds to run.", func.__name__, end - start)
        return result

    return wrapper


def chain(input_value: object, funcs: Sequence[Callable[..., object]], *params: object) -> object:
    """Chain functions together, passing the output of one function as the input of the next.

    Args:
        input_value: The initial input value to pass to the first function.
        funcs: A sequence of functions to chain together.
        *params: Additional parameters to pass to each function.

    Returns:
        The result of applying all functions in sequence.
    """
    res = input_value
    for func in funcs:
        try:
            res = func(res, *params)
        except TypeError:
            res = func(res)
    return res


def split_dots(value: str) -> list[int]:
    """Split a string separated by dots into a list of integers.

    Args:
        value: A dot-separated string like "a.b.c".

    Returns:
        A list of integers parsed from the string, e.g., [a, b, c].
    """
    return list(map(int, value.split(".")))


def compute_list_average(values: Sequence[float]) -> float:
    """Compute the arithmetic average of a sequence of numbers.

    Args:
        values: A sequence of numeric values.

    Returns:
        The arithmetic mean of the values.
    """
    return sum(values) / len(values)


def get_datetime() -> str:
    """Get the current datetime as a formatted string.

    Returns:
        The current datetime in YYYYMMDD_HHMMSS format.
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# Encoding functions


def int_dec_base_to_beat(beat_str: str) -> float:
    """Convert "integer.decimal.base" format to beats.

    Converts a string in miditok format to a float representing beats.
    For example, "0.4.8" = 0 + 4/8 = 0.5 beats.

    Args:
        beat_str: A string in "integer.decimal.base" format.

    Returns:
        The beat value as a float.
    """
    integer, decimal, base = split_dots(beat_str)
    return integer + decimal / base


def int_dec_base_to_delta(beat_str: str, instrument: str = "drums") -> int:
    """Convert time shift to time_delta according to encoding scheme.

    Drums TIME_DELTA are quantized according to DRUMS_BEAT_QUANTIZATION.
    Other instrument TIME_DELTA are quantized according to NONE_DRUMS_BEAT_QUANTIZATION.

    Args:
        beat_str: A string in "integer.decimal.base" format.
        instrument: The instrument type, used to determine quantization.

    Returns:
        The quantized time delta as an integer.
    """
    beat_res = (
        DRUMS_BEAT_QUANTIZATION if instrument.lower() == "drums" else NONE_DRUMS_BEAT_QUANTIZATION
    )
    time_delta = int_dec_base_to_beat(beat_str) * beat_res
    return int(time_delta)


def get_text(event: Event, instrument: str = "drums") -> str:
    """Convert an event into a string for the midi-text format.

    Args:
        event: A miditok Event object to convert.
        instrument: The instrument type for time delta quantization.

    Returns:
        The text representation of the event.
    """
    match event.type:
        case "Piece-Start":
            return "PIECE_START "
        case "Track-Start":
            return "TRACK_START "
        case "Track-End":
            return "TRACK_END "
        case "Instrument":
            if str(event.value).lower() == "drums":
                return "INST=DRUMS "
            else:
                return f"INST={event.value} "
        case "Density":
            return f"DENSITY={event.value} "
        case "Bar-Start":
            return "BAR_START "
        case "Bar-End":
            return "BAR_END "
        case "Time-Shift":
            return f"TIME_DELTA={int_dec_base_to_delta(event.value, instrument)} "
        case "Note-On":
            return f"NOTE_ON={event.value} "
        case "Note-Off":
            return f"NOTE_OFF={event.value} "
        case _:
            return ""


# Decoding functions


def time_delta_to_beat(time_delta: int | str, instrument: str = "drums") -> float:
    """Convert TIME_DELTA to beats according to encoding scheme.

    Args:
        time_delta: The time delta value from midi-text.
        instrument: The instrument type ("Drums" or other), used to determine
            the quantization resolution defined in constants.py.

    Returns:
        The beat value as a float.
    """
    beat_res = (
        DRUMS_BEAT_QUANTIZATION if instrument.lower() == "drums" else NONE_DRUMS_BEAT_QUANTIZATION
    )
    beats = float(time_delta) / beat_res
    return beats


def beat_to_int_dec_base(beat: float, beat_res: int = 8) -> str:
    """Convert beats into "integer.decimal.base" format for miditok.

    Args:
        beat: The beat value as a float.
        beat_res: The beat resolution (default 8).

    Returns:
        A string in "integer.decimal.base" format.
        For example, 0.5 beats with resolution 8 becomes "0.4.8".
    """
    int_dec_base = [
        int((beat * beat_res) // beat_res),
        int((beat * beat_res) % beat_res),
        beat_res,
    ]
    return ".".join(map(str, int_dec_base))


def time_delta_to_int_dec_base(time_delta: int | str, instrument: str = "drums") -> str:
    """Convert TIME_DELTA to "integer.decimal.base" format.

    Args:
        time_delta: The time delta value from midi-text.
        instrument: The instrument type for quantization.

    Returns:
        A string in "integer.decimal.base" format.
    """
    return chain(
        time_delta,
        [
            time_delta_to_beat,
            beat_to_int_dec_base,
        ],
        instrument,
    )


def get_event(text: str, value: str | None = None, instrument: str = "drums") -> Event | None:
    """Convert a midi-text like event into a miditok like event.

    Args:
        text: The event type text (e.g., "PIECE_START", "NOTE_ON").
        value: The optional value associated with the event.
        instrument: The instrument type for time delta conversion.

    Returns:
        A miditok Event object, or None if the text is not recognized.
    """
    match text:
        case "PIECE_START":
            return Event("Piece-Start", value)
        case "TRACK_START":
            return Event("Track-Start", value)
        case "TRACK_END":
            return Event("Track-End", value)
        case "INST":
            if value == "DRUMS":
                value = "Drums"
            return Event("Instrument", value)
        case "BAR_START":
            return Event("Bar-Start", value)
        case "BAR_END":
            return Event("Bar-End", value)
        case "TIME_SHIFT":
            return Event("Time-Shift", value)
        case "TIME_DELTA":
            return Event("Time-Shift", time_delta_to_int_dec_base(value, instrument))
        case "NOTE_ON":
            return Event("Note-On", value)
        case "NOTE_OFF":
            return Event("Note-Off", value)
        case _:
            return None


# File utils


def write_to_file(path: str | Path, content: dict[str, object] | str | object) -> None:
    """Write content to a file, creating parent directories if needed.

    Args:
        path: The file path to write to.
        content: The content to write. Dicts are written as JSON, other types
            are converted to strings.
    """
    path = Path(path)
    if isinstance(content, dict):
        with path.open("w") as json_file:
            json.dump(content, json_file)
    else:
        if not isinstance(content, str):
            content = str(content)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            f.write(content)


# Backwards compatibility aliases
writeToFile = write_to_file  # noqa: N816


def read_from_file(
    path: str | Path,
    *,
    is_json: bool = False,
    isJSON: bool | None = None,  # noqa: N803
) -> str | dict[str, object]:
    """Read content from a file.

    Args:
        path: The file path to read from.
        is_json: If True, parse the file as JSON.
        isJSON: Deprecated alias for is_json (for backward compatibility).

    Returns:
        The file content as a string or parsed JSON object.
    """
    # Support deprecated parameter name
    if isJSON is not None:
        is_json = isJSON
    path = Path(path)
    with path.open() as f:
        if is_json:
            return json.load(f)
        else:
            return f.read()


# Backwards compatibility aliases
readFromFile = read_from_file  # noqa: N816


def get_files(directory: Path, extension: str, *, recursive: bool = False) -> list[Path]:
    """Get a list of file paths matching a specified extension.

    Args:
        directory: The directory to search as a Path object.
        extension: The file extension to match as a string (without dot).
        recursive: Whether to search recursively in the directory.

    Returns:
        A list of Path objects for matching files.
    """
    if recursive:
        return list(directory.rglob(f"*.{extension}"))
    else:
        return list(directory.glob(f"*.{extension}"))


def load_jsonl(filepath: str | Path) -> list[dict[str, object]]:
    """Load a JSONL file.

    Args:
        filepath: Path to the JSONL file.

    Returns:
        A list of dictionaries, one per line in the file.
    """
    filepath = Path(filepath)
    with filepath.open() as f:
        data = [json.loads(line) for line in f]
    return data


def write_mp3(waveform: np.ndarray, output_path: Path, bitrate: str = "92k") -> None:
    """Write a waveform to an MP3 file.

    Args:
        waveform: Numpy array of the waveform data.
        output_path: Path object for the output MP3 file.
        bitrate: Bitrate of the MP3 file (64k, 92k, 128k, 256k, 312k).
    """
    # write the wav file
    wav_path = output_path.with_suffix(".wav")
    write(wav_path, 44100, waveform.astype(np.float32))
    # compress the wav file as mp3
    AudioSegment.from_wav(wav_path).export(output_path, format="mp3", bitrate=bitrate)
    # remove the wav file
    wav_path.unlink()


def copy_file(input_file: Path, output_dir: Path) -> None:
    """Copy an input file to the output directory.

    Args:
        input_file: Path to the file to copy.
        output_dir: Path to the destination directory.
    """
    output_file = output_dir / input_file.name
    shutil.copy(input_file, output_file)


class FileCompressor:
    """Handles compression and decompression of files using zip format."""

    def __init__(self, input_directory: Path, output_directory: Path, n_jobs: int = -1) -> None:
        """Initialize the FileCompressor.

        Args:
            input_directory: Directory containing files to process.
            output_directory: Directory to output processed files.
            n_jobs: Number of parallel jobs (-1 for all CPUs).
        """
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.n_jobs = n_jobs

    # File compression and decompression
    def unzip_file(self, file: Path) -> None:
        """Uncompress a single zip file.

        Args:
            file: Path to the zip file to uncompress.
        """
        with ZipFile(file, "r") as zip_ref:
            zip_ref.extractall(self.output_directory)

    def zip_file(self, file: Path) -> None:
        """Compress a single text file to a new zip file and delete the original.

        Args:
            file: Path to the file to compress.
        """
        output_file = self.output_directory / (file.stem + ".zip")
        with ZipFile(output_file, "w") as zip_ref:
            zip_ref.write(file, arcname=file.name, compress_type=ZIP_DEFLATED)
            file.unlink()

    @timeit
    def unzip(self) -> None:
        """Uncompress all zip files in the input directory."""
        files = get_files(self.input_directory, extension="zip")
        Parallel(n_jobs=self.n_jobs)(delayed(self.unzip_file)(file) for file in files)

    @timeit
    def zip(self) -> None:
        """Compress all text files in output directory to zip files and remove originals."""
        files = get_files(self.output_directory, extension="txt")
        Parallel(n_jobs=self.n_jobs)(delayed(self.zip_file)(file) for file in files)
