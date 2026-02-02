# Continuation Prompt

**Branch:** `refactor/rename-package-jammy` (ready to merge to `main`)

## Context

Refactoring The Jam Machine. Package renamed from `the_jam_machine` to `jammy`.

## Start Here

Read `.plans/MASTER-PLAN.md` - it's the central reference with ordered phases.

## Key Plans

| Plan | Purpose |
|------|---------|
| `MASTER-PLAN.md` | Order of operations (15 phases) |
| `design-audit-implementation-plan.md` | Detailed implementation steps |
| `test-coverage-audit.md` | Test improvements |

## Current Status

- Phase 1 (Postponed Annotations) ✅ Complete
- Phase 2 (Package Rename & Absolute Imports) ✅ Complete
- All ruff lint checks pass ✅
- Tests: 3 pass, 2 fail, 1 error (pre-existing issues)

## Next Steps (from MASTER-PLAN)

1. **Merge current branch** to `main`
2. **Phase 3**: Fix broken tests (rename helper functions, skip/delete broken tests)
3. **Phase 4**: Config dataclasses (PR #2 feedback)

## Commands

```bash
pipenv run pytest test/ -v           # Run tests
pipenv run ruff check src/ test/     # Lint (should pass)
pipenv run python app/playground.py  # Run app
```
