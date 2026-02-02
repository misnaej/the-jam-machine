# Design Audit Implementation Plan

**Date:** 2026-02-02
**Branch:** Feature branches created from `main`
**Scope:** `src/the_jam_machine/`

---

## Overview

This plan addresses design issues identified in the codebase audit, organized into 5 phases that can be implemented incrementally. Each phase is self-contained and results in a working codebase.

### Convention: Postponed Annotations

All files should use postponed annotation evaluation to avoid quoted type hints:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel

class MyClass:
    def __init__(self, model: GPT2LMHeadModel) -> None:  # No quotes needed
        pass
```

This is cleaner, less error-prone (typos caught by type checker), and the future Python default.

### Convention: Prefer Functions Over Classes

When splitting modules, use **module-level functions** instead of classes with only static methods.
Python modules are already namespaces - no need to wrap functions in a class.

```python
# ❌ Over-engineered - class with only static methods
class TimeShiftProcessor:
    @staticmethod
    def normalize(events: list[Event]) -> list[Event]: ...
    @staticmethod
    def combine(events: list[Event]) -> list[Event]: ...

# ✅ Pythonic - module functions
# time_processing.py
def normalize_timeshifts(events: list[Event]) -> list[Event]: ...
def combine_timeshifts(events: list[Event]) -> list[Event]: ...
```

**Use classes when:**
- You have instance state (attributes that vary per instance)
- Objects have a lifecycle (init, configure, use, cleanup)
- You need multiple instances with different configurations

**Use functions when:**
- Operations are stateless transformations
- You'd end up with all `@staticmethod` or `@classmethod`
- Data flows in, transformed data flows out

---

## Phase 1: Config Dataclasses for Generation

**Goal:** Replace repeated argument patterns with dataclasses (PR #2 feedback)

### 1.1 Create `src/the_jam_machine/generating/config.py`

```python
"""Configuration dataclasses for MIDI generation."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TrackConfig:
    """Configuration for a single track generation.

    Attributes:
        instrument: Instrument identifier (family number or "DRUMS").
        density: Note density level (1-3 typical).
        temperature: Sampling temperature (0.1-1.0).
    """
    instrument: str
    density: int
    temperature: float


@dataclass
class GenerationConfig:
    """Configuration for the generation engine.

    Attributes:
        n_bars: Number of bars to generate per section.
        force_sequence_length: Whether to regenerate until correct length.
        improvisation_level: N-gram penalty size (0 = no penalty).
        max_prompt_length: Maximum tokens in prompt before truncation.
        generate_until_token: Token that signals end of generation.
        max_retries: Maximum regeneration attempts before giving up.
    """
    n_bars: int = 8
    force_sequence_length: bool = True
    improvisation_level: int = 0
    max_prompt_length: int = 1500
    generate_until_token: str = "TRACK_END"
    max_retries: int = 2
```

### 1.2 Update `generate.py`

**Changes:**

1. Import `TrackConfig` and `GenerationConfig`
2. Accept `GenerationConfig` in `__init__` (optional, uses defaults)
3. Update `generate_one_new_track()` to accept `TrackConfig`
4. Update `_generate_until_track_end()` to use config internally
5. Update `generate_piece()` to accept `list[TrackConfig]`
6. Keep legacy signatures as overloaded methods for backwards compatibility

**Before:**
```python
def generate_one_new_track(
    self,
    instrument: str,
    density: int,
    temperature: float,
    input_prompt: str = "PIECE_START ",
) -> str:
```

**After:**
```python
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
        input_prompt=input_prompt,
        instrument=track.instrument,
        density=track.density,
        temperature=track.temperature,
    )
    # ...
```

**Before:**
```python
def generate_piece(
    self,
    instrument_list: list[str],
    density_list: list[int],
    temperature_list: list[float],
) -> str:
```

**After:**
```python
def generate_piece(self, tracks: list[TrackConfig]) -> str:
    """Generate a complete piece with multiple tracks.

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
```

### 1.3 Update `GenerateMidiText.__init__`

**Before:**
```python
def __init__(
    self,
    model: GPT2LMHeadModel,
    tokenizer: GPT2Tokenizer,
    piece_by_track: list | None = None,
) -> None:
    # ...
    self.force_sequence_length = True
```

**After:**
```python
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
        config: Generation configuration (uses defaults if None).
    """
    if piece_by_track is None:
        piece_by_track = []
    if config is None:
        config = GenerationConfig()

    self.config = config
    self.tokenizer = tokenizer

    # Initialize components
    self.engine = GenerationEngine(model, tokenizer)
    self.piece = PieceBuilder(piece_by_track)
    self.prompts = PromptHandler(n_bars=config.n_bars, max_length=config.max_prompt_length)

    # Apply config to engine
    self.engine.set_improvisation_level(config.improvisation_level)
```

### 1.4 Update `prompt_handler.py`

**Before:**
```python
MAX_PROMPT_LENGTH = 1500

class PromptHandler:
    def __init__(self) -> None:
        self.n_bars = 8
```

**After:**
```python
class PromptHandler:
    def __init__(self, n_bars: int = 8, max_length: int = 1500) -> None:
        """Initialize the prompt handler.

        Args:
            n_bars: Number of bars per generation section.
            max_length: Maximum prompt length in tokens.
        """
        self.n_bars = n_bars
        self.max_length = max_length
```

### 1.5 Update `app/playground.py`

**Before:**
```python
genesis.generate_one_new_track(inst, density, temp, input_prompt=input_prompt)
```

**After:**
```python
from the_jam_machine.generating.config import TrackConfig

track_config = TrackConfig(instrument=inst, density=density, temperature=temp)
genesis.generate_one_new_track(track_config, input_prompt=input_prompt)
```

### 1.6 Update `examples/generation_playground.py`

Apply similar changes to use `TrackConfig`.

### 1.7 Files Changed

| File | Action |
|------|--------|
| `generating/config.py` | **CREATE** |
| `generating/generate.py` | MODIFY |
| `generating/prompt_handler.py` | MODIFY |
| `generating/__init__.py` | MODIFY (export config) |
| `app/playground.py` | MODIFY |
| `examples/generation_playground.py` | MODIFY |

### 1.8 Tests

- Run `pipenv run pytest test/test_generate.py`
- Verify existing API still works
- Add test for new config-based API

---

## Phase 2: Token & Constant Consolidation

**Goal:** Centralize magic strings and values

### 2.1 Create `src/the_jam_machine/tokens.py`

```python
"""Token constants used throughout the MIDI text representation."""


class Tokens:
    """Standard token strings for MIDI text encoding/decoding.

    These tokens are used to structure the text representation of MIDI sequences
    and must match the tokenizer vocabulary.
    """
    # Structure tokens
    PIECE_START = "PIECE_START"
    TRACK_START = "TRACK_START"
    TRACK_END = "TRACK_END"
    BAR_START = "BAR_START"
    BAR_END = "BAR_END"

    # Note tokens (prefixes)
    NOTE_ON = "NOTE_ON"
    NOTE_OFF = "NOTE_OFF"
    TIME_DELTA = "TIME_DELTA"

    # Metadata prefixes
    INST = "INST"
    DENSITY = "DENSITY"

    # Special values
    DRUMS = "DRUMS"
```

### 2.2 Update `constants.py`

**Add:**
```python
# === Generation Defaults ===
DEFAULT_BARS_PER_SECTION = 8
DEFAULT_VELOCITY = 99
MAX_SEQUENCE_LENGTH = 2048
MAX_GENERATION_RETRIES = 2
DEFAULT_MAX_PROMPT_LENGTH = 1500

# === Visualization ===
INSTRUMENT_COLORS: dict[str, str] = {
    "Drums": "purple",
    "Synth Bass 1": "orange",
    "Synth Lead Square": "green",
    "Synth Lead Sawtooth": "green",
    "Electric Piano 1": "blue",
    "Vibraphone": "cyan",
    "Percussive Organ": "red",
    "Synth Strings 1": "pink",
    "Synth Strings 2": "pink",
    "Synth Brass 1": "gold",
    "Synth Brass 2": "gold",
    "Synth Lead Calliope": "lime",
}
DEFAULT_INSTRUMENT_COLOR = "green"
```

### 2.3 Replace Hardcoded Values

| Location | Current | Replace With |
|----------|---------|--------------|
| `decoder.py:315` | `99` | `DEFAULT_VELOCITY` |
| `encoder.py:223` | `n_bar=8` | `n_bar=DEFAULT_BARS_PER_SECTION` |
| `prompt_handler.py:25` | `1500` | `DEFAULT_MAX_PROMPT_LENGTH` |
| `generate.py:225` | `2` | `MAX_GENERATION_RETRIES` |
| `generation_engine.py:47` | `"TRACK_END"` | `Tokens.TRACK_END` |
| `utils.py:225-230` | hardcoded colors | `INSTRUMENT_COLORS.get(name, DEFAULT_INSTRUMENT_COLOR)` |

### 2.4 Replace Token Strings

**Example in `generate.py`:**

Before:
```python
input_prompt = f"{input_prompt}TRACK_START INST={instrument} "
```

After:
```python
from ..tokens import Tokens

input_prompt = f"{input_prompt}{Tokens.TRACK_START} {Tokens.INST}={instrument} "
```

**Files to update:**
- `generating/generate.py`
- `generating/generation_engine.py`
- `generating/track_builder.py`
- `generating/piece_builder.py`
- `embedding/encoder.py`
- `embedding/decoder.py`

### 2.5 Files Changed

| File | Action |
|------|--------|
| `tokens.py` | **CREATE** |
| `constants.py` | MODIFY |
| `generating/*.py` | MODIFY (use Tokens) |
| `embedding/*.py` | MODIFY (use Tokens, constants) |

---

## Phase 3: Split `generating/utils.py`

**Goal:** Separate concerns into focused modules

### 3.1 Current Contents Analysis

| Content | New Location |
|---------|--------------|
| `WriteTextMidiToFile` | `generating/file_io.py` |
| `define_generation_dir()` | `generating/file_io.py` |
| `bar_count_check()` | `generating/validation.py` |
| `forcing_bar_count()` | `generating/validation.py` |
| `check_if_prompt_inst_in_tokenizer_vocab()` | `generating/validation.py` |
| `check_if_prompt_density_in_tokenizer_vocab()` | `generating/validation.py` (or DELETE - stub) |
| `print_inst_classes()` | `generating/validation.py` |
| `get_max_time()` | `generating/visualization.py` |
| `plot_piano_roll()` | `generating/visualization.py` |
| matplotlib config | `generating/visualization.py` |

### 3.2 Create `generating/file_io.py`

```python
"""File I/O utilities for MIDI generation."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..utils import get_datetime, writeToFile

if TYPE_CHECKING:
    from .generate import GenerateMidiText

logger = logging.getLogger(__name__)


class WriteTextMidiToFile:
    """Utility for saving MIDI text from GenerateMidiText to file."""
    # ... (existing implementation)


def define_generation_dir(generation_dir: str) -> str:
    """Create generation directory if it doesn't exist."""
    # ... (existing implementation)
```

### 3.3 Create `generating/validation.py`

```python
"""Validation utilities for MIDI generation."""

import logging
from typing import Any

import numpy as np

from ..constants import INSTRUMENT_CLASSES

logger = logging.getLogger(__name__)


def bar_count_check(sequence: str, n_bars: int) -> tuple[bool, int]:
    """Check if the sequence contains the right number of bars."""
    # ... (existing implementation)


def forcing_bar_count(
    input_prompt: str,
    generated: str,
    bar_count: int,
    expected_length: int,
) -> tuple[str, bool]:
    """Force the generated sequence to have the expected length."""
    # ... (existing implementation)


def check_if_prompt_inst_in_tokenizer_vocab(
    tokenizer: Any,
    inst_prompt_list: list[str],
) -> None:
    """Check if the prompt instruments are in the tokenizer vocab."""
    # ... (existing implementation)
```

### 3.4 Create `generating/visualization.py`

```python
"""Visualization utilities for MIDI generation."""

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from ..constants import INSTRUMENT_COLORS, DEFAULT_INSTRUMENT_COLOR

if TYPE_CHECKING:
    import pretty_midi

# matplotlib settings
matplotlib.use("Agg")
matplotlib.rcParams["xtick.major.size"] = 0
matplotlib.rcParams["ytick.major.size"] = 0
matplotlib.rcParams["axes.facecolor"] = "none"
matplotlib.rcParams["axes.edgecolor"] = "grey"


def get_max_time(inst_midi: "pretty_midi.PrettyMIDI") -> float:
    """Get the maximum end time across all instruments."""
    # ... (existing implementation)


def plot_piano_roll(inst_midi: "pretty_midi.PrettyMIDI") -> plt.Figure:
    """Generate a piano roll visualization of the MIDI."""
    # ... (existing implementation, use INSTRUMENT_COLORS)
```

### 3.5 Update `generating/utils.py`

Convert to re-export hub for backwards compatibility:

```python
"""MIDI generation utilities.

This module re-exports utilities from their new locations for backwards compatibility.
"""

# Re-exports for backwards compatibility
from .file_io import WriteTextMidiToFile, define_generation_dir
from .validation import (
    bar_count_check,
    check_if_prompt_inst_in_tokenizer_vocab,
    forcing_bar_count,
)
from .visualization import get_max_time, plot_piano_roll

__all__ = [
    "WriteTextMidiToFile",
    "define_generation_dir",
    "bar_count_check",
    "check_if_prompt_inst_in_tokenizer_vocab",
    "forcing_bar_count",
    "get_max_time",
    "plot_piano_roll",
]
```

### 3.6 Update Imports in Dependent Files

**`generate.py`:**
```python
from .validation import bar_count_check, forcing_bar_count
```

**`app/playground.py`:**
```python
from the_jam_machine.generating.visualization import plot_piano_roll
```

### 3.7 Files Changed

| File | Action |
|------|--------|
| `generating/file_io.py` | **CREATE** |
| `generating/validation.py` | **CREATE** |
| `generating/visualization.py` | **CREATE** |
| `generating/utils.py` | MODIFY (re-exports only) |
| `generating/generate.py` | MODIFY imports |
| `app/playground.py` | MODIFY imports |

---

## Phase 4: Split `embedding/encoder.py`

**Goal:** Break 406-line file into focused modules

### 4.1 Responsibility Breakdown

| Responsibility | New Location | Classes/Functions |
|----------------|--------------|-------------------|
| Time-shift normalization | `time_processor.py` | `TimeShiftProcessor` |
| Bar markers & density | `bar_processor.py` | `BarProcessor` |
| Section building | `section_builder.py` | `SectionBuilder` |
| Orchestration | `encoder.py` | `MIDIEncoder` (slimmed) |

### 4.2 Create `embedding/time_processing.py`

```python
"""Time-shift processing for MIDI encoding."""

from __future__ import annotations

from miditok import Event


def remove_velocity(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Remove velocity events from MIDI events."""
    return [
        [event for event in inst_events if event.type != "Velocity"]
        for inst_events in midi_events
    ]


def normalize_timeshifts(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Convert time-shifts to minimum length units."""
    # ... (existing implementation from MIDIEncoder.set_timeshifts_to_min_length)


def combine_timeshifts_in_bar(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Combine adjacent time-shifts within the same bar."""
    # ... (existing implementation)


def remove_timeshifts_before_bar_end(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Remove useless time-shifts before bar end events."""
    # ... (existing implementation, fix typo: preceeding -> preceding)
```

### 4.3 Create `embedding/bar_processing.py`

```python
"""Bar processing for MIDI encoding."""

from __future__ import annotations

from miditok import Event

from ..constants import BEATS_PER_BAR


def add_bar_markers(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Add bar-start and bar-end events to MIDI events."""
    # ... (existing implementation)


def calculate_bar_density(midi_events: list[list[Event]]) -> list[list[Event]]:
    """Calculate and add note density to each bar."""
    # ... (existing implementation)


def calculate_section_density(midi_sections: list) -> list:
    """Add section-level density as mode of bar densities."""
    # ... (existing implementation)
```

### 4.4 Create `embedding/section_building.py`

```python
"""Section building for MIDI encoding."""

from __future__ import annotations

from miditok import Event

from ..constants import DEFAULT_BARS_PER_SECTION
from .familizer import Familizer


def make_sections(
    midi_events: list[list[Event]],
    instruments: list,
    n_bar: int = DEFAULT_BARS_PER_SECTION,
    familized: bool = False,
) -> list:
    """Create n-bar sections for each instrument."""
    # ... (existing implementation)


def define_instrument(midi_tok_instrument, familize: bool = False) -> str | int:
    """Define the instrument token from midi token instrument."""
    # ... (existing implementation)


def init_track_section(instrument: str | int, track_index: int) -> list[Event]:
    """Create the initial events for a track section."""
    # ... (existing implementation)


def terminate_track_section(section: list[Event], track_index: int) -> tuple[list, int]:
    """Add track end event and increment index."""
    # ... (existing implementation)


def sections_to_piece(midi_events: list) -> list[Event]:
    """Combine all sections into one piece."""
    # ... (existing implementation)
```

### 4.5 Slim Down `encoder.py`

```python
"""MIDI to text encoder."""

from __future__ import annotations

import logging
from miditoolkit import MidiFile

from ..constants import DEFAULT_BARS_PER_SECTION
from ..utils import get_miditok
from . import bar_processing, section_building, time_processing

logger = logging.getLogger(__name__)


def encode_midi(midi, tokenizer, familized: bool = False) -> str:
    """Convert MIDI to text representation.

    Orchestrates the encoding pipeline:
    1. Extract events from MIDI
    2. Normalize time-shifts
    3. Add bar markers and density
    4. Build sections
    5. Convert to text

    Args:
        midi: MidiTok MIDI object.
        tokenizer: MidiTok tokenizer instance.
        familized: Whether to use instrument families.

    Returns:
        Text representation of the MIDI.
    """
    midi_events = _extract_events(midi, tokenizer)

    # Time processing
    midi_events = time_processing.remove_velocity(midi_events)
    midi_events = time_processing.normalize_timeshifts(midi_events)

    # Bar processing
    midi_events = bar_processing.add_bar_markers(midi_events)
    midi_events = time_processing.combine_timeshifts_in_bar(midi_events)
    midi_events = time_processing.remove_timeshifts_before_bar_end(midi_events)
    midi_events = bar_processing.calculate_bar_density(midi_events)

    # Section building
    sections = section_building.make_sections(
        midi_events, midi.instruments, familized=familized
    )
    sections = bar_processing.calculate_section_density(sections)

    # Convert to text
    piece = section_building.sections_to_piece(sections)
    return events_to_text(piece)


def _extract_events(midi, tokenizer) -> list:
    """Extract events from MIDI using tokenizer."""
    return [
        tokenizer.tokens_to_events(inst_tokens)
        for inst_tokens in tokenizer.midi_to_tokens(midi)
    ]


def events_to_text(events) -> str:
    """Convert events to text string."""
    # ... (existing implementation)


def midi_to_sectioned_text(midi_filename: str, familized: bool = False) -> str:
    """Convert a MIDI file to text representation.

    Args:
        midi_filename: Path to MIDI file (without extension).
        familized: Whether to use instrument families.

    Returns:
        Text representation of the MIDI.
    """
    midi = MidiFile(f"{midi_filename}.mid")
    tokenizer = get_miditok()
    return encode_midi(midi, tokenizer, familized=familized)
```

### 4.6 Files Changed

| File | Action |
|------|--------|
| `embedding/time_processor.py` | **CREATE** |
| `embedding/bar_processor.py` | **CREATE** |
| `embedding/section_builder.py` | **CREATE** |
| `embedding/encoder.py` | MODIFY (slim down, orchestration only) |
| `embedding/__init__.py` | MODIFY (update exports) |

---

## Phase 5: Split `embedding/decoder.py`

**Goal:** Break 333-line file into focused modules

### 5.1 Responsibility Breakdown

| Responsibility | New Location | Classes/Functions |
|----------------|--------------|-------------------|
| Text parsing | `text_parser.py` | `TextParser` |
| Event processing | `event_processor.py` | `EventProcessor` |
| Orchestration | `decoder.py` | `TextDecoder` (slimmed) |

### 5.2 Create `embedding/text_parsing.py`

```python
"""Text parsing for MIDI decoding."""

from __future__ import annotations

from miditok import Event

from ..constants import DRUMS_BEAT_QUANTIZATION, NONE_DRUMS_BEAT_QUANTIZATION
from ..utils import get_event


def parse_text_to_events(text: str, verbose: bool = False) -> list[Event]:
    """Parse text into a list of events."""
    # ... (existing implementation from TextDecoder.text_to_events)


def add_track_ids(events: list[Event]) -> list[Event]:
    """Add track IDs to track start/end events."""
    # ... (existing implementation)


def split_by_instrument(piece_events: list[Event]) -> list[dict]:
    """Convert piece events to per-instrument event lists."""
    # ... (existing implementation)


def add_bar_ids(inst_events: list[dict]) -> list[dict]:
    """Add bar indices to bar start/end events."""
    # ... (existing implementation)
```

### 5.3 Create `embedding/event_processing.py`

```python
"""Event processing for MIDI decoding."""

from __future__ import annotations

from miditok import Event

from ..constants import BEATS_PER_BAR, DEFAULT_VELOCITY
from ..utils import beat_to_int_dec_base, int_dec_base_to_beat


def add_missing_timeshifts(
    inst_events: list[dict],
    beat_per_bar: int = BEATS_PER_BAR,
    verbose: bool = False,
) -> list[dict]:
    """Add missing time-shifts to ensure each bar has correct beats."""
    # ... (existing implementation)


def remove_structural_tokens(events: list[dict]) -> list[dict]:
    """Remove structural tokens not needed for MIDI output."""
    # ... (existing implementation)


def aggregate_timeshifts(events: list[dict]) -> list[dict]:
    """Aggregate consecutive time-shift events."""
    # ... (existing implementation)


def add_velocity(events: list[dict], velocity: int = DEFAULT_VELOCITY) -> list[dict]:
    """Add velocity events after note-on events."""
    # ... (existing implementation, parameterized velocity)


def check_for_duplicated_events(event_list: list[Event]) -> None:
    """Log any duplicated consecutive events."""
    # ... (existing implementation)
```

### 5.4 Slim Down `decoder.py`

```python
"""Text to MIDI decoder."""

from __future__ import annotations

import logging
from typing import Any

from ..constants import DEFAULT_VELOCITY
from ..utils import get_miditok
from . import event_processing, text_parsing
from .familizer import Familizer

logger = logging.getLogger(__name__)


def decode_text(text: str) -> list[dict]:
    """Decode text to instrument events.

    Pipeline:
    1. Parse text to events
    2. Organize by instrument
    3. Process time-shifts and velocity

    Args:
        text: MIDI text representation.

    Returns:
        List of instrument event dictionaries.
    """
    # Parse
    events = text_parsing.parse_text_to_events(text)
    events = text_parsing.add_track_ids(events)
    event_processing.check_for_duplicated_events(events)

    # Organize by instrument
    inst_events = text_parsing.split_by_instrument(events)
    inst_events = text_parsing.add_bar_ids(inst_events)

    # Process
    inst_events = event_processing.add_missing_timeshifts(inst_events)
    inst_events = event_processing.remove_structural_tokens(inst_events)
    inst_events = event_processing.aggregate_timeshifts(inst_events)
    inst_events = event_processing.add_velocity(inst_events)

    return inst_events


def text_to_midi(text: str, tokenizer: Any, filename: str | None = None):
    """Convert text to MIDI file.

    Args:
        text: MIDI text representation.
        tokenizer: MidiTok tokenizer instance.
        filename: Optional path to save MIDI file.

    Returns:
        MidiToolkit MIDI object.
    """
    events = decode_text(text)
    tokens = [tokenizer.events_to_tokens(inst["events"]) for inst in events]
    instruments = _get_instruments_tuple(events)
    midi = tokenizer.tokens_to_midi(tokens, instruments)

    if filename is not None:
        midi.dump(filename)
        logger.info("MIDI file written: %s", filename)

    return midi


def _get_instruments_tuple(events: list[dict]) -> tuple:
    """Get instruments tuple for MIDI generation."""
    # ... (existing implementation)
```

### 5.5 Files Changed

| File | Action |
|------|--------|
| `embedding/text_parser.py` | **CREATE** |
| `embedding/event_processor.py` | **CREATE** |
| `embedding/decoder.py` | MODIFY (slim down) |
| `embedding/__init__.py` | MODIFY (update exports) |

---

## Phase 6: Naming Fixes & Cleanup

**Goal:** Fix typos, remove dead code, standardize naming

### 6.0 Add Postponed Annotations

Add to **all** Python files in `src/` and `app/`:

```python
from __future__ import annotations
```

Then remove all quoted type hints (e.g., `"GPT2LMHeadModel"` → `GPT2LMHeadModel`).

**Files to update:**
- All files in `src/the_jam_machine/`
- `app/playground.py`

### 6.1 Typo Fixes

| Location | Current | Fixed |
|----------|---------|-------|
| `encoder.py` | `from_MIDI_to_sectionned_text` | `midi_to_sectioned_text` |
| `encoder.py` | `remove_timeshifts_preceeding_bar_end` | `remove_timeshifts_preceding_bar_end` |
| `decoder.py` | `dictionnary` (comment) | `dictionary` |
| `encoder.py` | `beggining` (comment) | `beginning` |

### 6.2 Remove Dead Code

| Location | What | Action |
|----------|------|--------|
| `decoder.py:230-235` | `check_bar_count_in_section()` | DELETE (stub with only `pass`) |
| `generating/utils.py:140-151` | `check_if_prompt_density_in_tokenizer_vocab()` | DELETE or implement |
| `src/the_jam_machine/unused/` | Entire directory | DELETE |

### 6.3 Remove Legacy Aliases

After all callers are updated, remove from `generate.py`:
- `get_whole_piece_from_bar_dict()` (use `get_piece_text()`)
- `get_whole_track_from_bar_dict()` (use `get_track_text()`)
- `delete_one_track()` (use `delete_track()`)

### 6.4 Files Changed

| File | Action |
|------|--------|
| `**/*.py` | MODIFY (add `from __future__ import annotations`, remove quoted hints) |
| `embedding/encoder.py` | MODIFY (fix typos, rename function) |
| `embedding/decoder.py` | MODIFY (fix typos, remove stub) |
| `generating/utils.py` | MODIFY (remove/implement stub) |
| `unused/` | **DELETE** directory |
| `generate.py` | MODIFY (remove legacy aliases) |

---

## Implementation Order

```
Phase 1 (Config Dataclasses)
    │
    ▼
Phase 2 (Token & Constant Consolidation)
    │
    ▼
Phase 3 (Split generating/utils.py)
    │
    ▼
Phase 4 (Split embedding/encoder.py)
    │
    ▼
Phase 5 (Split embedding/decoder.py)
    │
    ▼
Phase 6 (Naming Fixes & Cleanup)
```

Each phase should be:
1. Implemented in a separate commit
2. Tested with `pipenv run pytest test/`
3. Linted with `pipenv run ruff check src/ app/`
4. Formatted with `pipenv run ruff format src/ app/`

---

## Summary of New Files

| Phase | New Files |
|-------|-----------|
| 1 | `generating/config.py` |
| 2 | `tokens.py` |
| 3 | `generating/file_io.py`, `generating/validation.py`, `generating/visualization.py` |
| 4 | `embedding/time_processor.py`, `embedding/bar_processor.py`, `embedding/section_builder.py` |
| 5 | `embedding/text_parser.py`, `embedding/event_processor.py` |
| 6 | (no new files) |

**Total new files:** 10

---

## Test Plan

After each phase:

```bash
# Run tests
pipenv run pytest test/ -v

# Lint
pipenv run ruff check src/ app/ test/

# Format
pipenv run ruff format src/ app/ test/

# Verify app works
pipenv run python app/playground.py
```

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| 1 | Breaking existing API | Keep legacy method signatures |
| 2 | Missing token replacements | Search codebase thoroughly |
| 3-5 | Circular imports | Careful import organization |
| 6 | Breaking external callers | Deprecation warnings first |

---

## Notes

- Each phase can be a separate PR if needed
- Backwards compatibility maintained via re-exports
- Type hints added to all new code
- Docstrings follow Google style
- All new files under 200 lines target
