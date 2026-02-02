# Design Audit - The Jam Machine

**Date:** 2026-02-02
**Scope:** `src/the_jam_machine/` - focusing on splitting functions, files, renaming, and config patterns

---

## Design Principles

### Prefer Functions Over Classes

When splitting modules, use **module-level functions** instead of classes with only static methods:

```python
# ❌ Over-engineered
class TimeShiftProcessor:
    @staticmethod
    def normalize(events): ...
    @staticmethod
    def combine(events): ...

# ✅ Pythonic - just use module functions
# time_processor.py
def normalize(events): ...
def combine(events): ...
```

**Use classes only when:**
- You have instance state (attributes that vary per instance)
- Objects have a lifecycle (init, use, cleanup)
- You need multiple instances with different configurations

**Use functions when:**
- Operations are stateless transformations
- You'd end up with all `@staticmethod` or `@classmethod`

---

## Table of Contents

1. [Config Dataclasses (PR #2 Feedback)](#1-config-dataclasses-pr-2-feedback)
2. [Module-Level Issues](#2-module-level-issues)
3. [Naming Inconsistencies](#3-naming-inconsistencies)
4. [Files to Split](#4-files-to-split)
5. [Constants & Magic Values](#5-constants--magic-values)
6. [Recommended Actions](#6-recommended-actions)

---

## 1. Config Dataclasses (PR #2 Feedback)

### Problem

Multiple methods share repeated argument patterns that should be grouped into dataclasses:

**`generate.py` - Track Generation:**
```python
# Current: scattered args
def generate_one_new_track(self, instrument, density, temperature, input_prompt="PIECE_START ")
def _generate_until_track_end(self, input_prompt, instrument, density, temperature, verbose, expected_length)
```

**`generate.py` - Generation Config:**
```python
# Scattered across multiple setters
self.force_sequence_length = True
self.prompts.n_bars = 8
self.engine.no_repeat_ngram_size = 0  # improvisation
```

### Proposed Dataclasses

#### A. `TrackConfig` - Track generation parameters
```python
@dataclass
class TrackConfig:
    """Configuration for generating a single track."""
    instrument: str
    density: int
    temperature: float
```

#### B. `GenerationConfig` - Generator-level settings
```python
@dataclass
class GenerationConfig:
    """Configuration for the generation engine."""
    n_bars: int = 8
    force_sequence_length: bool = True
    improvisation_level: int = 0
    max_prompt_length: int = 1500
    generate_until_token: str = "TRACK_END"
    max_retries: int = 2
```

#### C. `PromptConfig` - Prompt building parameters
```python
@dataclass
class PromptConfig:
    """Configuration for prompt construction."""
    input_prompt: str = "PIECE_START "
    expected_length: int | None = None
    verbose: bool = True
```

### Refactored API Example

```python
# Before
generator.generate_one_new_track("Drums", 2, 0.7, "PIECE_START ")

# After
track = TrackConfig(instrument="Drums", density=2, temperature=0.7)
generator.generate_one_new_track(track)
```

### Files Affected
- `src/the_jam_machine/generating/generate.py`
- `src/the_jam_machine/generating/generation_engine.py`
- `src/the_jam_machine/generating/prompt_handler.py`
- `app/playground.py` (caller)

---

## 2. Module-Level Issues

### 2.1 `embedding/encoder.py` (406 lines) - TOO LARGE

**Current responsibilities (violates SRP):**
- Remove velocity events
- Normalize time-shifts
- Add bar markers
- Combine time-shifts
- Calculate note density
- Create 8-bar sections
- Build text representation

**Recommended split:**
| New File | Responsibility |
|----------|----------------|
| `time_processor.py` | Time-shift normalization, combination |
| `bar_processor.py` | Bar markers, density calculation |
| `section_builder.py` | 8-bar section creation |
| `encoder.py` | Orchestration only |

### 2.2 `embedding/decoder.py` (333 lines) - TOO LARGE

**Current responsibilities:**
- Parse text to events
- Track ID management
- Add missing time-shifts
- Aggregate time-shifts
- Add velocity
- Resolve instruments

**Recommended split:**
| New File | Responsibility |
|----------|----------------|
| `text_parser.py` | Parse text to event structures |
| `event_processor.py` | Time-shift aggregation, velocity |
| `decoder.py` | Orchestration only |

### 2.3 `preprocessing/midi_stats.py` (500+ lines) - STRUCTURAL ISSUE

**Problem:** 50+ standalone functions with repeated patterns:
```python
def some_stat(pm):
    if pm.instruments:
        return compute()
    return None
```

**Recommended approach:**
- Use decorator or helper for null-safety pattern
- Group into analyzer classes by domain (NoteAnalyzer, TempoAnalyzer, etc.)
- Or use a single dataclass for all stats

### 2.4 `generating/utils.py` - MIXED CONCERNS

**Current contents:**
- `WriteTextMidiToFile` class (file I/O)
- `bar_count_check()` (validation)
- `check_if_instrument_in_tokenizer_vocab()` (validation)
- `get_miditok_inst_by_family()` (MIDI utilities)
- `piano_roll_to_pretty_midi()` (visualization)
- Matplotlib configuration

**Recommended split:**
| New File | Contents |
|----------|----------|
| `file_io.py` | `WriteTextMidiToFile`, file operations |
| `validation.py` | `bar_count_check`, vocab checks |
| `midi_utils.py` | `get_miditok_inst_by_family`, conversions |
| `visualization.py` | Piano roll, matplotlib config |

---

## 3. Naming Inconsistencies

### 3.1 Method Names

| Current | Issue | Suggested |
|---------|-------|-----------|
| `striping_track_ends()` | Typo | `strip_track_ends()` |
| `from_MIDI_to_sectionned_text()` | Typo + inconsistent case | `midi_to_sectioned_text()` |
| `initiate_track_dict()` | Verbose | `init_track()` |
| `update_track_dict__add_bars()` | Double underscore | `add_bars_to_track()` |
| `get_whole_piece_from_bar_dict()` | Verbose | `build_piece_text()` (done in refactor) |

### 3.2 Variable Names

| Current | Issue | Suggested |
|---------|-------|-----------|
| `pm` | Cryptic abbreviation | `midi` or `pretty_midi` |
| `inst_events` / `events` / `piece_events` | Inconsistent | Standardize on one pattern |
| `midi_sections` | Unclear structure | Document or rename to `nested_midi_sections` |

### 3.3 Function vs Method Consistency

The codebase mixes:
- `get_text()` (module-level)
- `events_to_text()` (class method)
- Both do similar things

**Recommendation:** Consolidate into one location with clear naming.

---

## 4. Files to Split

### Priority Order

| Priority | File | Lines | Action |
|----------|------|-------|--------|
| HIGH | `encoder.py` | 406 | Split into 4 files |
| HIGH | `decoder.py` | 333 | Split into 3 files |
| MEDIUM | `generating/utils.py` | 250 | Split into 4 files |
| MEDIUM | `midi_stats.py` | 500+ | Restructure functions |
| LOW | `trainer.py` | 150 | Extract config to dataclass |

---

## 5. Constants & Magic Values

### Currently Scattered Hardcoded Values

| Value | Location | Meaning | Action |
|-------|----------|---------|--------|
| `8` | encoder.py:223, prompt_handler.py:27 | Bars per section | → `DEFAULT_BARS_PER_SECTION` |
| `99` | decoder.py:315 | Default velocity | → `DEFAULT_VELOCITY` |
| `1500` | prompt_handler.py:25 | Max prompt tokens | Already constant ✓ |
| `2048` | trainer_utils.py:21 | Max sequence length | → `MAX_SEQUENCE_LENGTH` |
| `2` | generate.py:225 | Retry threshold | → `MAX_GENERATION_RETRIES` |
| `"TRACK_END"` | generation_engine.py:47 | Stop token | → `Tokens.TRACK_END` |
| Colors dict | utils.py:224-230 | Instrument colors | → `INSTRUMENT_COLORS` |

### Proposed Token Constants

```python
# src/the_jam_machine/tokens.py
class Tokens:
    """Standard token strings used throughout the codebase."""
    PIECE_START = "PIECE_START"
    TRACK_START = "TRACK_START"
    TRACK_END = "TRACK_END"
    BAR_START = "BAR_START"
    BAR_END = "BAR_END"
    NOTE_ON = "NOTE_ON"
    NOTE_OFF = "NOTE_OFF"
```

### Updated `constants.py`

```python
# Add to existing constants.py
DEFAULT_BARS_PER_SECTION = 8
DEFAULT_VELOCITY = 99
MAX_SEQUENCE_LENGTH = 2048
MAX_GENERATION_RETRIES = 2

INSTRUMENT_COLORS = {
    "Drums": "purple",
    "Synth Bass 1": "orange",
    "Synth Lead Square": "green",
    # ... etc
}
```

---

## 6. Recommended Actions

### Phase 1: Config Dataclasses (Immediate - PR #2 scope)

1. **Create `src/the_jam_machine/generating/config.py`**
   - `TrackConfig` dataclass
   - `GenerationConfig` dataclass
   - `PromptConfig` dataclass (optional)

2. **Update `generate.py`**
   - Accept `TrackConfig` in generation methods
   - Accept `GenerationConfig` in constructor or via setter

3. **Update `playground.py`**
   - Use new config classes when calling generator

### Phase 2: Constants Consolidation (Short-term)

1. Add missing constants to `constants.py`
2. Create `tokens.py` for token strings
3. Replace hardcoded values throughout codebase

### Phase 3: File Splitting (Medium-term)

1. Split `encoder.py` into focused modules
2. Split `decoder.py` into focused modules
3. Split `generating/utils.py` by concern

### Phase 4: Naming & Cleanup (Ongoing)

1. Fix typos (`striping` → `strip`, `sectionned` → `sectioned`)
2. Standardize variable naming conventions
3. Remove unused code in `unused/` directory
4. Remove stub methods (`pass` only)

---

## Appendix: Files Overview

```
src/the_jam_machine/
├── constants.py          # ✓ Good - expand with more constants
├── utils.py              # Mixed concerns - consider splitting
├── logging_config.py     # ✓ Good - clean and focused
│
├── embedding/
│   ├── encoder.py        # ✗ 406 lines - needs splitting
│   ├── decoder.py        # ✗ 333 lines - needs splitting
│   ├── familizer.py      # ✓ Good - focused
│   ├── preprocess.py     # ~ OK - thin wrapper
│   └── load.py           # ~ OK - needs type hints
│
├── generating/
│   ├── generate.py       # ✓ Recently refactored - add config dataclasses
│   ├── generation_engine.py  # ✓ Good - focused
│   ├── piece_builder.py  # ✓ Good - focused
│   ├── track_builder.py  # ✓ Good - focused
│   ├── prompt_handler.py # ✓ Good - focused
│   ├── utils.py          # ✗ Mixed concerns - needs splitting
│   └── playback.py       # ~ OK - needs type hints
│
├── preprocessing/
│   ├── midi_stats.py     # ✗ Structural issues - needs restructure
│   ├── mmd_metadata.py   # ~ OK - needs type hints
│   ├── picker.py         # ✓ Good - simple
│   └── load.py           # ~ OK - needs type hints
│
├── training/
│   ├── trainer.py        # ✗ Hardcoded config - extract to dataclass
│   └── trainer_utils.py  # ~ OK - needs type hints
│
├── stats/
│   └── track_stats_for_encoding.py  # ✗ Script mixed with analysis
│
└── unused/               # ✗ Delete entire directory
    ├── encoder_oct.py
    └── encoder_mumidi.py
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-02 | Create config dataclasses | PR #2 feedback - repeated arg patterns |
| 2026-02-02 | Split encoder/decoder | >300 lines, multiple responsibilities |
| 2026-02-02 | Create tokens.py | DRY - token strings repeated everywhere |
