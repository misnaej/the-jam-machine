# Phase 14: Design Audit Fixes — Implementation Plan

**Date:** 2026-03-25
**Status:** Planned
**Original findings:** 43 (from `.plans/design-audit-findings.md`)
**Already fixed:** 17 (in PRs #19 and #20)
**Remaining:** 26

---

## Pre-Implementation Checklist

- [ ] Read `CLAUDE.md` for coding standards
- [ ] Read `.plans/MASTER-PLAN.md` for context
- [ ] Read `.plans/design-audit-findings.md` for the full audit

---

## What's Already Done

| WP | Items | Fixed in |
|----|-------|----------|
| WP7 | #17-23 (string joins, comprehensions, `next()`) | PR #19 |
| WP8 | #28 (playground state mutation) | PR #19 |
| WP8 | PieceBuilder shared reference bug | PR #19 |
| WP3 | #7 (mmd_metadata bare except → IndexError/TypeError) | PR #20 |
| WP10 | DTZ005 (naive datetime) | PR #20 |
| Ruff | EM102, TRY003, PLC0415, RET504, PERF401/402, LOG015 | PR #20 |

---

## Remaining Work — 4 PRs

### PR 1: Security + Side Effects + Error Handling (WP1 + WP2 + WP3)
**Scope:** Small — straightforward fixes, no API changes
**Branch:** `fix/security-and-side-effects`

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `training/trainer.py:25` | `from jammy.passwords import` | Use `os.environ["HF_READ_TOKEN"]` etc. |
| 2 | `training/trainer.py:117` | Token serialized in TrainingArguments | Pass via env var |
| 3 | `training/trainer.py:49-151` | Module-level side effects | Wrap in `main()` + `__main__` guard |
| 4 | `stats/track_stats_for_encoding.py:185` | Auto-executes on import | Add `__main__` guard |
| 5 | `preprocessing/midi_stats.py:418` | Bare except in `average_tempo` | Narrow to `ValueError` |
| 6 | `preprocessing/midi_stats.py:563` | Bare except in `single_file_statistics` | Narrow to `(OSError, ValueError, KeyError)` |
| 8 | `utils.py` | `compute_list_average` crashes on empty list | Guard with `if not values: return 0.0` |

**Ruff ignores removed after this PR:** `BLE001`, `ERA001` (partially — trainer commented code)

### PR 2: Classes → Functions + DRY (WP5 + WP6)
**Scope:** Medium — API changes, callers must be updated
**Branch:** `refactor/classes-to-functions`

| # | File | Issue | Fix |
|---|------|-------|-----|
| 12 | `preprocessing/load.py` | `LoadModel` class → function | `load_model_and_tokenizer(path, ...)` |
| 13 | `preprocessing/midi_stats.py:548` | `MidiStats` class → functions | `single_file_statistics()`, `get_stats()` |
| 14 | `embedding/familizer.py:150` | Dynamic attribute assignment | Pass `operation` as parameter to methods |
| 15 | `midi_stats.py` + `familizer.py` | Duplicate instrument lookup | Shared `get_instrument_family()` in constants |
| 16 | `midi_stats.py` | 20+ repeated `if pm.instruments:` guards | Extract `_get_all_notes(pm)` helper |

**Callers to update:** `app/playground.py`, `examples/generate.py`, `test/conftest.py`, `test/preprocessing/test_load.py`, `examples/encode_decode.py`

**Ruff ignores removed after this PR:** `PLR0913` (LoadModel args reduced), `A001` (if shadowing is in these files)

### PR 3: Complexity Reduction (WP4)
**Scope:** Medium — refactoring, no API changes
**Branch:** `refactor/reduce-complexity`

| # | File | Issue | Fix |
|---|------|-------|-----|
| 9 | `text_parsing.py:17-89` | `text_to_events` too complex (C901) | Extract `_check_over_quantization()` helper |
| 10 | `playground.py:90-176` | `_generator` too long (PLR0913, PLR0915) | Extract `_find_track_index()`, `_build_result()` |
| 11 | `stats/track_stats_for_encoding.py:54-179` | `stats_on_track` 125 lines | Extract helpers, replace `print` with logging |

**Ruff ignores removed after this PR:** `C901`, `PLR0915`, `PLR0913`

### PR 4: Testability + Cleanup (WP9 + WP10)
**Scope:** Small — quick fixes
**Branch:** `refactor/testability-cleanup`

| # | File | Issue | Fix |
|---|------|-------|-----|
| 24 | `midi_stats.py:518` | `len([...])` → `len(pm.lyrics)` | Direct len |
| 25 | `midi_stats.py:330` | Materializes list to count | Use `sum()` |
| 26 | `mmd_metadata.py:222` | `filter_midis` result discarded | Assign back |
| 27 | `midi_stats.py:397` | `n_tempo_changes` returns wrong value | Fix to `len(pm.get_tempo_changes()[0])` |
| 29 | `visualization.py:15` | Global matplotlib state on import | Use `rc_context` |
| 30 | `section_building.py:32` | `Familizer()` created inline | Dependency injection |
| 31 | `playground.py:156` | Hardcoded `"mixed.mid"` filename | Use temp files |
| 32 | `visualization.py:28` | `_BEATS_PER_BAR` duplicates constant | Import from constants |
| 33 | Multiple files | Commented-out code | Remove |
| 34 | `constants.py:25` | Typo "decodiing" | Fix |
| 35 | `constants.py:130-131` | Misleading quantization comments | Correct |
| 36 | `trainer_utils.py:106` | `assert` for runtime validation | `raise ValueError` |
| 37 | `trainer_utils.py:143` | Fragile dict length check | Check specific keys |
| 38 | `trainer_utils.py:22` | `TokenizeDataset` class → function | Convert |
| 39 | `midi_stats.py:492` | Redundant `len == 1` check | Remove |
| 40 | `track_stats.py:175` | Unused `_fig, _ax` | Remove |
| 41 | `mmd_metadata.py:109` | Nesting > 3 levels | Extract helper |
| 42 | `bar_processing.py:29` | Nesting > 3 levels | Extract helper |
| 43 | `playback.py:1` | Missing module docstring | Add |

**Ruff ignores removed after this PR:** `ERA001`, `PLR0911` (if dispatch simplified), `ICN001` (if matplotlib alias fixed)

---

## Goal: Remove All Ruff Ignores

After all 4 PRs, the ignore list in `pyproject.toml` should be reduced to only:
- `ISC001` — genuine formatter conflict
- `FBT001/002` — boolean args are a style choice, not a bug
- `TD002/003`, `FIX002` — TODO style is a project decision
- `INP001` — `app/` and `examples/` are intentionally not packages
- `PLR2004` — magic values are expected with token comparisons
- `PD002` — pandas inplace is acceptable in preprocessing scripts

Everything else should be fixed.

---

## Workflow Requirements

After each PR:
1. Run `/check` to verify all tests pass
2. Run `/review` on changed files
3. Update `.plans/CONTINUATION-PROMPT.md` with progress
4. Verify ruff ignores can be removed for fixed rules

After phase complete:
1. Update `.plans/MASTER-PLAN.md` — mark Phase 14 complete
2. Update `pyproject.toml` — remove resolved ignores
3. Run `/check` one final time

---

## Post-Implementation Tasks

1. Update MASTER-PLAN.md
2. Update CONTINUATION-PROMPT.md
3. Run agents (docs-reviewer, design-reviewer)
4. Delete `.plans/design-audit-findings.md` (superseded by this plan)
5. Update `.plans/ruff-all-rules.md` with final ignore list
