"""Section construction for MIDI event sequences.

Groups instrument events into n-bar sections for the piece structure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from miditok import Event

from jammy.embedding.familizer import Familizer

if TYPE_CHECKING:
    from miditoolkit import Instrument


def define_instrument(midi_tok_instrument: Instrument, familized: bool = False) -> int | str:
    """Define the instrument token from the MIDI token instrument.

    Args:
        midi_tok_instrument: The miditoolkit Instrument object.
        familized: Whether the instrument needs to be familized.

    Returns:
        The instrument identifier (program number, family number, or "Drums").
    """
    instrument: int | str = (
        midi_tok_instrument.program if not midi_tok_instrument.is_drum else "Drums"
    )
    if familized and not midi_tok_instrument.is_drum:
        familizer = Familizer()
        family_number = familizer.get_family_number(int(instrument))
        if family_number is not None:
            instrument = family_number

    return instrument


def initiate_track_in_section(instrument: int | str, track_index: int) -> list[Event]:
    """Initialize a track section with start and instrument events.

    Args:
        instrument: The instrument identifier (program number or "Drums").
        track_index: The index of the track.

    Returns:
        List of events starting a new track section.
    """
    return [
        Event("Track-Start", track_index),
        Event("Instrument", instrument),
    ]


def terminate_track_in_section(section: list[Event], track_index: int) -> tuple[list[Event], int]:
    """Terminate a track section with an end event.

    Args:
        section: The current section event list.
        track_index: The current track index.

    Returns:
        Tuple of (updated section, incremented track index).
    """
    section.append(Event("Track-End", track_index))
    track_index += 1
    return section, track_index


def make_sections(
    midi_events: list[list[Event]],
    instruments: list[Instrument],
    n_bar: int = 8,
    familized: bool = False,
) -> list[list[list[Event]]]:
    """Make sections of n_bar bars for each instrument.

    Creates midi_sections[inst_sections][sections] structure because files
    can be encoded in many sections of n_bar.

    Args:
        midi_events: List of instrument event lists.
        instruments: List of miditoolkit Instrument objects.
        n_bar: Number of bars per section. Defaults to 8.
        familized: Whether to familize instruments.

    Returns:
        Nested list of sections per instrument.
    """
    midi_sections = []
    for i, inst_events in enumerate(midi_events):
        inst_section = []
        track_index = 0
        instrument = define_instrument(instruments[i], familized=familized)
        section = initiate_track_in_section(instrument, track_index)
        for ev_idx, event in enumerate(inst_events):
            section.append(event)
            if ev_idx == len(inst_events) - 1 or (
                event.type == "Bar-End" and int(event.value + 1) % n_bar == 0
            ):
                section, track_index = terminate_track_in_section(section, track_index)
                inst_section.append(section)

                if ev_idx < len(inst_events) - 1:
                    section = initiate_track_in_section(instrument, track_index)

        midi_sections.append(inst_section)

    return midi_sections


def sections_to_piece(midi_sections: list[list[list[Event]]]) -> list[Event]:
    """Combine all sections into one piece.

    Sections are combined as follows:
    'Piece_Start
    Section 1 Instrument 1
    Section 1 Instrument 2
    Section 1 Instrument 3
    Section 2 Instrument 1
    ...'

    Args:
        midi_sections: Nested list of sections per instrument
            (shape: [instruments][sections][events]).

    Returns:
        Flat list of events representing the complete piece.
    """
    piece: list[Event] = []
    max_total_sections = max(map(len, midi_sections))
    for i in range(max_total_sections):
        # adding piece start event at the beginning of each section
        piece += [Event("Piece-Start", 1)]
        for inst_sections in midi_sections:
            if i < len(inst_sections):
                piece += inst_sections[i]
    return piece
