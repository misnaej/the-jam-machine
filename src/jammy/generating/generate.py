"""Main orchestrator for MIDI text generation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .config import GenerationConfig, TrackConfig
from .generation_engine import GenerationEngine
from .piece_builder import PieceBuilder
from .prompt_handler import PromptHandler
from .track_builder import TrackBuilder
from .utils import bar_count_check, forcing_bar_count

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, GPT2Tokenizer

logger = logging.getLogger(__name__)


class GenerateMidiText:
    """Main orchestrator for MIDI text generation.

    This class coordinates the generation of MIDI text sequences using
    a GPT-2 model. It delegates to specialized components for model
    interaction, piece state management, track operations, and prompt
    construction.

    LOGIC:

    FOR GENERATING FROM SCRATCH:
    - generate_one_new_track() -> _generate_until_track_end()

    FOR GENERATING NEW BARS:
    - generate_one_more_bar() -> prompts.build_next_bar_prompt() + _generate_until_track_end()

    Attributes:
        engine: Low-level model interaction handler.
        piece: Piece state manager.
        prompts: Prompt construction handler.
    """

    def __init__(
        self,
        model: GPT2LMHeadModel,
        tokenizer: GPT2Tokenizer,
        piece_by_track: list | None = None,
        config: GenerationConfig | None = None,
    ) -> None:
        """Initialize the generator.

        Args:
            model: The GPT-2 language model.
            tokenizer: The tokenizer for the model.
            piece_by_track: Optional existing piece state to restore.
            config: Optional generation configuration (uses defaults if None).
        """
        if piece_by_track is None:
            piece_by_track = []
        if config is None:
            config = GenerationConfig()

        self.tokenizer = tokenizer
        self.config = config

        # Initialize components
        self.engine = GenerationEngine(model, tokenizer)
        self.piece = PieceBuilder(piece_by_track)
        self.prompts = PromptHandler(
            n_bars=config.n_bars,
            max_length=config.max_prompt_length,
        )
        self.engine.generate_until = config.generate_until_token
        self.engine.set_improvisation_level(config.improvisation_level)

    def set_nb_bars_generated(self, n_bars: int = 8) -> None:
        """Set the number of bars to generate.

        Args:
            n_bars: Number of bars (default 8 for this model).
        """
        self.config.n_bars = n_bars
        self.prompts.n_bars = n_bars

    def set_force_sequence_length(self, force_sequence_length: bool = True) -> None:
        """Set whether to force exact sequence length.

        Args:
            force_sequence_length: If True, regenerates until correct length.
        """
        self.config.force_sequence_length = force_sequence_length

    def set_improvisation_level(self, level: int) -> None:
        """Set the improvisation level (n-gram penalty).

        Args:
            level: N-gram size for repetition penalty (0 = no penalty).
        """
        self.config.improvisation_level = level
        self.engine.set_improvisation_level(level)

    def reset_temperature(self, track_id: int, temperature: float) -> None:
        """Reset the temperature for a specific track.

        Args:
            track_id: Index of the track.
            temperature: New temperature value.
        """
        self.piece.set_track_temperature(track_id, temperature)

    def delete_track(self, track_id: int) -> None:
        """Delete a track from the piece.

        Args:
            track_id: Track index to delete.
        """
        self.piece.delete_track(track_id)

    def get_track_text(self, track_id: int) -> str:
        """Get full track text from state.

        Args:
            track_id: Track index.

        Returns:
            Track text with TRACK_END.
        """
        return self.piece.build_track_text(track_id)

    def get_piece_text(self) -> str:
        """Get full piece text from state.

        Returns:
            Complete piece text.
        """
        return self.piece.build_piece_text()

    # Legacy alias for backwards compatibility during transition
    def get_whole_piece_from_bar_dict(self) -> str:
        """Get full piece text from state (legacy alias).

        Returns:
            Complete piece text.
        """
        return self.get_piece_text()

    # Legacy alias
    def get_whole_track_from_bar_dict(self, track_id: int) -> str:
        """Get full track text from state (legacy alias).

        Args:
            track_id: Track index.

        Returns:
            Track text with TRACK_END.
        """
        return self.get_track_text(track_id)

    # Legacy alias
    def delete_one_track(self, track_id: int) -> None:
        """Delete a track from the piece (legacy alias).

        Args:
            track_id: Track index to delete.
        """
        self.delete_track(track_id)

    def _generate_until_track_end(
        self,
        track: TrackConfig,
        input_prompt: str = "PIECE_START ",
        add_track_header: bool = True,
        verbose: bool = True,
        expected_length: int | None = None,
    ) -> str:
        """Generate until end token is reached.

        Args:
            track: Track configuration (instrument, density, temperature).
            input_prompt: Starting prompt.
            add_track_header: Whether to add TRACK_START/INST/DENSITY to prompt.
            verbose: Whether to log status.
            expected_length: Expected number of bars.

        Returns:
            Full generated piece (prompt + generated).
        """
        if expected_length is None:
            expected_length = self.prompts.n_bars

        if add_track_header:
            input_prompt = f"{input_prompt}TRACK_START INST={track.instrument} "
            input_prompt = f"{input_prompt}DENSITY={track.density} "

        if verbose:
            logger.info(
                "Generating %s - Density %s - temperature %s",
                track.instrument,
                track.density,
                track.temperature,
            )

        bar_count_checks = False
        failed = 0

        while not bar_count_checks:
            full_piece = self.engine.generate(input_prompt, track.temperature, verbose=verbose)
            generated = TrackBuilder.get_new_content(full_piece, input_prompt)
            bar_count_checks, bar_count = bar_count_check(generated, expected_length)

            if not self.config.force_sequence_length:
                bar_count_checks = True

            if not bar_count_checks and self.config.force_sequence_length:
                if failed > -1:
                    full_piece, bar_count_checks = forcing_bar_count(
                        input_prompt,
                        generated,
                        bar_count,
                        expected_length,
                    )
                else:
                    logger.info("Wrong length - Regenerating")

            if not bar_count_checks:
                failed += 1

            if failed > self.config.max_retries:
                bar_count_checks = True

        return full_piece

    def generate_one_new_track(
        self,
        track: TrackConfig,
        input_prompt: str = "PIECE_START ",
    ) -> str:
        """Generate a new track and add it to the piece.

        Args:
            track: Track configuration (instrument, density, temperature).
            input_prompt: Starting prompt (usually current piece).

        Returns:
            Full piece text including new track.
        """
        self.piece.init_track(track.instrument, track.density, track.temperature)
        full_piece = self._generate_until_track_end(
            track=track,
            input_prompt=input_prompt,
        )

        generated_track = TrackBuilder.get_last_track(full_piece)
        self.piece.add_bars_to_track(-1, generated_track)
        return self.get_piece_text()

    def generate_piece(self, tracks: list[TrackConfig]) -> str:
        """Generate a complete piece with multiple tracks.

        Each track is generated based on a prompt containing previously
        generated tracks.

        Args:
            tracks: List of track configurations.

        Returns:
            Complete piece text.
        """
        generated_piece = "PIECE_START "
        for track in tracks:
            generated_piece = self.generate_one_new_track(
                track,
                input_prompt=generated_piece,
            )

        self._check_for_errors()
        return generated_piece

    def generate_one_more_bar(self, track_index: int) -> None:
        """Generate one additional bar for a track.

        Args:
            track_index: Track to extend.
        """
        track_config = self.piece.get_track_config(track_index)
        processed_prompt = self.prompts.build_next_bar_prompt(self.piece, track_index)
        prompt_plus_bar = self._generate_until_track_end(
            track=track_config,
            input_prompt=processed_prompt,
            add_track_header=False,
            expected_length=1,
            verbose=False,
        )
        added_bar = TrackBuilder.extract_new_bar(prompt_plus_bar)
        self.piece.add_bars_to_track(track_index, added_bar)

    def generate_n_more_bars(
        self,
        n_bars: int,
        only_this_track: int | None = None,
    ) -> None:
        """Generate n additional bars for all or one track.

        Args:
            n_bars: Number of bars to add.
            only_this_track: If set, only generate for this track.
        """
        logger.info("Adding %d more bars to the piece", n_bars)

        for bar_id in range(n_bars):
            logger.info("Added bar #%d", bar_id + 1)
            for i in range(self.piece.get_track_count()):
                track = self.piece.get_track(i)
                if only_this_track is None or i == only_this_track:
                    logger.info("Track: %s", track["label"])
                    self.generate_one_more_bar(i)

        self._check_for_errors()

    def _check_for_errors(self, piece: str | None = None) -> None:
        """Check piece for invalid tokens.

        Args:
            piece: Piece text to check (uses current state if None).
        """
        if piece is None:
            piece = self.get_piece_text()

        for idx, midi_token in enumerate(piece.split(" ")):
            if midi_token not in self.tokenizer.vocab or midi_token == "UNK":  # noqa: S105
                logger.warning(
                    "Token not found in the piece at %d: %s",
                    idx,
                    midi_token,
                )
                logger.warning("Context: %s", piece.split(" ")[idx - 5 : idx + 5])


if __name__ == "__main__":
    pass
