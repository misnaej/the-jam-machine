# Continuation Prompt

**Branch:** `main` (all work merges to `main`)

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

- Phases 1-8 ✅ Complete
- Phase 9 (Naming Fixes & Cleanup) ✅ Complete
- All ruff lint checks pass ✅
- Tests: 22 pass

## What Phase 9 Did

### Original Plan Items
- Deleted `src/jammy/unused/` directory (2 dead files)
- Removed dead `track_index` variable in `text_parsing.py`
- Removed 3 legacy method aliases in `generate.py` (`get_whole_piece_from_bar_dict`, `get_whole_track_from_bar_dict`, `delete_one_track`)
- Removed camelCase aliases (`writeToFile`, `readFromFile`) and deprecated `isJSON` param in `utils.py`
- Removed dead `__main__` block in `generate.py`

### Pre-existing Issues Fixed (from design/docs reviewer agents)
- Split `utils.py` into focused modules: `midi_codec.py` (encoding/decoding), `file_utils.py` (file I/O), slim `utils.py` (generic helpers)
- Removed `chain()` function (swallowed TypeError silently), inlined in `time_delta_to_int_dec_base`
- Fixed `write_to_file` inconsistent `mkdir` (now applies to both dict and non-dict paths)
- Extracted `get_beat_resolution()` helper (replaced 4 duplicate ternary patterns)
- Fixed `preprocess.py`: added docstring, wrapped in `main()` guard, narrowed bare `except Exception` to specific types, removed dead comment, unified miditok config via `get_miditok()`
- Renamed `set_nb_bars_generated` → `set_n_bars_generated`
- Renamed `_check_for_errors` param `piece` → `piece_text`
- Fixed hardcoded `"PIECE_START "` strings → `f"{PIECE_START} "` in `playground.py`
- Added `GeneratorResult` NamedTuple (replaced 8-element tuple) with documented attributes
- Extracted `SAMPLE_RATE` constant in `playground.py`
- Added `@functools.wraps` to `timeit` decorator
- Made `get_miditok()` a singleton via `@lru_cache(maxsize=1)`
- Moved heavy imports (numpy, pydub, scipy, joblib) to lazy imports in `file_utils.py`
- Removed dead re-exports from `utils.py`
- Fixed bare string literal as section comment in `constants.py`
- Added module docstring + class attribute docs to `familizer.py`
- Fixed `get_stats` type hint mismatch in `midi_stats.py`
- Removed stale `# TODO: include types` comment
- Added explanatory comment on `get_event` about why if/elif vs match/case

## Next Steps (from MASTER-PLAN)

1. **Phase 10**: Add Unit Tests
2. **Phase 11**: Genre Prediction Cleanup (Optional)

See `test-coverage-audit.md` for Phase 10 details.

## Commands

```bash
pipenv run pytest test/ -v           # Run tests (22 pass)
pipenv run ruff check src/ test/     # Lint (should pass)
pipenv run python app/playground.py  # Run app
```
