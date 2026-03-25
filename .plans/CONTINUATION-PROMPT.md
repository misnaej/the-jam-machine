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
| `test-plan.md` | Unit test plan (3 PRs) |
| `design-audit-findings.md` | 43 design issues in 10 work packages |
| `github-pages.md` | GitHub Pages site plan |
| `ci-badges.md` | CI workflow and badges plan |
| `audit-genre-prediction.md` | Genre prediction cleanup (optional) |

## Current Status

- Phases 1–11 complete (refactoring, examples, hooks, Claude setup)
- Phase 13 in progress: unit tests — PR 1 of 3 merged (generating module)
- 51 tests passing, 59% coverage
- Next: PR 2 (utilities) or Phase 14 (design audit fixes)

## Commands

```bash
pipenv run pytest test/ -v           # Run tests (51 pass)
pipenv run ruff check src/ test/     # Lint
pipenv run python app/playground.py  # Run app
./scripts/run-tests.sh               # Tests + coverage + badges
```
