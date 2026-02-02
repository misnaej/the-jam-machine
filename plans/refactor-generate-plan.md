# Plan: Refactor generate.py

**Date:** 2026-02-02
**Branch:** `refactor/generate-split` (PR #2 open against `dev`)
**Status:** ✅ **COMPLETE**
**Prerequisites:** Read `CLAUDE.md` for coding standards, git workflow, and commit style

---

## Overview

This plan addresses the largest SRP violation in the codebase: `src/the_jam_machine/generating/generate.py` (440+ lines, 30+ methods). We will:

1. **Part 1:** Fix 3 critical bugs (quick wins)
2. **Part 2:** Split the monolithic class into 4 focused classes

---

## Part 1: Fix Critical Bugs

### Bug 1: Device Tuple (Line 43)

**File:** `src/the_jam_machine/generating/generate.py`
**Line:** 43
**Issue:** `self.device = ("cpu",)` creates a tuple instead of a string

**Current:**
```python
self.device = ("cpu",)
```

**Fix:**
```python
self.device = "cpu"
```

---

### Bug 2: ValueError Not Raised (Line 207)

**File:** `src/the_jam_machine/generating/generate.py`
**Line:** 207
**Issue:** `ValueError()` is created but not raised

**Current:**
```python
if self.temperature is None:
    ValueError("Temperature must be defined")
```

**Fix:**
```python
if self.temperature is None:
    raise ValueError("Temperature must be defined")
```

---

### Bug 3: Unused Parameter (Line 404-405)

**File:** `src/the_jam_machine/generating/generate.py`
**Line:** 404-405
**Issue:** `only_this_track` parameter is assigned to itself (no-op)

**Current:**
```python
def get_whole_piece_from_bar_dict(self, only_this_track=None):
    only_this_track = only_this_track
```

**Investigation needed:** Determine if this parameter should filter tracks or if it's dead code. Check usage in codebase.

---

## Part 2: Split into Focused Classes

### Target Architecture

```
src/the_jam_machine/generating/
├── generate.py              # Public API (GenerateMidiText) - orchestrator only
├── generation_engine.py     # Low-level model interaction
├── piece_builder.py         # State management (piece_by_track dict)
├── track_builder.py         # Track-level text operations
└── prompt_handler.py        # Prompt manipulation and length control
```

---

### Class 1: GenerationEngine

**File:** `src/the_jam_machine/generating/generation_engine.py`
**Responsibility:** Low-level model interaction (tokenization, generation, decoding)

**Methods to extract from GenerateMidiText:**
- `tokenize_input_prompt()` (lines ~140-150)
- `generate_sequence_of_token_ids()` (lines ~152-175)
- `convert_ids_to_text()` (lines ~177-185)

**New class structure:**
```python
class GenerationEngine:
    """Handles low-level GPT-2 model interaction."""

    def __init__(self, model, tokenizer, device: str = "cpu"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def tokenize(self, prompt: str) -> torch.Tensor:
        """Tokenize input prompt."""

    def generate_ids(self, input_ids: torch.Tensor, max_length: int, temperature: float) -> torch.Tensor:
        """Generate sequence of token IDs."""

    def decode(self, token_ids: torch.Tensor) -> str:
        """Convert token IDs back to text."""

    def generate(self, prompt: str, max_length: int, temperature: float) -> str:
        """Full generation pipeline: tokenize -> generate -> decode."""
```

---

### Class 2: PieceBuilder

**File:** `src/the_jam_machine/generating/piece_builder.py`
**Responsibility:** Manage piece_by_track state dictionary

**Methods to extract from GenerateMidiText:**
- `initiate_track_dict()` (lines ~60-80)
- `update_track_dict__add_bars()` (lines ~82-100)
- `update_track_dict__add_track()` (lines ~102-120)
- `get_all_tracks_from_piece_by_track()` (lines ~380-395)
- `get_whole_piece_from_bar_dict()` (lines ~400-415)

**New class structure:**
```python
class PieceBuilder:
    """Manages the piece_by_track state dictionary."""

    def __init__(self):
        self.piece_by_track: dict = {}

    def init_track(self, track_id: int, instrument: str, density: int, temperature: float) -> None:
        """Initialize a new track in the piece."""

    def add_bars_to_track(self, track_id: int, bars: list[str]) -> None:
        """Add generated bars to an existing track."""

    def get_track(self, track_id: int) -> dict:
        """Get a single track by ID."""

    def get_all_tracks(self) -> list[dict]:
        """Get all tracks."""

    def build_piece_text(self, only_track: int | None = None) -> str:
        """Combine all tracks into final piece text."""
```

---

### Class 3: TrackBuilder

**File:** `src/the_jam_machine/generating/track_builder.py`
**Responsibility:** Track-level text manipulation

**Methods to extract from GenerateMidiText:**
- `get_tracks_from_a_piece()` (lines ~270-290)
- `get_newly_generated_text()` (lines ~292-310)
- `striping_track_ends()` → rename to `strip_track_ends()` (lines ~312-330)
- `track_to_text()` (lines ~332-350)
- `get_bars_from_track()` (lines ~352-370)

**New class structure:**
```python
class TrackBuilder:
    """Handles track-level text operations."""

    @staticmethod
    def extract_tracks(piece_text: str) -> list[str]:
        """Split piece text into individual tracks."""

    @staticmethod
    def extract_bars(track_text: str) -> list[str]:
        """Split track text into individual bars."""

    @staticmethod
    def strip_track_ends(track_text: str) -> str:
        """Remove TRACK_START/TRACK_END tokens."""

    @staticmethod
    def build_track_text(bars: list[str], instrument: str, density: int) -> str:
        """Combine bars into track text with proper tokens."""

    @staticmethod
    def get_new_content(full_text: str, prompt: str) -> str:
        """Extract newly generated content (full minus prompt)."""
```

---

### Class 4: PromptHandler

**File:** `src/the_jam_machine/generating/prompt_handler.py`
**Responsibility:** Prompt construction and length management

**Methods to extract from GenerateMidiText:**
- `generate_prompt_from_piece_by_track()` (lines ~185-205)
- `process_prompt_for_next_bar()` (lines ~207-230)
- `force_prompt_length()` (lines ~355-378)

**New class structure:**
```python
class PromptHandler:
    """Handles prompt construction and length management."""

    MAX_PROMPT_LENGTH = 1500  # Extract magic number as constant

    def __init__(self, n_bars: int = 8):
        self.n_bars = n_bars

    def build_prompt(self, piece_builder: PieceBuilder, current_track: int) -> str:
        """Build generation prompt from current piece state."""

    def prepare_next_bar_prompt(self, current_prompt: str, track_id: int) -> str:
        """Prepare prompt for generating the next bar."""

    def enforce_length_limit(self, prompt: str, max_length: int | None = None) -> str:
        """Truncate prompt to fit within token limit."""
```

---

### Class 5: GenerateMidiText (Refactored Orchestrator)

**File:** `src/the_jam_machine/generating/generate.py`
**Responsibility:** Public API, orchestrates the other classes

**New class structure:**
```python
from .generation_engine import GenerationEngine
from .piece_builder import PieceBuilder
from .track_builder import TrackBuilder
from .prompt_handler import PromptHandler

class GenerateMidiText:
    """Main orchestrator for MIDI text generation."""

    def __init__(self, model, tokenizer, piece_by_track: list | None = None):
        self.engine = GenerationEngine(model, tokenizer)
        self.piece = PieceBuilder()
        self.tracks = TrackBuilder()
        self.prompts = PromptHandler()

        # Restore state if provided
        if piece_by_track:
            self._restore_state(piece_by_track)

    def set_nb_bars_generated(self, n_bars: int) -> None:
        """Set number of bars to generate."""
        self.prompts.n_bars = n_bars

    def generate_piece(
        self,
        instruments: list[str],
        densities: list[int],
        temperatures: list[float],
    ) -> None:
        """Generate a complete piece with multiple tracks."""

    def generate_one_more_bar(self, track_id: int) -> str:
        """Generate one additional bar for a track."""

    def get_whole_piece_from_bar_dict(self) -> str:
        """Get the complete piece as text."""
        return self.piece.build_piece_text()

    # ... other public methods delegate to components
```

---

## Implementation Steps

### Step 1: Create Branch
```bash
git checkout dev
git pull origin dev
git checkout -b refactor/generate-split
```

### Step 2: Fix Bugs (Part 1)
1. Read `src/the_jam_machine/generating/generate.py`
2. Fix Bug 1: Line 43 - remove tuple parentheses
3. Fix Bug 2: Line 207 - add `raise`
4. Fix Bug 3: Line 404-405 - investigate and fix or remove
5. Run tests: `pipenv run pytest test/ -v`
6. Commit: "Fix critical bugs in generate.py"

### Step 3: Create New Files (Part 2)
1. Create `generation_engine.py` with GenerationEngine class
2. Create `piece_builder.py` with PieceBuilder class
3. Create `track_builder.py` with TrackBuilder class
4. Create `prompt_handler.py` with PromptHandler class

### Step 4: Extract Methods
For each new class:
1. Copy relevant methods from GenerateMidiText
2. Adapt method signatures (remove self references to old class)
3. Add type hints and docstrings per CLAUDE.md standards
4. Update imports

### Step 5: Refactor Orchestrator
1. Update GenerateMidiText to use new component classes
2. Keep public API unchanged for backwards compatibility
3. Delegate to components instead of implementing directly

### Step 6: Update Imports
1. Check all files that import from `generate.py`
2. Ensure GenerateMidiText is still importable from same location
3. Update `__init__.py` if needed

### Step 7: Test
```bash
pipenv run pytest test/ -v
pipenv run ruff check src/the_jam_machine/generating/
pipenv run ruff format src/the_jam_machine/generating/
```

### Step 8: Commit and PR
```bash
git add src/the_jam_machine/generating/
git commit -m "Refactor generate.py into focused classes"
git push -u origin refactor/generate-split
gh pr create --base dev --title "Refactor GenerateMidiText into focused classes"
```

---

## Verification Checklist

- [x] All 3 bugs fixed
- [x] 4 new files created (generation_engine.py, piece_builder.py, track_builder.py, prompt_handler.py)
- [x] GenerateMidiText refactored to use components
- [x] Public API unchanged (existing code still works)
- [x] Core tests pass (test_generate, test_encode, test_generation_playground)
- [x] Ruff checks pass
- [x] Code formatted
- [x] Type hints on all new functions
- [x] Docstrings on all new classes/methods
- [x] PR created to dev branch

**Note:** Some pre-existing test failures remain (missing test files, wrong paths) - these are not related to this refactor.

---

## Files to Read Before Starting

1. `CLAUDE.md` - Development guidelines, coding standards, git workflow
2. `src/the_jam_machine/generating/generate.py` - Current implementation
3. `src/the_jam_machine/generating/utils.py` - Related utilities
4. `test/test_tosort.py` - Tests that use GenerateMidiText
5. `app/playground.py` - UI that uses GenerateMidiText

---

## Related Plans

- [Main Audit Plan](./code-audit-plan.md)
- [Main Package Audit](./audit-main-package.md)
