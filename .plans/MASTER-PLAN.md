# Master Plan - The Jam Machine Refactoring

**Date:** 2026-02-02
**Current Branch:** `main` (branch strategy simplified - all work merges to `main`)

---

## Overview

This document is the **central reference** for all refactoring and improvement work on The Jam Machine codebase. It defines the order of operations and links to detailed sub-plans.

---

## Current State

| Area | Status | Notes |
|------|--------|-------|
| `generate.py` refactor | ✅ Complete | Split into 4 focused classes |
| Critical bugs | ✅ Fixed | Device tuple, ValueError, dead code |
| Logging | ✅ Added | `logging_config.py` created |
| Config dataclasses | ✅ Done | `TrackConfig` (frozen), `GenerationConfig` (mutable) |
| Test coverage | ⚠️ 12 pass | 8 config tests + 4 existing (Phase 3.5 done) |
| Type hints | ⚠️ Partial | New code has hints, old code doesn't |
| Annotations style | ✅ Done | All files use `from __future__ import annotations` |
| Package rename | ✅ Done | Renamed to `jammy`, absolute imports enforced |

---

## Plan Documents Index

| # | Plan | Status | Purpose |
|---|------|--------|---------|
| 1 | [Code Audit Plan](./code-audit-plan.md) | ✅ Phase 1-4 done | Original audit and setup |
| 2 | [Refactor Generate Plan](./refactor-generate-plan.md) | ✅ Complete | Split generate.py |
| 3 | [Main Package Audit](./audit-main-package.md) | 📋 Reference | Detailed module analysis |
| 4 | [Genre Prediction Audit](./audit-genre-prediction.md) | 📋 Reference | Separate system analysis |
| 5 | [Design Audit](./design-audit.md) | 📋 Reference | Quick summary of issues |
| 6 | [Design Audit Implementation](./design-audit-implementation-plan.md) | 🔜 Next | Detailed implementation steps |
| 7 | [Test Coverage Audit](./test-coverage-audit.md) | 🔜 Pending | Test improvements |
| 8 | [Postponed Annotations Plan](#phase-1-postponed-annotations) | ✅ Done | Type hint cleanup |

---

## Recommended Order of Implementation

### Phase 1: Postponed Annotations (Quick Win)
**Effort:** ~1 hour | **Risk:** Low | **Impact:** Code quality

Add `from __future__ import annotations` to all Python files and remove quoted type hints.

**Why first:**
- Quick, low-risk change
- Sets standard for all subsequent work
- Already documented in CLAUDE.md

**Files to update:**
- All `.py` files in `src/the_jam_machine/`
- `app/playground.py`

**Details:** [See Phase 1 below](#phase-1-postponed-annotations-detailed)

---

### Phase 2: Enforce Absolute Imports & Rename Package ✅
**Effort:** ~1 hour | **Risk:** Medium | **Impact:** Code consistency, DX

Add TID252 rule to enforce absolute imports and rename package from `the_jam_machine` to `jammy`.

**Status:** Complete - package renamed to `jammy`, TID252 enforced, all imports converted to absolute.

**Tasks:**
1. Rename `src/the_jam_machine/` → `src/jammy/`
2. Update `pyproject.toml`: package name, known-first-party
3. Update all imports throughout codebase
4. Add `"TID252"` to ruff select in `pyproject.toml`
5. Update CLAUDE.md project structure
6. Run tests to verify everything works

**Package name candidates:**
- `jammy` ← recommended (short, matches HuggingFace org "JammyMachina")
- `jammer`, `jamgen`, `midijam`

**Why:**
- `the_jam_machine` is verbose (15 chars vs 5)
- Absolute imports are more explicit and grep-friendly
- Shorter imports improve DX: `from jammy.generating import ...`

---

### Phase 3: Fix Broken Tests (Quick Win)
**Effort:** ~30 min | **Risk:** Low | **Impact:** CI/CD readiness

Get all tests passing before making more changes.

**Tasks:**
1. Rename `test_compare_generated_encoded` → `_compare_generated_encoded`
2. Skip or delete `test_decode` and `test_gradio`
3. Add assertions to `test_generate` and `test_encode`

**Details:** [Test Coverage Audit](./test-coverage-audit.md) - Phase 1

---

### Phase 3.5: Test Restructuring ✅
**Effort:** ~1 hour | **Risk:** Low | **Impact:** Test organization

Restructured test directory to mirror `src/jammy/` layout.

**Completed:**
- Created `test/conftest.py` with session-scoped fixtures
- Created `test/fixtures/` with sample data
- Created `test/helpers/comparison.py` with extracted utilities
- Migrated tests to module-specific files (`embedding/`, `generating/`, `preprocessing/`)
- Added placeholder files for Phase 10 unit tests
- Deleted old `test_tosort.py`

**Result:** 4 tests passing, 53% coverage, proper test organization for future development.

---

### Phase 4: Config Dataclasses (PR #2 Feedback) ✅
**Effort:** ~2 hours | **Risk:** Low | **Impact:** API cleanliness

Create `TrackConfig` and `GenerationConfig` dataclasses.

**Status:** Complete — `TrackConfig` (frozen) and `GenerationConfig` dataclasses in `src/jammy/generating/config.py`. `GenerateMidiText` constructor accepts `config=` parameter. `examples/generation_playground.py` refactored to use both.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 1

---

### Phase 4.1: Post-merge cleanup (PR #6 review findings)
**Effort:** ~15 min | **Risk:** Low | **Impact:** Code hygiene

Small issues found during PR #6 review. Do immediately after merging.

**Tasks:**
1. `src/jammy/generating/generate.py:214` — `if failed > -1` is always true (failed starts at 0). The `else` branch on line 223 is dead code. Fix the condition or remove dead branch.
2. `src/jammy/generating/__init__.py` — missing `from __future__ import annotations`. Add for consistency with all other files.
3. `test/generating/test_generate.py:57` — `piece_by_track: list[str] = []` has wrong type annotation. Should be `list[dict[str, Any]]` to match the tightened signature.

---

### Phase 5: Token & Constant Consolidation
**Effort:** ~1 hour | **Risk:** Low | **Impact:** DRY, maintainability

Create `tokens.py` and expand `constants.py`.

**Tasks:**
1. Create `src/the_jam_machine/tokens.py` with token strings
2. Add missing constants to `constants.py`
3. Replace hardcoded values throughout

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 2

---

### Phase 6: Split `generating/utils.py`
**Effort:** ~1 hour | **Risk:** Low | **Impact:** SRP compliance

Split into `file_io.py`, `validation.py`, `visualization.py`.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 3

---

### Phase 7: Split `embedding/encoder.py`
**Effort:** ~2 hours | **Risk:** Medium | **Impact:** SRP compliance

Split 406-line file into focused modules.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 4

---

### Phase 8: Split `embedding/decoder.py`
**Effort:** ~2 hours | **Risk:** Medium | **Impact:** SRP compliance

Split 333-line file into focused modules.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 5

---

### Phase 9: Naming Fixes & Cleanup
**Effort:** ~1 hour | **Risk:** Low | **Impact:** Code quality

Fix typos, remove dead code, delete `unused/` directory.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 6

---

### Phase 10: Add Unit Tests
**Effort:** ~4 hours | **Risk:** Low | **Impact:** Reliability

Add unit tests for refactored modules, target 70% coverage.

**Details:** [Test Coverage Audit](./test-coverage-audit.md) - Phases 2-4

---

### Phase 11: Genre Prediction Cleanup (Optional)
**Effort:** ~4 hours | **Risk:** Medium | **Impact:** Separate system

Fix module-level execution, deduplicate code.

**Details:** [Genre Prediction Audit](./audit-genre-prediction.md)

---

### Phase 12: Dedicated Output Folder
**Effort:** ~30 min | **Risk:** Low | **Impact:** UX, repo cleanliness

Create a dedicated `output/` folder for generated MIDI and audio files.

**Tasks:**
1. Create `output/` directory (gitignored)
2. Add `OUTPUT_DIR` constant to `constants.py`
3. Update `TextDecoder.get_midi()` to use output folder by default
4. Update `playground.py` to save files to output folder
5. Add `output/` to `.gitignore`

**Why:**
- Keeps generated files organized
- Prevents accidental commits of generated files
- Cleaner project root

---

### Phase 13: Python 3.13 Upgrade (Advanced)
**Effort:** ~2-4 hours | **Risk:** High | **Impact:** Future-proofing

Upgrade from Python 3.11 to Python 3.13.

**Prerequisites:**
- All tests passing
- All refactoring complete

**Tasks:**
1. Check dependency compatibility with Python 3.13
   - `torch`, `transformers`, `miditok`, `note-seq` are critical
   - Run `pip index versions <package>` to check support
2. Update `pyproject.toml`: `requires-python = ">=3.13"`
3. Update `CLAUDE.md` prerequisites
4. Update `README.md` badge and prerequisites
5. Test full pipeline (encode, generate, decode)
6. Fix any deprecation warnings or breaking changes

**Blockers to check:**
- PyTorch 3.13 wheels availability
- note-seq compatibility (often lags behind)
- Any C extensions that need rebuilding

**Rollback plan:**
- Keep 3.11 as fallback until all deps confirmed working

---

### Phase 14: Add Doctest for Code Examples
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** Documentation reliability

Add doctest to verify all code examples in docstrings are functional.

**Why:**
- Code examples in documentation can become stale
- Non-functioning examples mislead users
- Doctest catches drift between code and docs automatically

**Tasks:**
1. Add `--doctest-modules` to pytest configuration in `pyproject.toml`
2. Review and fix existing docstring examples
3. Add `Example:` sections to key public functions (encoder, decoder, generator)
4. Configure CI to run doctests

**Verification:**
```bash
pipenv run pytest --doctest-modules src/
```

---

### Phase 15: Remove Backward Compatibility Code
**Effort:** ~30 min | **Risk:** Low | **Impact:** Code cleanliness

Remove all backward compatibility aliases and deprecated parameters.

**Tasks:**
1. **encoder.py** (line 585): Remove `from_MIDI_to_sectionned_text` alias
2. **utils.py**:
   - Remove `writeToFile` alias (line 330)
   - Remove `readFromFile` alias (line 358)
   - Remove deprecated `isJSON` parameter from `read_from_file()`
3. Search for any remaining usages and update to new names
4. Remove associated `# noqa: N816` comments

**Verification:**
```bash
pipenv run ruff check src/ test/
pipenv run pytest test/
```

**Why:**
- The old camelCase names violate Python naming conventions
- Backward compatibility was only needed during migration
- Cleaner codebase without legacy aliases

---

### Phase 16: Replace `dict[str, Any]` with typed dataclasses in PieceBuilder
**Effort:** ~4 hours | **Risk:** Medium | **Impact:** Type safety, expressiveness, future features

**Two-step plan:**

#### Step 1: `TrackState` dataclass (replaces `dict[str, Any]`)

`PieceBuilder` stores tracks as `list[dict[str, Any]]` with a fixed shape `{label, instrument, density, temperature, bars}`. This weak typing propagates to `generate.py`, `prompt_handler.py`, `utils.py`, and `app/playground.py`.

Replace with:
```python
@dataclass
class TrackState:
    """Mutable state of a track during generation."""
    instrument: str
    density: int
    temperature: float
    bars: list[str] = field(default_factory=list)
```

- No `label` field — derive from index (`f"track_{i}"`)
- `PieceBuilder.piece_by_track` becomes `list[TrackState]`
- All `track["bars"]` → `track.bars`, etc.
- `WriteTextMidiToFile` uses `dataclasses.asdict()` for JSON serialization

**Files:** `config.py`, `piece_builder.py`, `generate.py`, `prompt_handler.py`, `utils.py`, `app/playground.py`, test

#### Step 2: `BarConfig` — per-bar generation parameters (future)

Once `TrackState` is in place, the natural next step is splitting density/temperature out so they can evolve per bar. The type hierarchy would be:
- **`BarConfig`** — atomic generation params: `density`, `temperature`
- **`TrackConfig`** — generation input: `instrument` + `BarConfig`
- **`TrackState`** — runtime state: `instrument` + `bars` + current `BarConfig`

This would enable things like "a drum track that gets denser over 8 bars."

**Open questions (for when we get here):**
- Should `BarConfig` live inside `TrackState` or be passed separately per bar?
- How does this interact with `generate_one_more_bar()` in the Gradio app?
- Convenience for the common case of uniform bars?

**Prerequisites:**
- Phase 4 (Config Dataclasses) ✅
- Step 1 (`TrackState`) must be done first

---

## Phase 1: Postponed Annotations (Detailed)

### Goal

Standardize all Python files to use `from __future__ import annotations` for cleaner, safer type hints.

### Why

| Without | With |
|---------|------|
| `model: "GPT2LMHeadModel"` | `model: GPT2LMHeadModel` |
| Typos not caught | Typos caught by type checker |
| Inconsistent style | Consistent style |

### Files to Update

```
src/the_jam_machine/
├── __init__.py                 # Skip (empty)
├── constants.py                # Add import
├── logging_config.py           # Add import
├── utils.py                    # Add import, remove quotes
├── embedding/
│   ├── __init__.py             # Skip (empty)
│   ├── decoder.py              # Add import
│   ├── encoder.py              # Add import
│   ├── familizer.py            # Add import
│   ├── preprocess.py           # Add import
│   └── load.py                 # Check for quotes
├── generating/
│   ├── __init__.py             # Skip (empty)
│   ├── generate.py             # Add import, remove quotes
│   ├── generation_engine.py    # Add import, remove quotes
│   ├── piece_builder.py        # Add import, remove quotes
│   ├── track_builder.py        # Add import
│   ├── prompt_handler.py       # Add import, remove quotes
│   ├── utils.py                # Add import, remove quotes
│   └── playback.py             # Add import
├── preprocessing/
│   ├── __init__.py             # Skip (empty)
│   ├── load.py                 # Add import
│   ├── midi_stats.py           # Add import
│   ├── mmd_metadata.py         # Add import
│   └── picker.py               # Add import
├── stats/
│   ├── __init__.py             # Skip (empty)
│   └── track_stats_for_encoding.py  # Add import
├── training/
│   ├── __init__.py             # Skip (empty)
│   ├── trainer.py              # Add import
│   └── trainer_utils.py        # Add import
└── unused/                     # Skip (will be deleted)

app/
└── playground.py               # Add import
```

### Implementation Steps

1. **For each file:**
   ```python
   # Add at the very top (after any module docstring)
   from __future__ import annotations
   ```

2. **Remove quoted type hints:**
   ```python
   # Before
   def foo(self, model: "GPT2LMHeadModel") -> "str":

   # After
   def foo(self, model: GPT2LMHeadModel) -> str:
   ```

3. **Keep `TYPE_CHECKING` blocks** - they're still needed to avoid runtime imports

### Verification

```bash
# Check for remaining quoted hints (should find none after cleanup)
grep -r '": "' src/ --include="*.py" | grep -v "__pycache__"

# Run type checker
pipenv run mypy src/ --ignore-missing-imports

# Run tests
pipenv run pytest test/ -v
```

### Commit

```bash
git add src/ app/
git commit -m "refactor: add postponed annotations to all modules"
```

---

## Quick Reference: What To Do Next

```
1. Postponed Annotations  ─────►  Quick win, sets standard ✅
         │
         ▼
2. Enforce Absolute Imports  ──►  Code consistency
         │
         ▼
3. Fix Broken Tests  ──────────►  Enables CI confidence
         │
         ▼
4. Config Dataclasses  ────────►  PR #2 feedback
         │
         ▼
5. Token Constants  ───────────►  DRY improvement
         │
         ▼
6. Split generating/utils.py  ─►  Small, isolated change
         │
         ▼
7. Split encoder.py  ──────────►  Larger refactor
         │
         ▼
8. Split decoder.py  ──────────►  Larger refactor
         │
         ▼
9. Naming & Cleanup  ──────────►  Polish
         │
         ▼
10. Add Unit Tests  ───────────►  Increase coverage
         │
         ▼
11. Genre Prediction (Optional) ► Separate system
         │
         ▼
12. Output Folder  ────────────►  UX improvement
         │
         ▼
13. Python 3.13 (Advanced)  ───►  Future-proofing
         │
         ▼
14. Add Doctest  ──────────────►  Documentation reliability
         │
         ▼
15. Remove Backward Compat  ───►  Code cleanliness
         │
         ▼
16. TrackConfig/BarConfig Split ► Time-varying generation
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-02 | Postponed annotations first | Low risk, sets standard |
| 2026-02-02 | Fix tests before more changes | Need CI confidence |
| 2026-02-02 | Config dataclasses before splits | Cleaner API for dependent code |
| 2026-02-02 | Defer genre_prediction | Separate system, lower priority |
| 2026-02-09 | Phase 4 complete | `TrackConfig`, `GenerationConfig` dataclasses, example script refactored |
| 2026-02-09 | Add Phase 16: TrackConfig/BarConfig split | Current `TrackConfig` bundles static identity with per-bar params; need design for time-varying density/temperature |

---

## Notes

- Each phase should be a separate commit (or PR if large)
- Run tests after each phase: `pipenv run pytest test/ -v`
- Run linter after each phase: `pipenv run ruff check src/ app/`
- All new code must follow CLAUDE.md standards

---

## Continuation Prompt

**Last completed:** Phase 4 - Config Dataclasses (PR #6)
**Next step:** Merge PR #6 → Phase 5 (Token & Constant Consolidation)
**Notes:** All ruff checks pass. 12 tests pass. PR #6 reviewed and ready to merge. Phase 16 (TrackState + future BarConfig) added to plan.
