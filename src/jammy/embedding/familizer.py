"""Instrument familization for MIDI program number to family mapping.

Converts between specific MIDI program numbers (0-127) and broader
instrument family categories (0-15), operating on text token files.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path

from joblib import Parallel, delayed

from jammy.constants import INSTRUMENT_CLASSES, INSTRUMENT_TRANSFER_CLASSES, get_instrument_class
from jammy.file_utils import FileCompressor, get_files, timeit
from jammy.tokens import DRUMS, INST

logger = logging.getLogger(__name__)


class Familizer:
    """Convert between MIDI program numbers and instrument family numbers.

    This class handles the conversion between specific MIDI program numbers
    (0-127) and their broader instrument family categories (0-15).

    Attributes:
        n_jobs: Number of parallel jobs.
        reference_programs: Mapping from family numbers to program numbers.
    """

    def __init__(self, n_jobs: int = -1, arbitrary: bool = False) -> None:
        """Initialize the Familizer.

        Args:
            n_jobs: Number of parallel jobs (-1 for all CPUs).
            arbitrary: Whether to use transfer classes for arbitrary instruments.
        """
        self.n_jobs = n_jobs
        self.reverse_family(arbitrary)

    def get_family_number(self, program_number: int) -> int | None:
        """Get the instrument family number for a MIDI program number.

        Args:
            program_number: MIDI program number (0-127).

        Returns:
            Family number (0-15) or None if not found.
        """
        cls = get_instrument_class(program_number)
        return cls["family_number"] if cls else None

    def reverse_family(self, arbitrary: bool) -> None:
        """Create mapping from family numbers to program numbers.

        This is used to reverse the family number tokens back to
        program number tokens.

        Args:
            arbitrary: Whether to use transfer classes.
        """
        int_class = INSTRUMENT_TRANSFER_CLASSES if arbitrary else INSTRUMENT_CLASSES

        self.reference_programs: dict[int, int] = {}
        for family in int_class:
            self.reference_programs[family["family_number"]] = random.choice(  # noqa: S311
                family["program_range"],
            )

    def get_program_number(self, family_number: int) -> int:
        """Get a program number for a family number.

        Returns a random program number in the respective program_range.
        This is the reverse operation of get_family_number.

        Args:
            family_number: Instrument family number (0-15).

        Returns:
            A program number from that family.

        Raises:
            KeyError: If family_number is not in reference_programs.
        """
        if family_number not in self.reference_programs:
            msg = f"Family number {family_number} not found"
            raise KeyError(msg)
        return self.reference_programs[family_number]

    def replace_instrument_token(self, token: str, operation: str) -> str:
        """Replace a MIDI program number token with family/program number.

        Args:
            token: Token like 'INST=86'.
            operation: Either 'family' or 'program'.

        Returns:
            Converted token, or the original token if operation is unknown.
        """
        inst_number = int(token.split("=")[1])
        if operation == "family":
            return f"{INST}={self.get_family_number(inst_number)}"
        if operation == "program":
            return f"{INST}={self.get_program_number(inst_number)}"
        return token

    def replace_instrument_in_text(self, text: str, operation: str) -> str:
        """Replace all instrument tokens in text.

        Args:
            text: Text containing INST= tokens.
            operation: Either 'family' or 'program'.

        Returns:
            Text with replaced instrument tokens.
        """
        return " ".join(
            self.replace_instrument_token(token, operation)
            if token.startswith(f"{INST}=") and token != f"{INST}={DRUMS}"
            else token
            for token in text.split(" ")
        )

    def replace_in_file(self, file: Path, operation: str) -> None:
        """Replace instrument tokens in a text file.

        Args:
            file: Path to the text file.
            operation: Either 'family' or 'program'.
        """
        text = file.read_text()
        file.write_text(self.replace_instrument_in_text(text, operation))

    @timeit
    def _replace_all(self, output_directory: Path, operation: str) -> None:
        """Replace instrument tokens in all text files in a directory.

        Args:
            output_directory: Directory containing text files.
            operation: Either 'family' or 'program'.
        """
        files = get_files(output_directory, extension="txt")
        Parallel(n_jobs=self.n_jobs)(
            delayed(self.replace_in_file)(file, operation) for file in files
        )

    def replace_tokens(self, input_directory: Path, output_directory: Path, operation: str) -> None:
        """Perform token replacement on all text files in a directory.

        Args:
            input_directory: Directory with input zip files.
            output_directory: Directory for output zip files.
            operation: Either 'family' or 'program'.
        """
        fc = FileCompressor(input_directory, output_directory, self.n_jobs)
        fc.unzip()
        self._replace_all(output_directory, operation)
        fc.zip()
        logger.info("%s complete", operation)

    def to_family(self, input_directory: Path, output_directory: Path) -> None:
        """Convert instrument tokens to family number tokens.

        Args:
            input_directory: Directory containing zip files.
            output_directory: Directory for output zip files.
        """
        self.replace_tokens(input_directory, output_directory, "family")

    def to_program(self, input_directory: Path, output_directory: Path) -> None:
        """Convert family tokens to program number tokens.

        Args:
            input_directory: Directory containing zip files.
            output_directory: Directory for output zip files.
        """
        self.replace_tokens(input_directory, output_directory, "program")


if __name__ == "__main__":
    # Choose number of jobs for parallel processing
    n_jobs = -1

    # Instantiate Familizer
    familizer = Familizer(n_jobs)

    # Choose directory to process for program
    input_directory = Path("midi/dataset/first_selection/validate").resolve()  # fmt: skip
    output_directory = input_directory / "family"

    # familize files
    familizer.to_family(input_directory, output_directory)
