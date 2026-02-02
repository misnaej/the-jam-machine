"""Extract metadata from the MMD dataset and add it to statistics file.

Uses the fuzzywuzzy library to compare strings and find duplicates.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path
from fuzzywuzzy import fuzz

from ..utils import load_jsonl


class MetadataExtractor:
    """Extract metadata from the MMD dataset and add to statistics file.

    Attributes:
        stats_path: Path to the statistics file from MidiStats.
        title_artist_path: Path to the title_artist jsonl MMD file.
        genre_path: Path to the genre jsonl MMD file.
    """

    def __init__(
        self,
        stats_path: str | Path,
        title_artist_path: str | Path,
        genre_path: str | Path,
    ) -> None:
        """Initialize the metadata extractor.

        Args:
            stats_path: Path to statistics CSV file.
            title_artist_path: Path to title_artist JSONL file.
            genre_path: Path to genre JSONL file.
        """
        self.stats_path = stats_path
        self.title_artist_path = title_artist_path
        self.genre_path = genre_path
        self.threshold: int = 75
        self.stats: pd.DataFrame = pd.DataFrame()
        self.names_df: pd.DataFrame = pd.DataFrame()
        self.genre_df: pd.DataFrame = pd.DataFrame()
        self.duplicates: pd.Series = pd.Series()

    def get_single_artist_title(self, row: list) -> tuple[str, str]:
        """Extract the artist and title from a scraped data row.

        Args:
            row: Row data from scraped results.

        Returns:
            Tuple of (artist, title).
        """
        try:
            artist = row[0][1]
            title = row[0][0]
            return artist, title
        except Exception:
            artist = row[0][0]
            title = "unknown"
            return artist, title

    def get_artist_and_titles(self) -> None:
        """Extract artist and title from the MMD scraped data."""
        title_artist = self.names_df["title_artist"].apply(self.get_single_artist_title)
        self.names_df["artist"] = title_artist.apply(lambda x: x[0])
        self.names_df["title"] = title_artist.apply(lambda x: x[1])
        self.names_df.drop("title_artist", axis=1, inplace=True)

    def get_genre(self) -> None:
        """Extract genre from the genre dataframe."""
        self.genre_df["genre"] = self.genre_df["genre"].apply(lambda x: x[0])
        self.genre_df = self.genre_df.explode("genre")

    def string_cleaner(self, string: str) -> str:
        """Clean unwanted characters from a string.

        Args:
            string: Input string to clean.

        Returns:
            Cleaned string.
        """
        unwanted_characters = [",", "_", "\n"]
        string = re.sub("|".join(unwanted_characters), "", string)
        string = re.sub(r"\([^)]*\)", "", string)
        string = re.sub(r"\.\d+", "", string)
        string = re.sub(r"(?<!^)(?=[A-Z])", " ", string)
        return string

    def find_and_replace_duplicates(self, str_list: list[str]) -> list[str]:
        """Compare strings and replace duplicates with canonical versions.

        Args:
            str_list: List of strings to deduplicate.

        Returns:
            List with duplicates replaced by canonical strings.
        """
        str_list = [self.string_cleaner(string) for string in str_list]
        similar_strs: list[str | None] = [None] * len(str_list)

        for i, s in enumerate(str_list):
            wrong_strs = ["karaoke", "reprise", "solo", "acoustic"]
            has_wrong_str = any(
                fuzz.partial_ratio(s, wrong_str) > self.threshold
                for wrong_str in wrong_strs
            )
            if similar_strs[i] is None and "," not in s and not has_wrong_str:
                for j, other_strs in enumerate(str_list):
                    is_similar = fuzz.token_sort_ratio(s, other_strs) > self.threshold
                    if similar_strs[j] is None and is_similar:
                        similar_strs[j] = s

        return [
            s if s is not None else str_list[i] for i, s in enumerate(similar_strs)
        ]

    def get_mmd_artist_genre(self) -> None:
        """Load and process MMD scraped data."""
        names = load_jsonl(self.title_artist_path)
        genre = load_jsonl(self.genre_path)
        self.names_df = pd.DataFrame(names)
        self.genre_df = pd.DataFrame(genre)
        self.get_artist_and_titles()
        self.get_genre()

    def merge_mmd_data(self) -> None:
        """Merge MMD data with statistics dataframe."""
        stats = pd.read_csv(self.stats_path)
        name_genres_df = self.names_df.merge(self.genre_df, on="md5", how="left")
        self.stats = stats.merge(name_genres_df, on="md5", how="left")

    def deduplicate_artists(self) -> None:
        """Find and replace duplicate artist names."""
        self.stats.rename(columns={"artist": "artist_old"}, inplace=True)
        self.stats.rename(columns={"title": "title_old"}, inplace=True)

        unique_artists = self.stats["artist_old"].unique()
        similar_artists = self.find_and_replace_duplicates(unique_artists)

        df_artists = pd.DataFrame(
            {"artist_old": unique_artists, "artist_new": similar_artists}
        )
        self.stats["artist"] = self.stats["artist_old"].replace(
            df_artists.set_index("artist_old")["artist_new"]
        )

    def deduplicate_genre(self) -> None:
        """Get most common genre per artist and remove duplicates."""
        self.stats["genre"] = self.stats.groupby("artist")["genre"].transform(
            lambda x: x.value_counts().index[0]
        )
        self.stats.drop_duplicates(subset=["md5"], inplace=True)

    def deduplicate_titles(self) -> None:
        """Find and replace duplicate song titles per artist."""
        for artist in self.stats["artist_old"].unique():
            df_temp = self.stats[self.stats["artist_old"] == artist]
            unique_titles = df_temp["title_old"]
            similar_titles = self.find_and_replace_duplicates(unique_titles)

            df_titles = pd.DataFrame(
                {"title_old": unique_titles, "title_new": similar_titles},
                index=df_temp.index,
            )
            self.stats.loc[df_titles.index, "title"] = df_titles["title_new"]

    def deduplicate_all(self) -> None:
        """Run all deduplication steps."""
        self.deduplicate_artists()
        self.deduplicate_genre()
        self.deduplicate_titles()
        self.stats.drop(columns=["artist_old", "title_old"], inplace=True)

    def extract(self, threshold: int = 75) -> None:
        """Extract and process metadata from MMD scraped data.

        Loads MMD metadata and statistics, merges them, and deduplicates
        using fuzzy string matching.

        Args:
            threshold: Fuzzy matching threshold (0-100). Higher = stricter.
        """
        self.threshold = threshold
        self.get_mmd_artist_genre()
        self.merge_mmd_data()
        self.deduplicate_all()

    def export_to_csv(self, output_path: str | Path) -> None:
        """Export statistics to CSV file.

        Args:
            output_path: Path for output CSV file.
        """
        self.stats.to_csv(output_path, index=False)

    def list_duplicates(self) -> None:
        """Find songs with multiple versions in the dataset."""
        self.duplicates = (
            self.stats.groupby(["artist", "title"]).size().sort_values(ascending=False)
        )

    def filter_midis(
        self,
        n_instruments: int = 12,
        four_to_the_floor: bool = True,
        single_version: bool = True,
    ) -> None:
        """Filter dataset based on criteria.

        Args:
            n_instruments: Maximum number of instruments to include.
            four_to_the_floor: Only include songs in 4/4 time.
            single_version: Only include best version of each song.
        """
        self.stats = self.stats[self.stats["n_instruments"] <= n_instruments]
        if four_to_the_floor:
            self.stats = self.stats[self.stats["four_to_the_floor"] == True]  # noqa: E712
        if single_version:
            self.stats.sort_values(
                "number_of_notes_per_second", ascending=False
            ).groupby(["title", "artist"]).first()


if __name__ == "__main__":
    # Pick paths
    stats_path = "data/music_picks/statistics.csv"
    title_artist_path = "data/mmd_matches/MMD_scraped_title_artist.jsonl"
    genre_path = "data/mmd_matches/MMD_scraped_genre.jsonl"
    output_path = "data/music_picks/statistics_deduplicated.csv"

    # Extract metadata
    meta = MetadataExtractor(stats_path, title_artist_path, genre_path)
    meta.extract(threshold=75)
    meta.filter_midis(n_instruments=12, four_to_the_floor=True, single_version=True)
    meta.export_to_csv(output_path)
