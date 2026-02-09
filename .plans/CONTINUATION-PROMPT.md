# Continuation Prompt

**Branch:** `main`

## Context

Refactoring The Jam Machine. Package renamed from `the_jam_machine` to `jammy`.

## Start Here

Read `.plans/MASTER-PLAN.md` - it's the central reference with ordered phases.

## Key Plans

| Plan | Purpose |
|------|---------|
| `MASTER-PLAN.md` | Order of operations (16 phases) |
| `design-audit-implementation-plan.md` | Detailed implementation steps |
| `test-coverage-audit.md` | Test improvements |

## Current Status

- Phase 1 (Postponed Annotations) ✅ Complete
- Phase 2 (Package Rename & Absolute Imports) ✅ Complete
- Phase 3 (Fix Broken Tests) ✅ Complete
- Phase 3.5 (Test Restructuring) ✅ Complete
- Phase 4 (Config Dataclasses) ✅ Complete (PR #6)
- Phase 5 (Token & Constant Consolidation) ✅ Complete
- All ruff lint checks pass ✅
- Tests: 12 pass

## Just Completed (Phase 5 — Token & Constant Consolidation)

- Created `src/jammy/tokens.py` with module-level MIDI text token constants
- Constants: PIECE_START, TRACK_START, TRACK_END, BAR_START, BAR_END, NOTE_ON, NOTE_OFF, TIME_DELTA, TIME_SHIFT (legacy), INST, DENSITY, DRUMS, UNK
- Replaced hardcoded strings across `generating/` (7 files), `embedding/` (2 files), and `utils.py`
- Converted `get_event()` in `utils.py` from `match/case` to `if/elif` (match/case doesn't work with variable patterns)
- Updated tests: `test_config.py`, `test_generate.py`, `test_encoder.py`
- Removed all token-related `# noqa: S105/S106` suppressions
- Skipped `DEFAULT_VELOCITY = 99` (only used in one place — decoder.py)

## Review Findings (not addressed — pre-existing issues)

- **High:** `extract_tracks` in `track_builder.py:39` passes `list[str]` to `strip_track_ends(str)` — latent type bug
- **Medium:** `TrackBuilder` is all-static methods — should be module functions (CLAUDE.md: "prefer functions over classes")
- **Medium:** Duplicated track-parsing logic between `PromptHandler._extract_tracks_from_prompt` and `TrackBuilder.extract_tracks`
- **Low:** Several YAGNI stubs (`check_if_prompt_density_in_tokenizer_vocab`, `check_bar_count_in_section`)

## Next Steps (from MASTER-PLAN)

1. **Phase 6**: Split `generating/utils.py`
2. **Phase 7**: Split `embedding/encoder.py`

## Commands

```bash
pipenv run pytest test/ -v           # Run tests (12 pass)
pipenv run ruff check src/ test/     # Lint (should pass)
pipenv run python app/playground.py  # Run app
```
