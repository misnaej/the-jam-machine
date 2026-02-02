"""Pick out MIDI files based on a reference file.

Takes a reference file as input containing the md5 hash of tracks to copy.
This reference file is created by midi_stats.py and refined in mmd_metadata.py.
Searches for all MIDI files in the input folder and copies matches to output.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..utils import copy_file, get_files

logger = logging.getLogger(__name__)


def pick_midis(input_dir: Path, output_dir: Path, reference_file: Path) -> None:
    """Copy MIDI files matching a reference list to the output directory.

    Args:
        input_dir: Directory to search for MIDI files.
        output_dir: Directory to copy matching files to.
        reference_file: CSV file with md5 hashes of tracks to copy.
    """
    # create output folder if it does not already exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load file in which we have the md5 hash of the tracks we want to copy
    reference = pd.read_csv(reference_file)

    # get all midi files from the folder and subfolders that match the reference file
    file_paths = get_files(input_dir, "mid", recursive=True)
    file_paths = [f for f in file_paths if f.stem in list(reference.md5)]

    # copy all files from the file_paths list to the output folder
    for f in file_paths:
        copy_file(f, output_dir)

    logger.info("All tracks copied successfully")


if __name__ == "__main__":
    # Select paths
    input_dir = Path("data/lmd_full/").resolve()
    output_dir = Path("data/lmd_new/").resolve()
    reference_file = Path("data/electronic_artists.csv").resolve()

    # Run function
    pick_midis(input_dir, output_dir, reference_file)
