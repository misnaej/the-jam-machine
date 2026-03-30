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
| `ci-badges.md` | CI workflow and badges plan |
| `audit-genre-prediction.md` | Genre prediction cleanup (optional) |

## Current Status (2026-03-30)

- **Phases 1–14 complete** (refactoring, tests, docs, analysis, design audit)
- **149 tests passing, 68% coverage**
- **Ruff:** `select = ["ALL"]`, 2 global ignores (ISC001, COM812 — formatter conflicts)
- Next: Phase 15 (HuggingFace Space) or Phase 16 (Docker)

## Commands

```bash
pipenv run pytest test/ -v           # Run tests (149 pass)
pipenv run ruff check src/ test/     # Lint
pipenv run python app/playground.py  # Run app
./scripts/run-tests.sh               # Tests + coverage + badges
```
