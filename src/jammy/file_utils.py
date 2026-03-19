"""File I/O utilities for reading, writing, copying, and compressing files."""

from __future__ import annotations

import functools
import json
import logging
import shutil
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, TypeVar
from zipfile import ZIP_DEFLATED, ZipFile

if TYPE_CHECKING:
    from collections.abc import Callable

    import numpy as np

logger = logging.getLogger(__name__)

T = TypeVar("T")


def timeit(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that logs the execution time of a function.

    Args:
        func: The function to wrap with timing.

    Returns:
        A wrapped function that logs execution time.
    """

    @functools.wraps(func)
    def wrapper(*args: object, **kwargs: object) -> T:
        start = perf_counter()
        result = func(*args, **kwargs)
        end = perf_counter()
        logger.info("%s took %.2f seconds to run.", func.__name__, end - start)
        return result

    return wrapper


def write_to_file(path: str | Path, content: dict[str, object] | str | object) -> None:
    """Write content to a file, creating parent directories if needed.

    Args:
        path: The file path to write to.
        content: The content to write. Dicts are written as JSON, other types
            are converted to strings.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, dict):
        with path.open("w") as json_file:
            json.dump(content, json_file)
    else:
        if not isinstance(content, str):
            content = str(content)
        with path.open("w") as f:
            f.write(content)


def read_from_file(
    path: str | Path,
    *,
    is_json: bool = False,
) -> str | dict[str, object]:
    """Read content from a file.

    Args:
        path: The file path to read from.
        is_json: If True, parse the file as JSON.

    Returns:
        The file content as a string or parsed JSON object.
    """
    path = Path(path)
    with path.open() as f:
        if is_json:
            return json.load(f)
        else:
            return f.read()


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
    import numpy as np
    from pydub import AudioSegment
    from scipy.io.wavfile import write

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
        from joblib import Parallel, delayed

        files = get_files(self.input_directory, extension="zip")
        Parallel(n_jobs=self.n_jobs)(delayed(self.unzip_file)(file) for file in files)

    @timeit
    def zip(self) -> None:
        """Compress all text files in output directory to zip files and remove originals."""
        from joblib import Parallel, delayed

        files = get_files(self.output_directory, extension="txt")
        Parallel(n_jobs=self.n_jobs)(delayed(self.zip_file)(file) for file in files)
