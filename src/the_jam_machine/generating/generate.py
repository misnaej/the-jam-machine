"""Main orchestrator for MIDI text generation."""

import logging
from typing import TYPE_CHECKING

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
        model: "GPT2LMHeadModel",
        tokenizer: "GPT2Tokenizer",
        piece_by_track: list | None = None,
    ) -> None:
        """Initialize the generator.

        Args:
            model: The GPT-2 language model.
            tokenizer: The tokenizer for the model.
            piece_by_track: Optional existing piece state to restore.
        """
        if piece_by_track is None:
            piece_by_track = []

        self.tokenizer = tokenizer

        # Initialize components
        self.engine = GenerationEngine(model, tokenizer)
        self.piece = PieceBuilder(piece_by_track)
        self.prompts = PromptHandler()

        # Configuration
        self.force_sequence_length = True

    def set_nb_bars_generated(self, n_bars: int = 8) -> None:
        """Set the number of bars to generate.

        Args:
            n_bars: Number of bars (default 8 for this model).
        """
        self.prompts.n_bars = n_bars

    def set_force_sequence_length(self, force_sequence_length: bool = True) -> None:
        """Set whether to force exact sequence length.

        Args:
            force_sequence_length: If True, regenerates until correct length.
        """
        self.force_sequence_length = force_sequence_length

    def set_improvisation_level(self, level: int) -> None:
        """Set the improvisation level (n-gram penalty).

        Args:
            level: N-gram size for repetition penalty (0 = no penalty).
        """
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
        input_prompt: str = "PIECE_START ",
        instrument: str | None = None,
        density: int | None = None,
        temperature: float | None = None,
        verbose: bool = True,
        expected_length: int | None = None,
    ) -> str:
        """Generate until TRACK_END token is reached.

        Args:
            input_prompt: Starting prompt.
            instrument: Optional instrument to add to prompt.
            density: Optional density to add to prompt.
            temperature: Sampling temperature (required).
            verbose: Whether to log status.
            expected_length: Expected number of bars.

        Returns:
            Full generated piece (prompt + generated).

        Raises:
            ValueError: If temperature is None.
        """
        if expected_length is None:
            expected_length = self.prompts.n_bars

        if instrument is not None:
            input_prompt = f"{input_prompt}TRACK_START INST={instrument} "
            if density is not None:
                input_prompt = f"{input_prompt}DENSITY={density} "

        if instrument is None and density is not None:
            logger.warning("Density cannot be defined without an instrument")

        if temperature is None:
            raise ValueError("Temperature must be defined")

        if verbose:
            logger.info(
                "Generating %s - Density %s - temperature %s", instrument, density, temperature
            )

        bar_count_checks = False
        failed = 0

        while not bar_count_checks:
            full_piece = self.engine.generate(input_prompt, temperature, verbose=verbose)
            generated = TrackBuilder.get_new_content(full_piece, input_prompt)
            bar_count_checks, bar_count = bar_count_check(generated, expected_length)

            if not self.force_sequence_length:
                bar_count_checks = True

            if not bar_count_checks and self.force_sequence_length:
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

            if failed > 2:
                bar_count_checks = True

        return full_piece

    def generate_one_new_track(
        self,
        instrument: str,
        density: int,
        temperature: float,
        input_prompt: str = "PIECE_START ",
    ) -> str:
        """Generate a new track and add it to the piece.

        Args:
            instrument: Instrument identifier.
            density: Note density level.
            temperature: Sampling temperature.
            input_prompt: Starting prompt (usually current piece).

        Returns:
            Full piece text including new track.
        """
        self.piece.init_track(instrument, density, temperature)
        full_piece = self._generate_until_track_end(
            input_prompt=input_prompt,
            instrument=instrument,
            density=density,
            temperature=temperature,
        )

        track = TrackBuilder.get_last_track(full_piece)
        self.piece.add_bars_to_track(-1, track)
        return self.get_piece_text()

    def generate_piece(
        self,
        instrument_list: list[str],
        density_list: list[int],
        temperature_list: list[float],
    ) -> str:
        """Generate a complete piece with multiple tracks.

        Each track is generated based on a prompt containing previously
        generated tracks.

        Args:
            instrument_list: List of instruments to generate.
            density_list: Density for each instrument.
            temperature_list: Temperature for each instrument.

        Returns:
            Complete piece text.
        """
        generated_piece = "PIECE_START "
        for instrument, density, temperature in zip(
            instrument_list, density_list, temperature_list, strict=True
        ):
            generated_piece = self.generate_one_new_track(
                instrument,
                density,
                temperature,
                input_prompt=generated_piece,
            )

        self._check_for_errors()
        return generated_piece

    def generate_one_more_bar(self, track_index: int) -> None:
        """Generate one additional bar for a track.

        Args:
            track_index: Track to extend.
        """
        processed_prompt = self.prompts.build_next_bar_prompt(self.piece, track_index)
        prompt_plus_bar = self._generate_until_track_end(
            input_prompt=processed_prompt,
            temperature=self.piece.get_track_temperature(track_index),
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
