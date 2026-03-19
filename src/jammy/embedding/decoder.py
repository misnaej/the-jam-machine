"""Decoder module for converting text tokens to MIDI files."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from jammy.embedding import event_processing, text_parsing
from jammy.embedding.familizer import Familizer

if TYPE_CHECKING:
    from miditok import MIDILike
    from miditoolkit import MidiFile

logger = logging.getLogger(__name__)


class TextDecoder:
    """Decode text tokens into MIDI file format.

    This class converts text token representations into:
    1. A list of MIDI events
    2. A MIDI file via MidiTok and miditoolkit

    Attributes:
        tokenizer: MidiTok tokenizer instance.
        familized: Whether to use familized instrument mapping.

    Example:
        >>> decoder = TextDecoder(tokenizer)
        >>> midi = decoder.get_midi(
        ...     "PIECE_START TRACK_START INST=25 DENSITY=2 BAR_START..."
        ... )
    """

    def __init__(self, tokenizer: MIDILike, familized: bool = True) -> None:
        """Initialize the TextDecoder.

        Args:
            tokenizer: MidiTok tokenizer instance for token conversion.
            familized: Whether to use familized instrument mapping.
        """
        self.tokenizer = tokenizer
        self.familized = familized

    def decode(self, text: str) -> list[dict[str, Any]]:
        """Convert text tokens to instrument events.

        Args:
            text: Text token string (e.g., "PIECE_START TRACK_START INST=25...").

        Returns:
            List of event dictionaries for each instrument, containing
            'Instrument', 'channel', and 'events' keys.
        """
        piece_events = text_parsing.text_to_events(text)
        piece_events = text_parsing.get_track_ids(piece_events)
        event_processing.check_for_duplicated_events(piece_events)
        inst_events = text_parsing.piece_to_inst_events(piece_events)
        inst_events = text_parsing.get_bar_ids(inst_events)
        events = event_processing.add_missing_timeshifts_in_bar(inst_events)
        events = event_processing.remove_unwanted_tokens(events)
        events = event_processing.aggregate_timeshifts(events)
        events = event_processing.add_velocity(events)
        return events

    def tokenize(self, events: list[dict[str, Any]]) -> list[list[str]]:
        """Convert events to MidiTok tokens.

        Args:
            events: List of event dictionaries for each instrument.

        Returns:
            List of token lists for each instrument.
        """
        tokens = []
        for inst in events:
            tokens.append(self.tokenizer.events_to_tokens(inst["events"]))
        return tokens

    def get_midi(self, text: str, filename: str | None = None) -> MidiFile:
        """Convert text tokens to MIDI.

        Args:
            text: Text token string (e.g., "PIECE_START TRACK_START INST=25...").
            filename: Optional filename to write the MIDI file.

        Returns:
            MidiFile object from miditoolkit.
        """
        events = self.decode(text)
        tokens = self.tokenize(events)
        instruments = self.get_instruments_tuple(events)
        midi = self.tokenizer.tokens_to_midi(tokens, instruments)

        if filename is not None:
            midi.dump(f"{filename}")
            logger.info("MIDI file written: %s", filename)

        return midi

    def get_instruments_tuple(
        self,
        events: list[dict[str, Any]],
    ) -> tuple[tuple[int, int], ...]:
        """Return instruments tuple for MIDI generation.

        Args:
            events: List of instrument event dictionaries. Each dict must
                contain an 'Instrument' key with a string or int value.

        Returns:
            Tuple of (program_number, is_drum) pairs for each instrument,
            where is_drum is 1 for drums and 0 otherwise.
        """
        familizer = Familizer(arbitrary=True) if self.familized else None
        instruments = []
        for track in events:
            is_drum = 0
            program = track["Instrument"]
            if str(program).lower() == "drums":
                program = 0
                is_drum = 1
            elif familizer is not None:
                program = familizer.get_program_number(int(program))
            instruments.append((int(program), is_drum))
        return tuple(instruments)
