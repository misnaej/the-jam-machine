# Design Audit Findings

**Date:** 2026-03-25
**Status:** Planned
**Total findings:** 43 (2 Critical, 13 High, 20 Medium, 8 Low)

---

## Scope

Full codebase audit of `src/jammy/`, `app/`, `examples/` using the updated design-reviewer agent (9-section checklist: logic, architecture, complexity, anti-patterns, idioms, testability, error handling, security, naming).

---

## Action Plan

Findings are grouped into work packages that can be tackled as separate PRs.

### WP1: Security fixes (Critical) — do first

| # | File | Issue | Fix |
|---|------|-------|-----|
| 1 | `training/trainer.py:25` | Hardcoded secrets import (`from jammy.passwords import`) | Use `os.environ["HF_TOKEN"]` |
| 2 | `training/trainer.py:117` | Token passed to TrainingArguments (serialized to JSON) | Pass via env var, not kwarg |

### WP2: Module-level side effects (High) — do with tests

| # | File | Issue | Fix |
|---|------|-------|-----|
| 3 | `training/trainer.py:49-151` | Entire training pipeline runs on import | Wrap in `main()` + `__main__` guard |
| 4 | `stats/track_stats_for_encoding.py:185` | `stats_on_track()` called on import | Add `__main__` guard |

### WP3: Error handling (High)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 5 | `preprocessing/midi_stats.py:418` | Bare `except Exception` in `average_tempo` | Narrow to `ValueError` |
| 6 | `preprocessing/midi_stats.py:563` | Bare `except Exception` in `single_file_statistics` | Narrow to `(OSError, ValueError, KeyError)` |
| 7 | `preprocessing/mmd_metadata.py:64` | Bare `except Exception` in `get_single_artist_title` | Narrow to `IndexError` |
| 8 | `utils.py:48` | `compute_list_average` crashes on empty list | Guard against empty or use `statistics.mean()` |

### WP4: Complexity (High) — may split across PRs

| # | File | Issue | Fix |
|---|------|-------|-----|
| 9 | `embedding/text_parsing.py:17-89` | `text_to_events` 72 lines, ~12 branches | Extract quantization logic |
| 10 | `app/playground.py:90-176` | `_generator` 86 lines, multiple concerns | Extract helper functions |
| 11 | `stats/track_stats_for_encoding.py:54-179` | `stats_on_track` 125 lines, print, auto-import | Refactor completely |

### WP5: Classes → functions (High)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 12 | `preprocessing/load.py` | `LoadModel` used as `LoadModel(x).load()` — function disguised as class | Convert to `load_model_and_tokenizer()` |
| 13 | `preprocessing/midi_stats.py:548` | `MidiStats` has no instance state | Convert methods to functions |
| 14 | `embedding/familizer.py:150` | Dynamic attribute assignment for control flow | Pass `operation` as parameter |

### WP6: DRY violations (High)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 15 | `midi_stats.py:30` + `familizer.py:46` | Duplicate instrument lookup logic | Shared utility function |
| 16 | `midi_stats.py:57-534` | 20+ repeated `if pm.instruments:` guards | Extract `_get_all_notes(pm)` helper |

### WP7: Pythonic idioms (Medium)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 17 | `encoder.py:104` | String concatenation in loop | `"".join(...)` |
| 18 | `piece_builder.py:159-174` | String concatenation in loop | `"".join(...)` |
| 19 | `track_builder.py:57` | String concatenation in loop | `"".join(...)` |
| 20 | `playground.py:189` | String concatenation in loop | `"".join(...)` |
| 21 | `decoder.py:76` | Append loop → comprehension | List comprehension |
| 22 | `visualization.py:68` | Append loop → comprehension | List comprehension |
| 23 | `utils.py:20` | Manual loop → `next()` with generator | One-liner |
| 24 | `midi_stats.py:518` | `len([...])` → `len(pm.lyrics)` | Direct len |
| 25 | `midi_stats.py:330` | Materializes list to count | Use `sum()` |

### WP8: Logic bugs (Medium)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 26 | `mmd_metadata.py:222` | `filter_midis` result discarded (silent no-op) | Assign back to `self.stats` |
| 27 | `midi_stats.py:397` | `n_tempo_changes` returns tuple len (always 2) | Fix to `len(pm.get_tempo_changes()[0])` |
| 28 | `playground.py:139` | `_generator` mutates input `state` list | Work on a copy |

### WP9: Testability (Medium)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 29 | `visualization.py:15` | Global matplotlib state on import | Move to setup function or `rc_context` |
| 30 | `section_building.py:32` | `Familizer()` created inside function | Dependency injection |
| 31 | `playground.py:156` | Hardcoded `"mixed.mid"` filename | Use temp files for concurrent safety |

### WP10: Cleanup (Medium/Low)

| # | File | Issue | Fix |
|---|------|-------|-----|
| 32 | `visualization.py:28` | `_BEATS_PER_BAR = 4` duplicates constant | Import from `constants.py` |
| 33 | `familizer.py:202`, `trainer.py:73`, `track_stats.py:182` | Commented-out code | Remove |
| 34 | `constants.py:25` | Typo "decodiing" | Fix |
| 35 | `constants.py:130-131` | Misleading quantization comments | Correct |
| 36 | `trainer_utils.py:106` | `assert` for runtime validation | Use `raise ValueError` |
| 37 | `trainer_utils.py:143` | Fragile dict length check | Check for specific keys |
| 38 | `trainer_utils.py:22` | `TokenizeDataset` class → function | Convert |
| 39 | `midi_stats.py:492` | Redundant `len == 1` check | Remove |
| 40 | `track_stats.py:175` | Unused `_fig, _ax` variable | Remove |
| 41 | `mmd_metadata.py:109` | Nesting depth > 3 | Extract helper |
| 42 | `bar_processing.py:29` | Nesting depth > 3 | Extract helper |
| 43 | `playback.py:1` | Missing module docstring | Add |

---

## Execution Order

1. **WP1** (security) — immediate, before any other work
2. **WP2** (side effects) — quick wins, unblocks testability
3. **WP3** (error handling) — straightforward fixes
4. **WP7** (pythonic idioms: string joins) — quick, high impact on core modules
5. **WP8** (logic bugs) — real bugs that affect correctness
6. **WP4-WP6** (complexity, classes, DRY) — larger refactors, one PR per WP
7. **WP9-WP10** (testability, cleanup) — polish

Some of these overlap with the test PRs — WP7/WP8 issues in `piece_builder.py`, `track_builder.py`, `encoder.py` should be fixed alongside the test work.

---

## Out of scope

- `training/trainer.py` and `training/trainer_utils.py` — training pipeline, separate workflow. Fix security (WP1) and side effects (WP2) only.
- `preprocessing/midi_stats.py` and `preprocessing/mmd_metadata.py` — data analysis scripts. Fix bugs (WP8) and error handling (WP3) only. Full refactor is low priority.
- `stats/track_stats_for_encoding.py` — debugging tool. Fix side effect (WP2) only.
