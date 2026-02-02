"""Decoder module for converting text tokens to MIDI files."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from miditok import Event

from ..constants import DRUMS_BEAT_QUANTIZATION, NONE_DRUMS_BEAT_QUANTIZATION
from ..utils import (
    beat_to_int_dec_base,
    get_event,
    get_miditok,
    int_dec_base_to_beat,
    readFromFile,
)
from .familizer import Familizer

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
        piece_events = self.text_to_events(text)
        piece_events = self.get_track_ids(piece_events)
        self.check_for_duplicated_events(piece_events)
        inst_events = self.piece_to_inst_events(piece_events)
        inst_events = self.get_bar_ids(inst_events)
        events = self.add_missing_timeshifts_in_a_bar(inst_events)
        events = self.remove_unwanted_tokens(events)
        events = self.aggregate_timeshifts(events)
        events = self.add_velocity(events)
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
            logger.info("midi file written: %s", filename)

        return midi

    @staticmethod
    def text_to_events(text: str, verbose: bool = False) -> list[Event]:
        """Convert text tokens to a list of MidiTok events.

        Args:
            text: Text token string to parse.
            verbose: Whether to log detailed quantization information.

        Returns:
            List of MidiTok Event objects.
        """
        events: list[Event] = []
        instrument = "drums"
        track_index = -1
        cumul_time_delta = 0
        max_cumul_time_delta = 0

        for word in text.split(" "):
            _event = word.split("=")
            value = _event[1] if len(_event) > 1 else None
            beyond_quantization = False  # needs to be reset for each event

            if _event[0] == "INST":
                track_index += 1
                bar_value = 0
                # get the instrument for passing in get_event when time_delta
                # for proper quantization
                instrument = get_event(_event[0], value).value

                # how much delta can be added before over quantization
                max_cumul_time_delta = (
                    DRUMS_BEAT_QUANTIZATION * 4
                    if instrument.lower() == "drums"
                    else NONE_DRUMS_BEAT_QUANTIZATION * 4
                )

            if _event[0] == "BAR_START":
                bar_value += 1
                value = bar_value
                # reseting cumul_time_delta
                cumul_time_delta = 0

            # ----- hack to prevent over quantization -----
            # NOT IDEAL - the model should not output these events
            if _event[0] == "TIME_DELTA":
                cumul_time_delta += int(_event[1])
                if cumul_time_delta > max_cumul_time_delta:
                    beyond_quantization = True
                    cumul_time_delta -= int(_event[1])

            if _event[0] == "NOTE_ON" and cumul_time_delta >= max_cumul_time_delta:
                beyond_quantization = True

            if beyond_quantization and verbose:
                logger.debug(
                    "instrument %s - bar %s - skipping %s because of over quantization",
                    instrument,
                    bar_value,
                    _event[0],
                )
            # ---------------------------------------------

            # getting event
            event = get_event(_event[0], value, instrument)
            if event and not beyond_quantization:
                if event.type == "Bar-End":
                    if verbose:
                        logger.debug(
                            "instrument %s - bar %s - Cumulated TIME_DELTA = %s",
                            instrument,
                            bar_value,
                            cumul_time_delta,
                        )
                    cumul_time_delta = 0

                # appending event
                events.append(event)

        return events

    @staticmethod
    def get_track_ids(events: list[Event]) -> list[Event]:
        """Add track IDs to track start and end events.

        Args:
            events: List of MidiTok Event objects.

        Returns:
            Modified list of events with track IDs assigned.
        """
        track_id = 0
        for i, event in enumerate(events):
            if event.type == "Track-Start":
                events[i].value = track_id
            if event.type == "Track-End":
                events[i].value = track_id
                track_id += 1
        return events

    @staticmethod
    def piece_to_inst_events(piece_events: list[Event]) -> list[dict[str, Any]]:
        """Convert piece events to instrument-grouped events.

        Args:
            piece_events: List of events with Notes, Timeshifts, Bars, Tracks.

        Returns:
            List of dictionaries, each containing 'Instrument', 'channel',
            and 'events' keys for one instrument.
        """
        inst_events: list[dict[str, Any]] = []
        current_track = -1  # so does not start before Track-Start is encountered
        for event in piece_events:
            # creates a new entry in the dictionary when "Track-Start" event is encountered
            if event.type == "Track-Start":
                current_track = event.value
                if len(inst_events) == event.value:
                    inst_events.append({})
                    inst_events[current_track]["channel"] = current_track
                    inst_events[current_track]["events"] = []
            # append event to the track
            if current_track != -1:
                inst_events[current_track]["events"].append(event)

            if event.type == "Instrument":
                inst_events[current_track]["Instrument"] = event.value
        # TODO: needs cleaning Track-start and track end
        return inst_events

    @staticmethod
    def get_bar_ids(inst_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Track bar index for each instrument and save them in the MidiTok Events.

        Args:
            inst_events: List of instrument event dictionaries.

        Returns:
            Modified list with bar IDs assigned to bar events.
        """
        for inst_index, inst_event in enumerate(inst_events):
            bar_idx = 0
            for event_index, event in enumerate(inst_event["events"]):
                if event.type == "Bar-Start" or event.type == "Bar-End":
                    inst_events[inst_index]["events"][event_index].value = bar_idx
                if event.type == "Bar-End":
                    bar_idx += 1
        return inst_events

    @staticmethod
    def add_missing_timeshifts_in_a_bar(
        inst_events: list[dict[str, Any]],
        beat_per_bar: int = 4,
        verbose: bool = False,
    ) -> list[dict[str, Any]]:
        """Add missing time shifts in bar to ensure each bar has 4 beats.

        Handles the problem of a missing time shift if notes do not last until
        the end of the bar, and handles empty bars defined only by BAR_START BAR_END.

        Args:
            inst_events: List of instrument event dictionaries.
            beat_per_bar: Number of beats per bar (default 4).
            verbose: Whether to log detailed information.

        Returns:
            New list of instrument events with corrected time shifts.
        """
        new_inst_events: list[dict[str, Any]] = []
        for index, inst_event in enumerate(inst_events):
            new_inst_events.append({})
            new_inst_events[index]["Instrument"] = inst_event["Instrument"]
            new_inst_events[index]["channel"] = index
            new_inst_events[index]["events"] = []

            beat_count = 0
            for event in inst_event["events"]:
                if event.type == "Bar-Start":
                    beat_count = 0

                if event.type == "Time-Shift":
                    beat_count += int_dec_base_to_beat(event.value)

                if event.type == "Bar-End" and beat_count < beat_per_bar:
                    time_shift_to_add = beat_to_int_dec_base(beat_per_bar - beat_count)
                    new_inst_events[index]["events"].append(Event("Time-Shift", time_shift_to_add))
                    beat_count += int_dec_base_to_beat(time_shift_to_add)

                if event.type == "Bar-End" and verbose:
                    logger.debug(
                        "Instrument %s - %s - Bar %s - beat_count = %s",
                        index,
                        inst_event["Instrument"],
                        event.value,
                        beat_count,
                    )
                if event.type == "Bar-End" and beat_count > beat_per_bar:
                    logger.warning(
                        "Instrument %s - %s - Bar %s - Beat count exceeded",
                        index,
                        inst_event["Instrument"],
                        event.value,
                    )
                new_inst_events[index]["events"].append(event)

        return new_inst_events

    # TODO: Implement this method
    @staticmethod
    def check_bar_count_in_section(
        inst_events: list[dict[str, Any]],
        bars_in_sections: int = 8,  # noqa: ARG004
    ) -> list[dict[str, Any]]:
        """Check bar count in section.

        Args:
            inst_events: List of instrument event dictionaries.
            bars_in_sections: Expected number of bars per section.

        Returns:
            New list of instrument events (currently unimplemented).
        """
        new_inst_events: list[dict[str, Any]] = []
        for _index, _inst_event in enumerate(inst_events):
            pass
        return new_inst_events

    @staticmethod
    def remove_unwanted_tokens(
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Remove structural tokens not needed for MIDI conversion.

        Removes Bar-Start, Bar-End, Track-Start, Track-End, Piece-Start,
        and Instrument events.

        Args:
            events: List of instrument event dictionaries.

        Returns:
            Modified list with unwanted tokens removed.
        """
        for inst_index, inst_event in enumerate(events):
            new_inst_event = []
            for event in inst_event["events"]:
                if event.type not in (
                    "Bar-Start",
                    "Bar-End",
                    "Track-Start",
                    "Track-End",
                    "Piece-Start",
                    "Instrument",
                ):
                    new_inst_event.append(event)
            # replace the events list with the new one
            events[inst_index]["events"] = new_inst_event
        return events

    @staticmethod
    def check_for_duplicated_events(event_list: list[Event]) -> None:
        """Check for and log any duplicate consecutive events.

        Args:
            event_list: List of MidiTok Event objects to check.
        """
        for i, event in enumerate(event_list):
            if (
                i < len(event_list) - 1
                and event.type == event_list[i + 1].type
                and event.value == event_list[i + 1].value
            ):
                logger.warning("Duplicate event found at index %s : %s", i, event)

    @staticmethod
    def add_timeshifts(beat_values1: str, beat_values2: str) -> str:
        """Add two beat values in integer.decimal.base format.

        Args:
            beat_values1: First beat value (e.g., "0.3.8").
            beat_values2: Second beat value (e.g., "1.7.8").

        Returns:
            Sum of beat values (e.g., "2.2.8" for the example values).
        """
        value1 = int_dec_base_to_beat(beat_values1)
        value2 = int_dec_base_to_beat(beat_values2)
        return beat_to_int_dec_base(value1 + value2)

    def aggregate_timeshifts(
        self,
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Aggregate consecutive time shift events.

        Combines consecutive Time-Shift events into single events that may
        span more than a bar (e.g., Timeshift 4.0.8).

        Args:
            events: List of instrument event dictionaries.

        Returns:
            Modified list with aggregated time shifts.
        """
        for inst_index, inst_event in enumerate(events):
            new_inst_event = []
            for event in inst_event["events"]:
                if (
                    event.type == "Time-Shift"
                    and len(new_inst_event) > 0
                    and new_inst_event[-1].type == "Time-Shift"
                ):
                    new_inst_event[-1].value = self.add_timeshifts(
                        new_inst_event[-1].value, event.value
                    )
                else:
                    new_inst_event.append(event)

            events[inst_index]["events"] = new_inst_event
        return events

    @staticmethod
    def add_velocity(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Add default velocity to note events.

        Adds velocity 99 to note events since they are removed from text
        but needed to generate MIDI.

        Args:
            events: List of instrument event dictionaries.

        Returns:
            Modified list with velocity events added after Note-On events.
        """
        for inst_index, inst_event in enumerate(events):
            new_inst_event = []
            for event in inst_event["events"]:
                new_inst_event.append(event)
                if event.type == "Note-On":
                    new_inst_event.append(Event("Velocity", 99))
            events[inst_index]["events"] = new_inst_event
        return events

    def get_instruments_tuple(
        self,
        events: list[dict[str, Any]],
    ) -> tuple[tuple[int, int], ...]:
        """Return instruments tuple for MIDI generation.

        Args:
            events: List of instrument event dictionaries.

        Returns:
            Tuple of (program_number, is_drum) pairs for each instrument.
        """
        instruments = []
        for track in events:
            is_drum = 0
            if track["Instrument"].lower() == "drums":
                track["Instrument"] = 0
                is_drum = 1
            if self.familized and not is_drum:
                track["Instrument"] = Familizer(arbitrary=True).get_program_number(
                    int(track["Instrument"])
                )
            instruments.append((int(track["Instrument"]), is_drum))
        return tuple(instruments)


if __name__ == "__main__":
    # investigating the duplicates issues
    test_filename = "source/tests/20230305_150554"
    encoded_json = readFromFile(
        f"{test_filename}.json",
        isJSON=True,
    )
    encoded_text = encoded_json["generated_midi"]

    miditok = get_miditok()
    TextDecoder(miditok).get_midi(encoded_text, filename=test_filename)
