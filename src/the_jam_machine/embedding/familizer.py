from __future__ import annotations

import logging
import random
from pathlib import Path

from joblib import Parallel, delayed

from ..constants import INSTRUMENT_CLASSES, INSTRUMENT_TRANSFER_CLASSES
from ..utils import FileCompressor, get_files, timeit

logger = logging.getLogger(__name__)


class Familizer:
    """Convert between MIDI program numbers and instrument family numbers.

    This class handles the conversion between specific MIDI program numbers
    (0-127) and their broader instrument family categories (0-15).
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
        for instrument_class in INSTRUMENT_CLASSES:
            if program_number in instrument_class["program_range"]:
                return instrument_class["family_number"]
        return None

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
                family["program_range"]
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
            raise KeyError(f"Family number {family_number} not found")
        return self.reference_programs[family_number]

    def replace_instrument_token(self, token: str) -> str:
        """Replace a MIDI program number token with family/program number.

        Args:
            token: Token like 'INST=86'.

        Returns:
            Converted token like 'INST=10'.
        """
        inst_number = int(token.split("=")[1])
        if self.operation == "family":
            return "INST=" + str(self.get_family_number(inst_number))
        elif self.operation == "program":
            return "INST=" + str(self.get_program_number(inst_number))
        return token

    def replace_instrument_in_text(self, text: str) -> str:
        """Replace all instrument tokens in text with family number tokens.

        Args:
            text: Text containing INST= tokens.

        Returns:
            Text with replaced instrument tokens.
        """
        return " ".join(
            [
                self.replace_instrument_token(token)
                if token.startswith("INST=") and token != "INST=DRUMS"  # noqa: S105
                else token
                for token in text.split(" ")
            ]
        )

    def replace_instruments_in_file(self, file: Path) -> None:
        """Replace instrument tokens in a text file.

        Args:
            file: Path to the text file.
        """
        text = file.read_text()
        file.write_text(self.replace_instrument_in_text(text))

    @timeit
    def replace_instruments(self) -> None:
        """Replace instrument tokens in all text files in output directory."""
        files = get_files(self.output_directory, extension="txt")
        Parallel(n_jobs=self.n_jobs)(
            delayed(self.replace_instruments_in_file)(file) for file in files
        )

    def replace_tokens(self, input_directory: Path, output_directory: Path, operation: str) -> None:
        """Perform token replacement on all text files in a directory.

        Args:
            input_directory: Directory with input zip files.
            output_directory: Directory for output zip files.
            operation: Either 'family' or 'program'.
        """
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.operation = operation

        # Uncompress files, replace tokens, compress files
        fc = FileCompressor(self.input_directory, self.output_directory, self.n_jobs)
        fc.unzip()
        self.replace_instruments()
        fc.zip()
        logger.info("%s complete", self.operation)

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

    # Choose directory to process for family
    # input_directory = Path(".../encoded_samples/validate/family").resolve()
    # output_directory = input_directory.parent / "program"

    # # programize files
    # familizer.to_program(input_directory, output_directory)
