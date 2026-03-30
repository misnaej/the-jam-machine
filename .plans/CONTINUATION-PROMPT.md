# Continuation Prompt

**Branch:** `main`

## Context

Refactoring The Jam Machine. Package: `jammy`.

## Start Here

Read `.plans/MASTER-PLAN.md` — the central reference with ordered phases.

## Active Plan Files

| Plan | Purpose |
|------|---------|
| `MASTER-PLAN.md` | Phase order, status, decisions |
| `design-audit-findings.md` | Remaining design issues (WP6, WP7, WP9, WP10) |
| `ci-badges.md` | CI workflow and badges plan |
| `audit-genre-prediction.md` | Genre prediction cleanup (optional) |

## Current Status (2026-03-27)

- **Phases 1–13 complete** (refactoring, examples, hooks, pages, analysis, tests)
- **Phase 14 in progress** — WP1-5, WP8 done; WP6-7, WP9-10 remaining
- **149 tests passing, 68% coverage**
- Next: Phase 14 remaining (DRY, idioms, testability, cleanup) or Phase 15 (HuggingFace Space)

## Commands

```bash
pipenv run pytest test/ -v           # Run tests (149 pass)
pipenv run ruff check src/ test/     # Lint
pipenv run python app/playground.py  # Run app
./scripts/run-tests.sh               # Tests + coverage + badges
```
