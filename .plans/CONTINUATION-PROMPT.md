# Continuation Prompt

**Branch:** `main` (all work merges to `main`)

## Context

Refactoring The Jam Machine. Major cleanup of lint issues and documentation completed.

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
- All ruff lint issues fixed ✅
- Custom agents configured in `agents/`
- App runs successfully

## Next Steps (from MASTER-PLAN)

1. Phase 2: Enforce absolute imports & rename package to `jammy`
2. Phase 3: Fix broken tests
3. Phase 4: Config dataclasses (PR #2 feedback)

## Commands

```bash
pipenv run pytest test/ -v           # Run tests
pipenv run ruff check src/ test/     # Lint (should pass)
pipenv run python app/playground.py  # Run app
```
