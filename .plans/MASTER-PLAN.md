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
| Test coverage | ⚠️ 22 pass | 8 config + 10 track_builder + 4 existing |
| Token constants | ✅ Done | `tokens.py` with 13 constants, ~130 hardcoded strings replaced |
| TrackBuilder | ✅ Done | Converted to module functions, bugs fixed |
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

### Phase 5: Token & Constant Consolidation ✅
**Effort:** ~1 hour | **Risk:** Low | **Impact:** DRY, maintainability

Created `src/jammy/tokens.py` with all MIDI text token constants and replaced ~130 hardcoded string literals across the codebase.

**Completed:**
- Created `src/jammy/tokens.py` with module-level constants (PIECE_START, TRACK_START, TRACK_END, BAR_START, BAR_END, NOTE_ON, NOTE_OFF, TIME_DELTA, TIME_SHIFT, INST, DENSITY, DRUMS, UNK)
- Replaced hardcoded strings in `generating/` (generate.py, piece_builder.py, track_builder.py, prompt_handler.py, utils.py, generation_engine.py, config.py)
- Replaced hardcoded strings in `embedding/` (familizer.py, decoder.py)
- Replaced hardcoded strings in `utils.py` (get_text, get_event)
- Updated tests to use constants (test_config.py, test_generate.py, test_encoder.py)
- Removed all token-related `# noqa: S105/S106` suppressions
- All 12 tests pass, all lint checks pass

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 2

---

### Phase 6: Split `generating/utils.py` ✅
**Effort:** ~1 hour | **Risk:** Low | **Impact:** SRP compliance

Split into `file_io.py`, `validation.py`, `visualization.py`. Also replaced `WriteTextMidiToFile` class with `write_text_midi_to_file()` function (class was over-engineered — no shared state). Deleted `get_max_time()` (unused). Made `print_inst_classes()` private.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 3

---

### Phase 7: Split `embedding/encoder.py` ✅
**Effort:** ~2 hours | **Risk:** Medium | **Impact:** SRP compliance

Split 594-line file into `time_processing.py`, `bar_processing.py`, `section_building.py` + slimmed `encoder.py`. Converted 10 `@staticmethod` methods to module functions. Replaced fragile `chain()` with explicit pipeline. Deleted unused `get_text_by_section`, `get_piece_sections`, backward compat alias, `__main__` block.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 4

---

### Phase 8: Split `embedding/decoder.py` ✅
**Effort:** ~2 hours | **Risk:** Medium | **Impact:** SRP compliance

Split 470-line file into `text_parsing.py`, `event_processing.py` + slimmed `decoder.py`. Converted 10 `@staticmethod` + 1 pseudo-instance method to module functions. No caller changes needed.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 5

---

### Phase 9: Naming Fixes & Cleanup ✅
**Effort:** ~1 hour | **Risk:** Low | **Impact:** Code quality

Fix typos, remove dead code, delete `unused/` directory.

**Details:** [Design Audit Implementation](./design-audit-implementation-plan.md) - Phase 6

**Completed:** Deleted `unused/` directory, removed dead `track_index` variable, removed 3 legacy method aliases in `generate.py`, removed camelCase aliases and deprecated `isJSON` param in `utils.py`, removed dead `__main__` block, updated all callers.

---

### Phase 10: Examples Reorganization ✅
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** DX, documentation

Organize `examples/` with two runnable scripts: encode/decode roundtrip (using Reptilia MIDI) and generation. Clean up scattered MIDI artifacts and test side effects.

**Details:** [Examples Reorganization](./examples-reorganization.md)

**Completed:** Created `encode_decode.py`, renamed `generation_playground.py` → `generate.py`, fixed test side effects, cleaned up MIDI artifacts, added README, output to `output/examples/` (gitignored). 23 tests pass.

---

### Phase 11: Pre-commit Hook Enhancements
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** Code quality, security

Add docstring coverage (interrogate) and security audit (bandit) to the pre-commit hook. All hook output logged to `.githooks/logs/` so agents and users can diagnose failures.

**Details:** [CI Workflow, Badges & Security](./ci-badges.md) — Step 5 (hook updates)

---

### Phase 12: GitHub Pages Documentation Site
**Effort:** ~4-6 hours | **Risk:** Low | **Impact:** Documentation, DX

Build a GitHub Pages site with: landing page (what is The Jam Machine), encoding/decoding guide (pipeline walkthrough, quantization caveats, worked Reptilia example), and the embedding explorer notebook rendered as HTML. Also fix the notebook (hardcoded paths, broken cells, move deps to optional group).

**Details:** [GitHub Pages](./github-pages.md)

---

### Phase 13: Add Unit Tests
**Effort:** ~4 hours | **Risk:** Low | **Impact:** Reliability

Add unit tests for refactored modules, target 70% coverage.

**Details:** [Test Coverage Audit](./test-coverage-audit.md) - Phases 2-4

---

### Phase 14: Replace `dict[str, Any]` with typed dataclasses in PieceBuilder
**Effort:** ~4 hours | **Risk:** Medium | **Impact:** Type safety, expressiveness

Replace `list[dict[str, Any]]` in PieceBuilder with a `TrackState` dataclass. Propagate through generate.py, prompt_handler.py, and playground.py.

---

### Phase 15: Add Doctest for Code Examples
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** Documentation reliability

Add `--doctest-modules` to pytest, add Example sections to key public functions.

---

### Phase 16: Genre Prediction Cleanup (Optional)
**Effort:** ~4 hours | **Risk:** Medium | **Impact:** Separate system

Fix module-level execution, deduplicate code.

**Details:** [Genre Prediction Audit](./audit-genre-prediction.md)

---

### Phase 17: Python 3.13 Upgrade (Advanced)
**Effort:** ~2-4 hours | **Risk:** High | **Impact:** Future-proofing

Upgrade from Python 3.11 to Python 3.13. Check torch/transformers/miditok compatibility first.

---

### Phase 18: CI Workflow & Badges (when needed)
**Effort:** ~2 hours | **Risk:** Low | **Impact:** CI/CD, visibility

Set up GitHub Actions CI with pytest + coverage (Codecov), docstring coverage (interrogate), security audit (pip-audit + bandit), lint check, and Dependabot. Add badges to README.

**Details:** [CI Workflow, Badges & Security](./ci-badges.md) — all steps except Step 5 (hooks)

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
| 2026-02-09 | Phase 5 complete | Created `tokens.py`, replaced ~130 hardcoded strings, removed `# noqa: S105/S106` suppressions |
| 2026-02-09 | Phase 5.5: Fix track builder review findings | Converted TrackBuilder to module functions, fixed extract_tracks type bug, deduplicated track-parsing logic, removed YAGNI stubs, added 10 tests |
| 2026-03-17 | Merged Phase 5 + 5.5 (PR #8) | Squash-merged token consolidation + track builder fixes to main |
| 2026-03-17 | Phase 6 complete | Split `generating/utils.py` into `file_io.py`, `validation.py`, `visualization.py`; replaced `WriteTextMidiToFile` class with function; deleted unused `get_max_time()` |
| 2026-03-18 | Phase 7 complete | Split `embedding/encoder.py` into `time_processing.py`, `bar_processing.py`, `section_building.py`; converted 10 staticmethods to functions; replaced `chain()` with explicit pipeline; deleted unused methods and backward compat alias |
| 2026-03-18 | Phase 8 complete | Split `embedding/decoder.py` into `text_parsing.py`, `event_processing.py`; converted 11 methods to module functions; deleted `__main__` block; no caller changes needed |

---

## Notes

- Each phase should be a separate commit (or PR if large)
- Run tests after each phase: `pipenv run pytest test/ -v`
- Run linter after each phase: `pipenv run ruff check src/ app/`
- All new code must follow CLAUDE.md standards

---

## Continuation Prompt

**Last completed:** Phase 8 (Split `embedding/decoder.py`)
**Next step:** Phase 11 (Pre-commit Hook Enhancements)
**Notes:** All ruff checks pass. 22 tests pass. On `refactor/split-embedding-decoder` branch.
