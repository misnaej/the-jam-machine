# Continuation Prompt

**Branch:** `refactor/split-generating-utils` (PR pending → merge to `main`)

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
- Phase 5 (Token & Constant Consolidation) ✅ Complete (PR #8)
- Phase 5.5 (Track Builder Review Findings) ✅ Complete (PR #8)
- Phase 6 (Split generating/utils.py) ✅ Complete
- All ruff lint checks pass ✅
- Tests: 22 pass

## What Phase 6 Did

- Split `generating/utils.py` into 3 focused modules:
  - `file_io.py` — `write_text_midi_to_file()`, `define_generation_dir()`
  - `validation.py` — `bar_count_check()`, `check_if_prompt_inst_in_tokenizer_vocab()`, `forcing_bar_count()`, `_print_inst_classes()`
  - `visualization.py` — `plot_piano_roll()`, matplotlib config
- Replaced `WriteTextMidiToFile` class with `write_text_midi_to_file()` function (no shared state)
- Deleted `get_max_time()` (YAGNI — unused)
- Made `print_inst_classes()` private (`_print_inst_classes`)
- Updated 5 callers: `generate.py`, `playground.py`, `test_generate.py`, `generation_playground.py`, `test_decoder.py`
- Deleted `utils.py`

## Next Steps (from MASTER-PLAN)

1. **Phase 7**: Split `embedding/encoder.py`
2. **Phase 8**: Split `embedding/decoder.py`
3. **Phase 9**: Naming Fixes & Cleanup

See `design-audit-implementation-plan.md` Phase 4 for detailed Phase 7 plan.

## Commands

```bash
pipenv run pytest test/ -v           # Run tests (22 pass)
pipenv run ruff check src/ test/     # Lint (should pass)
pipenv run python app/playground.py  # Run app
```
