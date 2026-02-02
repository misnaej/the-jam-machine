# Main Package Audit Report

**Audited:** `src/the_jam_machine/`, `app/`, `examples/`
**Date:** 2026-02-02
**Status:** Complete

---

## Executive Summary

The Jam Machine has a generally logical structure, but several areas suffer from Single Responsibility Principle (SRP) violations, poor module organization, and code duplication. The codebase ranges from well-designed modules (embedding, generating) to poorly organized ones (utils, preprocessing).

---

## 1. Module Analysis

### 1.1 `src/the_jam_machine/utils.py` - CRITICAL ISSUES

**Lines:** ~300
**Responsibilities (TOO MANY - 7+):**
- MIDI event conversion (int_dec_base_to_beat, time_delta conversion)
- Text generation from events (get_text, get_event)
- File operations (writeToFile, readFromFile, get_files, FileCompressor)
- Audio processing (write_mp3)
- Generic utilities (timeit, chain, split_dots, compute_list_average)
- MidiTok initialization (get_miditok singleton)

**Issues:**
1. **SRP Violation**: 7+ distinct responsibilities in one file
2. **Implicit Dependencies**: `get_miditok()` called throughout codebase but not clearly documented as global singleton
3. **Poor Naming**: `get_text()` does encoding (misleading)
4. **Exception Handling**: `chain()` catches TypeError to handle variable argument counts (fragile)
5. **Type Hints Missing**: Many functions lack type hints

**Suggested Refactoring:**
```
utils/
├── encoding.py         # int_dec_base_to_beat, time_delta conversions
├── decoding.py         # get_event, reverse conversions
├── file_io.py          # writeToFile, readFromFile, FileCompressor
├── audio.py            # write_mp3
├── midi_tokenizer.py   # get_miditok (proper singleton)
└── generic.py          # timeit, chain, etc.
```

---

### 1.2 `src/the_jam_machine/constants.py` - GOOD

**Purpose:** Configuration constants for instruments and beat quantization

**Strengths:**
- Single clear responsibility
- Well-organized with comments
- Type-safe mapping structures

**Minor Issues:**
- `INSTRUMENT_TRANSFER_CLASSES` has inconsistent structure (some use `range()`, others use list)
- Comments at top are bare strings (should be docstring)

---

### 1.3 `src/the_jam_machine/embedding/encoder.py` - GOOD DESIGN, LARGE CLASS

**Lines:** 400+
**Purpose:** Convert MIDI files to text token sequences

**Key Class:** `MIDIEncoder`

**Strengths:**
- Clear pipeline structure
- Well-named static methods
- Each method has focused responsibility

**Issues:**
1. **Large Class**: 400 lines with 15+ methods; should be split by concern
2. **SRP Violation**: Handles too many stages:
   - Event manipulation (remove_velocity, set_timeshifts_to_min_length)
   - Bar logic (add_bars, combine_timeshifts_in_bar)
   - Density calculation (add_density_to_bar, add_density_to_sections)
   - Section creation (make_sections)
   - Text conversion (events_to_text)

**Suggested Refactoring:**
```
embedding/
├── event_cleaner.py       # remove_velocity, remove_timeshifts_preceeding_bar_end
├── timeshift_processor.py # set_timeshifts_to_min_length, combine_timeshifts_in_bar
├── bar_processor.py       # add_bars, add_density_to_bar, add_density_to_sections
├── section_creator.py     # make_sections, sections_to_piece
├── text_converter.py      # events_to_text, get_text conversions
└── encoder.py             # Main orchestrator class
```

---

### 1.4 `src/the_jam_machine/embedding/decoder.py` - GOOD DESIGN, DENSE

**Lines:** 340
**Purpose:** Convert text token sequences back to MIDI files

**Key Class:** `TextDecoder`

**Strengths:**
- Clear pipeline structure mirroring encoder
- Well-organized public API

**Issues:**
1. **Large Class**: 340 lines, should be split
2. **Dead Code**: `check_bar_count_in_section()` is empty (lines 231-235)
3. **Bare Exception**: Line 386 catches all exceptions silently

**Suggested Refactoring:**
```
embedding/
├── text_parser.py          # text_to_events parsing logic
├── event_processor.py      # track_ids, bar_ids, unwanted_tokens removal
├── timeshift_aggregator.py # add_missing_timeshifts, aggregate_timeshifts
├── instrument_handler.py   # add_velocity, get_instruments_tuple
└── decoder.py              # Main orchestrator class
```

---

### 1.5 `src/the_jam_machine/embedding/familizer.py` - GOOD

**Purpose:** Convert between instrument families and program numbers

**Strengths:**
- Single, focused responsibility
- Clear API
- Good separation of concerns

**Minor Issue:** `replace_instruments()` and `replace_tokens()` don't belong in a mapping class

---

### 1.6 `src/the_jam_machine/generating/generate.py` - LARGEST, MOST COMPLEX - CRITICAL

**Lines:** 440+
**Methods:** 30+
**Purpose:** Music generation using GPT-2 model

**Key Class:** `GenerateMidiText`

**Critical Issues:**

1. **MASSIVE SRP VIOLATION** (should be 3-4 classes):
   - **Generation Engine** (tokenize_input_prompt, generate_sequence_of_token_ids, convert_ids_to_text)
   - **State Management** (piece_by_track dict operations)
   - **Text Manipulation** (piece/track extraction, stripping)
   - **Bar-level Generation** (generate_one_more_bar, process_prompt_for_next_bar)

2. **Bugs:**
   - Line 43: `self.device = ("cpu",)` creates tuple instead of string
   - Line 209: `ValueError()` created but not raised
   - Line 405: `only_this_track` parameter never used

3. **Poor Naming:**
   - `striping_track_ends()` should be `strip_track_ends()` (spelling error)
   - `piece_by_track` is dict but name suggests list

4. **Magic Numbers:**
   - 1500 token limit hardcoded in `force_prompt_length()`
   - -1 default for track_index used as convention

**Suggested Refactoring:**
```
generating/
├── generation_engine.py    # Low-level model interaction
│   └── class GenerationEngine: tokenize, generate_tokens, convert_to_text
├── piece_builder.py        # High-level piece assembly
│   └── class PieceBuilder: piece_by_track management
├── track_builder.py        # Track-level operations
│   └── class TrackBuilder: bars, track_to_text, extraction
├── prompt_handler.py       # Prompt manipulation
│   └── class PromptHandler: prompt length, track extraction
└── generate.py             # Public orchestrator class
```

---

### 1.7 `src/the_jam_machine/generating/playback.py` - SIMPLE, GOOD

**Purpose:** MIDI playback and visualization

**Strengths:**
- Focused, minimal responsibility
- Simple API
- Good example of minimal, focused module

---

### 1.8 `src/the_jam_machine/generating/utils.py` - SCATTERED RESPONSIBILITIES

**Purpose:** Generation utilities

**Issues:**
1. **SRP Violation**: Multiple distinct concerns:
   - JSON wrapping and file I/O (`WriteTextMidiToFile`)
   - Bar count validation (`bar_count_check`)
   - Token validation (`check_if_prompt_inst_in_tokenizer_vocab`)
   - Piano roll visualization (`plot_piano_roll`)

**Suggested Refactoring:**
```
generating/
├── output_writer.py    # WriteTextMidiToFile
├── validation.py       # bar_count_check, check_if_prompt_inst_in_tokenizer_vocab
└── visualization.py    # plot_piano_roll
```

---

### 1.9 `src/the_jam_machine/preprocessing/load.py` - GOOD

**Purpose:** Load pretrained GPT-2 model and tokenizer from HuggingFace

**Strengths:**
- Single responsibility
- Clear API
- Proper device handling

---

### 1.10 `src/the_jam_machine/preprocessing/midi_stats.py` - GOOD DESIGN, LARGE

**Lines:** 365
**Purpose:** Compute statistics on MIDI files

**Issues:**
1. 50+ standalone functions before `MidiStats` class
2. Loop patterns repeated across functions (should be decorator)
3. Class should wrap the functions; currently free-floating

---

### 1.11 `src/the_jam_machine/training/trainer.py` - SCRIPT-STYLE

**Purpose:** Train GPT-2 model

**Issues:**
1. **Not a Class**: Entire pipeline is procedural script
2. **Hardcoded Configuration**: All parameters hardcoded at top
3. **No Error Handling**: No validation of dataset, model, paths

---

## 2. App Layer Analysis

### 2.1 `app/playground.py` - WEB UI

**Purpose:** Gradio web interface for music generation

**Issues:**
1. Model repo hardcoded
2. Generator function 70 lines with complex branching
3. State management via 8-value tuple returns (fragile)
4. TODOs left in production code

**Suggestion:** Separate generation logic from UI layer.

---

### 2.2 `examples/generation_playground.py` - GOOD

**Purpose:** Example script for batch generation

**Issues:**
- Partially commented code for multiple model variants
- Should be config-driven

---

## 3. Cross-Cutting Issues

| Issue | Locations |
|-------|-----------|
| Silent Failures | decoder.py:386 catches all exceptions |
| Half-Implemented Errors | generate.py:209 creates ValueError but doesn't raise |
| No Logging | Should use Python logging instead of print() |
| Missing Type Hints | ~95% of code |
| Missing Docstrings | ~60% of methods |
| Code Duplication | Time delta conversion in encoder.py and utils.py |

---

## 4. Dependency Map

```
app/playground.py
├── LoadModel
├── GenerateMidiText
├── TextDecoder
├── get_music
├── plot_piano_roll
└── INSTRUMENT_TRANSFER_CLASSES

examples/generation_playground.py
├── LoadModel
├── GenerateMidiText
├── TextDecoder
├── WriteTextMidiToFile
└── check_if_prompt_inst_in_tokenizer_vocab

embedding/encoder.py
├── MIDIEncoder
├── Familizer
└── get_miditok() [from utils]

embedding/decoder.py
├── TextDecoder
├── Familizer
└── get_miditok() [from utils]

generating/generate.py
├── GenerateMidiText
├── bar_count_check [from utils]
└── forcing_bar_count [from utils]
```

---

## 5. SOLID Principles Compliance

| Principle | Rating | Comments |
|-----------|--------|----------|
| **S - Single Responsibility** | 2/5 | utils.py, generate.py violate badly |
| **O - Open/Closed** | 3/5 | Generally good; could use more abstraction |
| **L - Liskov Substitution** | 3/5 | No inheritance issues detected |
| **I - Interface Segregation** | 2/5 | Large classes expose too many methods |
| **D - Dependency Inversion** | 3/5 | Good use of dependency injection overall |

---

## 6. Priority Recommendations

### HIGH PRIORITY

1. **Break down utils.py** into focused modules
   - Effort: 3 hours
   - Impact: Improves maintainability, testability

2. **Refactor generate.py into 4 classes**
   - Effort: 4-5 hours
   - Impact: Reduces complexity, fixes bugs

3. **Fix critical bugs in generate.py**
   - Line 43: device tuple bug
   - Line 209: ValueError not raised
   - Effort: 1 hour

### MEDIUM PRIORITY

4. **Break down encoder.py** into focused classes
5. **Break down decoder.py** similarly
6. **Create configuration management**
7. **Add proper logging**

### LOW PRIORITY

8. Improve test coverage
9. Add type hints throughout
10. Extract helper classes

---

## Related Plans

- [Main Audit Plan](./code-audit-plan.md)
- [Genre Prediction Audit](./audit-genre-prediction.md)
