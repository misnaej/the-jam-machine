# Plan: Enable All Ruff Rules

**Date:** 2026-03-25
**Status:** Planned

---

## Goal

Switch from a curated ruleset to `select = ["ALL"]` with a targeted ignore list. This catches more issues (like `PLC0415` import-outside-toplevel) while suppressing rules that conflict with the project's style.

---

## Current State

18 rule groups enabled. Running `select = ["ALL"]` produces ~2,661 violations.

## Top violations with ALL enabled

| Rule | Count | Description | Action |
|------|-------|-------------|--------|
| `PLR2004` | 52 | Magic value in comparison | **Ignore** — token strings/numbers are expected |
| `ERA001` | 37 | Commented-out code | **Fix** — remove dead comments (overlaps with WP10) |
| `COM812` | 37 | Missing trailing comma | **Ignore** — conflicts with ruff formatter |
| `FBT001` | 27 | Boolean positional arg | **Ignore** — too strict for Gradio callbacks |
| `FBT002` | 25 | Boolean default arg | **Ignore** — same |
| `PLC0415` | 6 | Import not at top level | **Fix** — move imports to module level |
| `RET504` | 6 | Unnecessary assignment before return | **Fix** — trivial |
| `TRY003` | 5 | Long exception message | **Ignore** — descriptive errors are fine |
| `TD002/003` | 10 | TODO missing author/link | **Ignore** — simple TODOs are fine |
| `FIX002` | 5 | TODO found | **Ignore** — intentional |
| `INP001` | ~3 | Implicit namespace package | **Ignore** — `app/` and `examples/` are not packages |
| `ICN001` | 2 | Unconventional import alias | **Ignore** — `matplotlib` as `mpl` not enforced |
| `PD002` | 5 | Pandas inplace | **Fix** in preprocessing |
| `EM102` | 4 | Exception string formatting | **Fix** — use variables |
| `BLE001` | 3 | Blind except | **Fix** — overlaps with WP3 |
| `DTZ005` | 2 | Naive datetime | **Fix** — use timezone-aware |
| `A001` | 2 | Shadowing builtin | **Fix** |

## Proposed Config

```toml
select = ["ALL"]
ignore = [
    "COM812",  # trailing comma — conflicts with ruff formatter
    "ISC001",  # implicit string concat — conflicts with ruff formatter
    "PLR2004", # magic value comparison — expected with token strings
    "FBT001",  # boolean positional arg — too strict
    "FBT002",  # boolean default arg — too strict
    "TD002",   # TODO missing author
    "TD003",   # TODO missing issue link
    "FIX002",  # TODO found — intentional
    "INP001",  # implicit namespace package — app/ examples/ not packages
    "ICN001",  # unconventional import alias
    "TRY003",  # long exception message — descriptive errors are fine
]
```

## Steps

1. Switch to `select = ["ALL"]` with ignore list
2. Run `ruff check` — expect ~50-100 remaining fixable violations
3. Auto-fix what ruff can: `ruff check --fix`
4. Manually fix the rest (ERA001 commented code, BLE001 bare excepts)
5. Verify all tests pass
6. Update CLAUDE.md to document the ALL policy

## Overlap

- `ERA001` (commented-out code) overlaps with design audit WP10
- `BLE001` (bare except) overlaps with design audit WP3
- `PLC0415` (imports) — 6 occurrences, mostly in `get_event` and lazy imports

Consider doing this alongside or immediately after Phase 14 (design audit fixes).
