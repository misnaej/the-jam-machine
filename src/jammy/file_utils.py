"""File I/O utilities for reading, writing, copying, and compressing files."""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING, TypeVar
from zipfile import ZIP_DEFLATED, ZipFile

if TYPE_CHECKING:
    from collections.abc import Callable

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
