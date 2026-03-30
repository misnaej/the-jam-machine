# Master Plan - The Jam Machine Refactoring

**Date:** 2026-02-02
**Current Branch:** `main` (branch strategy simplified - all work merges to `main`)

---

## Overview

This document is the **central reference** for all refactoring and improvement work on The Jam Machine codebase. It defines the order of operations and links to detailed sub-plans.

---

## Current State (updated 2026-03-27)

| Area | Status | Notes |
|------|--------|-------|
| Refactoring (Phases 1–10) | ✅ Complete | Package renamed, modules split, examples reorganized |
| Pre-commit hooks (Phase 11) | ✅ Complete | Ruff, interrogate, bandit, pip-audit, badges |
| GitHub Pages (Phase 12) | ✅ Complete | Landing page, encoding guide, embedding explorer |
| Analysis module (Phase 12b) | ✅ Complete | Interactive plotly visualizations, smoke tests |
| Unit tests (Phase 13) | ✅ Complete | 149 tests, 68% coverage |
| Design audit (Phase 14) | ⚠️ Partial | WP1–5, WP8 done; WP6–7, WP9–10 remaining |
| Claude Code setup | ✅ Complete | Skills, agents, hooks configured |
| Code quality | ✅ All ruff rules | `select = ["ALL"]` with targeted ignores |

---

## Plan Documents Index

| # | Plan | Status | Purpose |
|---|------|--------|---------|
| 1 | [Test Plan](./test-plan.md) | ✅ Complete | Unit tests (3 PRs merged) |
| 2 | [Design Audit Findings](./design-audit-findings.md) | ⚠️ In progress | WP1-5, WP8 done; WP6-7, WP9-10 remaining |
| 3 | [GitHub Pages](./github-pages.md) | ✅ Complete | Documentation site live |
| 4 | [Analysis Module](./analysis-module.md) | ✅ Complete | Interactive plotly visualizations |
| 5 | [CI Badges](./ci-badges.md) | ⚠️ Partial | Hooks done, GitHub Actions not yet |
| 6 | [Genre Prediction Audit](./audit-genre-prediction.md) | 📋 Reference | Separate system (optional) |

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

**Details:** *(plan archived — phase complete)*

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

**Details:** *(plan archived — phase complete)*

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

**Details:** *(plan archived — phase complete)*

---

### Phase 6: Split `generating/utils.py` ✅
**Effort:** ~1 hour | **Risk:** Low | **Impact:** SRP compliance

Split into `file_io.py`, `validation.py`, `visualization.py`. Also replaced `WriteTextMidiToFile` class with `write_text_midi_to_file()` function (class was over-engineered — no shared state). Deleted `get_max_time()` (unused). Made `print_inst_classes()` private.

**Details:** *(plan archived — phase complete)*

---

### Phase 7: Split `embedding/encoder.py` ✅
**Effort:** ~2 hours | **Risk:** Medium | **Impact:** SRP compliance

Split 594-line file into `time_processing.py`, `bar_processing.py`, `section_building.py` + slimmed `encoder.py`. Converted 10 `@staticmethod` methods to module functions. Replaced fragile `chain()` with explicit pipeline. Deleted unused `get_text_by_section`, `get_piece_sections`, backward compat alias, `__main__` block.

**Details:** *(plan archived — phase complete)*

---

### Phase 8: Split `embedding/decoder.py` ✅
**Effort:** ~2 hours | **Risk:** Medium | **Impact:** SRP compliance

Split 470-line file into `text_parsing.py`, `event_processing.py` + slimmed `decoder.py`. Converted 10 `@staticmethod` + 1 pseudo-instance method to module functions. No caller changes needed.

**Details:** *(plan archived — phase complete)*

---

### Phase 9: Naming Fixes & Cleanup ✅
**Effort:** ~1 hour | **Risk:** Low | **Impact:** Code quality

Fix typos, remove dead code, delete `unused/` directory.

**Details:** *(plan archived — phase complete)*

**Completed:** Deleted `unused/` directory, removed dead `track_index` variable, removed 3 legacy method aliases in `generate.py`, removed camelCase aliases and deprecated `isJSON` param in `utils.py`, removed dead `__main__` block, updated all callers.

---

### Phase 10: Examples Reorganization ✅
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** DX, documentation

Organize `examples/` with two runnable scripts: encode/decode roundtrip (using Reptilia MIDI) and generation. Clean up scattered MIDI artifacts and test side effects.

**Details:** *(plan archived — phase complete)*

**Completed:** Created `encode_decode.py`, renamed `generation_playground.py` → `generate.py`, fixed test side effects, cleaned up MIDI artifacts, added README, output to `output/examples/` (gitignored). 23 tests pass.

---

### Phase 11: Pre-commit Hook Enhancements ✅
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** Code quality, security

Added docstring coverage (interrogate), security audit (bandit), and pip-audit to the pre-commit hook. All output logged to `.githooks/logs/`. SVG badges generated automatically.

**Completed:** PR #16

---

### Phase 12: GitHub Pages Documentation Site ✅
**Effort:** ~4-6 hours | **Risk:** Low | **Impact:** Documentation, DX

Built GitHub Pages site with Jekyll (Cayman theme): landing page, encoding/decoding guide with Reptilia walkthrough, and embedding explorer HTML page.

**Completed:** PRs #25, #26, #27

---

### Phase 12b: Analysis Module + Notebook Refactor ✅
**Effort:** ~8-10 hours | **Risk:** Medium | **Impact:** Education, visualization, testability

Extracted notebook visualizations into `jammy.analysis` module with 4 submodules (embedding, activation, attention, head_roles). All plots converted to interactive plotly charts. Build script generates self-contained HTML page for GitHub Pages. 18 tests (10 unit + 8 smoke).

**Completed:** PR #29

---

### Phase 13: Add Unit Tests ✅
**Effort:** ~6 hours (3 PRs) | **Risk:** Low | **Impact:** Reliability

Added unit tests across all core modules. 149 tests passing, 68% coverage (up from 22 tests, ~40%).

**Completed:** PRs #17 (generating), #19 (utilities + embedding), #24 (remaining gaps)

---

### Phase 14: Design Audit Fixes ⚠️ In Progress
**Effort:** ~6-8 hours (multiple PRs) | **Risk:** Medium | **Impact:** Code quality, security, correctness

Fix 43 findings from the full codebase design audit. Grouped into 10 work packages.

**Completed:** PRs #20 (ruff all rules), #21 (WP1 security + WP2 side effects + WP3 error handling), #22 (WP5 classes→functions), #23 (WP4 complexity), #24 (WP8 logic bugs), #28 (dependency security)

**Remaining:**
- WP6: DRY violations (instrument lookup, repeated guards)
- WP7: Pythonic idioms (string joins, list comprehensions)
- WP9: Testability improvements (matplotlib global state, hardcoded filenames)
- WP10: Cleanup (commented code, duplicated constants)

**Details:** [Design Audit Findings](./design-audit-findings.md)

---

### Phase 15: HuggingFace Space Deployment from GitHub
**Effort:** ~2-3 hours | **Risk:** Medium | **Impact:** Deployment, DX

The HuggingFace Space is currently a stale manual copy of flat Python files. Modernize it to build directly from the GitHub repo.

**Approach:**
- Configure the HF Space to use a `Dockerfile` or `app.py` entry point that installs from the repo
- The Space should only contain: `Dockerfile` (or `requirements.txt` + `app.py` shim), `README.md`, and `packages.txt` (for FluidSynth)
- The `app.py` shim just imports and runs `app/playground.py` from the installed `jammy` package
- No code duplication — the Space pulls from `main` on every rebuild

**Options:**
1. **Docker-based Space**: `Dockerfile` that clones the repo, installs deps, runs the app
2. **GitHub-linked Space**: HF Spaces supports linking to a GitHub repo directly (auto-sync on push)
3. **pip-installable + shim**: `requirements.txt` with `git+https://github.com/misnaej/the-jam-machine.git` and a thin `app.py`

**Tasks:**
1. Research which approach HF Spaces supports best for Gradio apps
2. Create the deployment config (Dockerfile or requirements.txt)
3. Test locally with Docker
4. Deploy to HuggingFace, verify the app works
5. Set up auto-rebuild on push to `main` (if using GitHub sync)

---

### Phase 16: Docker Build
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** Deployment, reproducibility

Create a Dockerfile for local development and deployment.

**Tasks:**
1. Create `Dockerfile` — Python 3.11, FluidSynth, pip install from repo
2. Create `docker-compose.yml` — mount volumes for output, expose Gradio port
3. Create `.dockerignore` — exclude `.git`, `midi/generated/`, `output/`, etc.
4. Document in README: `docker compose up` to run the app
5. Optionally reuse the same Dockerfile for the HuggingFace Space (Phase 14)

---

### Phase 17: Replace `dict[str, Any]` with typed dataclasses
**Effort:** ~4 hours | **Risk:** Medium | **Impact:** Type safety, expressiveness

Replace `list[dict[str, Any]]` in PieceBuilder with a `TrackState` dataclass. Propagate through generate.py, prompt_handler.py, and playground.py.

---

### Phase 18: Add Doctest for Code Examples
**Effort:** ~1-2 hours | **Risk:** Low | **Impact:** Documentation reliability

Add `--doctest-modules` to pytest, add Example sections to key public functions.

---

### Phase 19: Genre Prediction Cleanup (Optional)
**Effort:** ~4 hours | **Risk:** Medium | **Impact:** Separate system

Fix module-level execution, deduplicate code.

**Details:** [Genre Prediction Audit](./audit-genre-prediction.md)

---

### Phase 20: Python 3.13 Upgrade (Advanced)
**Effort:** ~2-4 hours | **Risk:** High | **Impact:** Future-proofing

Upgrade from Python 3.11 to Python 3.13. Check torch/transformers/miditok compatibility first.

---

### Phase 21: CI Workflow & Badges (when needed)
**Effort:** ~2 hours | **Risk:** Low | **Impact:** CI/CD, visibility

Set up GitHub Actions CI with pytest + coverage (Codecov), docstring coverage (interrogate), security audit (pip-audit + bandit), lint check, and Dependabot. Add badges to README.

**Details:** [CI Workflow, Badges & Security](./ci-badges.md) — all steps except Step 5 (hooks)

---

### Phase 22: Improvise Button (Optional)
**Effort:** TBD | **Risk:** Low | **Impact:** UX

Add an "improvise" button to the Gradio UI that randomizes generation parameters (instrument, density, temperature) for quick exploration. Needs design: which params to randomize, what ranges, whether to auto-generate or just set sliders.

*Developer-driven — requires UX decisions before implementation.*

---

### Phase 23: Add Bars to Existing Generation (Optional)
**Effort:** TBD | **Risk:** Medium | **Impact:** UX

Allow users to append bars to an existing generation instead of starting from scratch. Needs design: how to handle context window limits, whether to regenerate the full piece or just append, UI flow for selecting which track gets new bars.

*Developer-driven — requires UX and architecture decisions before implementation.*

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
| 2026-03-18 | Phase 9-10 complete | Naming fixes, examples reorganized |
| 2026-03-19 | Phase 11 complete | Pre-commit hooks with interrogate, bandit, pip-audit, badges |
| 2026-03-20 | Phase 13 complete | 149 tests, 68% coverage across 3 PRs |
| 2026-03-21 | Phase 14 partial | WP1-5, WP8 done across PRs #20-24 |
| 2026-03-25 | Phase 12 complete | GitHub Pages with Jekyll, encoding guide, embedding explorer |
| 2026-03-27 | Phase 12b complete | Analysis module with plotly charts, smoke tests (PR #29) |

---

## Notes

- Each phase should be a separate commit (or PR if large)
- Run tests after each phase: `pipenv run pytest test/ -v`
- Run linter after each phase: `pipenv run ruff check src/ app/`
- All new code must follow CLAUDE.md standards

---

## Continuation Prompt

**Last completed:** Phase 12b (Analysis module, PR #29)
**Next step:** Phase 14 remaining (WP6, WP7, WP9, WP10) or Phase 15 (HuggingFace Space)
**Notes:** 149 tests, 68% coverage. All ruff checks pass. On `main`.
