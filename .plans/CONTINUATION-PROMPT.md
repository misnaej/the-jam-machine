# Continuation Prompt

**Branch:** `refactor/split-embedding-decoder` (PR pending → merge to `main`)

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

- Phases 1-7 ✅ Complete
- Phase 8 (Split embedding/decoder.py) ✅ Complete
- All ruff lint checks pass ✅
- Tests: 22 pass

## What Phase 8 Did

- Split 470-line `embedding/decoder.py` into 2 focused modules + slim orchestrator:
  - `text_parsing.py` — `text_to_events`, `get_track_ids`, `piece_to_inst_events`, `get_bar_ids`
  - `event_processing.py` — `add_missing_timeshifts_in_bar`, `remove_unwanted_tokens`, `check_for_duplicated_events`, `aggregate_timeshifts`, `add_velocity`, `_add_timeshifts`
  - `decoder.py` (slimmed) — `TextDecoder` class: `__init__`, `decode`, `tokenize`, `get_midi`, `get_instruments_tuple`
- Converted 10 `@staticmethod` + 1 pseudo-instance method to module functions
- Renamed `add_missing_timeshifts_in_a_bar` → `add_missing_timeshifts_in_bar`
- Made `add_timeshifts` private (`_add_timeshifts`)
- Deleted `__main__` block (dead debug code)
- No caller changes needed

## Next Steps (from MASTER-PLAN)

1. **Phase 9**: Naming Fixes & Cleanup
2. **Phase 10**: Add Unit Tests
3. **Phase 11**: Genre Prediction Cleanup (Optional)

See `design-audit-implementation-plan.md` Phase 6 for detailed Phase 9 plan.

## Commands

```bash
pipenv run pytest test/ -v           # Run tests (22 pass)
pipenv run ruff check src/ test/     # Lint (should pass)
pipenv run python app/playground.py  # Run app
```
