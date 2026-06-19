# Migration plan — adopt forge in `misnaej/the-jam-machine`

> Copy this file into the jam-machine repo root and execute the phases in
> order from there. Each phase is independently committable and reversible.
> Branch off `main`; do not push to `main` directly.

## Context (read first)

jam-machine is forge's **ancestor**: it hand-copied the conventions forge
later packaged, so it *looks* like a forge consumer but consumes **nothing**
from the forge package or plugin. This is a migration from bespoke
forge-likes → the real forge, in two install channels that are easy to
conflate:

| Channel | Ships | Installed via | Provides |
|---|---|---|---|
| **pip package** `forge-scripts` | CLIs + githooks + generated docs | `pip`/`pipenv` + `install-forge-*` | `forge-precommit`, `verify-forge-*`, `install-forge-*`, `FOUNDATION.md`, githooks |
| **Claude Code plugin** `forge@forge` | agents + skills + claude-hooks | `/plugin` in Claude Code | `forge:design-checker`, `/forge:commit`, `block_*` hooks |

You must adopt **both**. Phases 1–6 = pip side. Phase 7 = plugin side.
Phase 8 = the version-trigger wiring (the whole point). Phase 9 = verify.

### Current jam-machine state (ground truth, 2026-06)
- Package `the-jam-machine`, module `jammy`, layout `src/jammy/`.
- Test dir **`test/`** (singular). Forge accepts it (back-compat); canonical
  is `tests/`. Rename deferred to optional Phase 10.
- **pipenv** (`Pipfile`/`Pipfile.lock`); extras `ci` + `notebooks` in
  pyproject. Manual `version = "0.1.0"`.
- Ruff config inlined as `[tool.ruff*]` in `pyproject.toml` (`select=["ALL"]`,
  line-length 100, ignore ISC001/COM812). Forge wants a single root
  `ruff.toml` (FOUNDATION §5).
- `[tool.interrogate] fail-under = 95`, `[tool.bandit]`, `[tool.mypy]`,
  `[tool.pytest.ini_options]` all inline — these forge reads as-is, keep them.
- Bespoke `.githooks/pre-commit` (pipenv ruff/interrogate/bandit/pip-audit +
  curl badges) → replaced by forge's githook calling `forge-precommit`.
- Bespoke agents `.claude/agents/`: `design_agent`, `git_agent`,
  `pr_review_agent`, `test_agent`, `documentation_agent`.
- Bespoke skills `.claude/skills/`: `check commit lint next pr review`.
- Hand-rolled `CLAUDE.md` (Critical-Thinking text inlined; no `@FOUNDATION.md`).
- CI `.github/workflows/ci.yml` runs raw `ruff/interrogate/bandit/mypy/pytest`
  via pipenv; also `docker.yml`, `sync-hf-space.yml` (leave those alone).

### The pipenv ↔ PATH gotcha (decide before Phase 4)
Forge's githook and CI call **bare** `forge-precommit` / `verify-forge-*` —
they expect the CLIs on `PATH`. Under pipenv the CLIs live in the pipenv
venv and a bare call fails outside `pipenv shell`. **Decide now:**

- **Option A (lowest churn): keep pipenv.** Developers run git inside
  `pipenv shell`, and CI prefixes `pipenv run`. The forge githook wrapper
  calls bare `forge-precommit`, so for local commits the venv must be active.
  Document in CLAUDE.md repo rules.
- **Option B (cleanest forge fit): migrate to pip + venv.** Drop Pipfile,
  add a `dev` extra, `python -m venv .venv && pip install -e ".[dev]"`.
  Bare CLI calls then work in an activated venv exactly as forge assumes.

**Recommended: Option B** — forge's whole CLI-on-PATH contract (FOUNDATION
§2 "fail loudly when the CLI is missing") assumes a plain venv; pipenv adds a
`pipenv run` prefix to every forge invocation forever. This plan writes
commands for **Option B**; if you keep pipenv, prefix forge CLIs with
`pipenv run` and skip the Pipfile-removal steps.

---

## Phase 0 — Prep & safety net

**Goal:** clean baseline, escape hatch.

```bash
git clone git@github.com:misnaej/the-jam-machine.git
cd the-jam-machine
git checkout -b chore/adopt-forge

# Snapshot the pre-migration state for rollback / diffing.
git tag pre-forge-migration

# Confirm current CI passes locally BEFORE changing anything.
pipenv install -e ".[ci]"
pipenv run ruff check src/ test/ examples/ hf_space/
pipenv run pytest test/ -q
```

**Verify:** existing checks green. If red now, fix or note before migrating —
don't migrate onto a broken baseline (FOUNDATION §1).
**Rollback:** `git checkout main && git branch -D chore/adopt-forge`.

---

## Phase 1 — Add the `forge-scripts` dependency (pip side)

**Goal:** forge CLIs available; pick the channel that drives the test-bed.

For the test-bed, pin the **fast channel** so every forge patch + minor
reaches jam-machine:

```toml
# pyproject.toml
[project.optional-dependencies]
# Option B: rename/extend a dev extra (keep `ci` too if other tools use it)
dev = [
    "forge-scripts @ git+https://github.com/misnaej/forge.git@dev",
    "ruff", "pytest", "pytest-cov", "pytest-html",
    "pip-audit", "bandit", "interrogate", "mypy",
]
```

```bash
# Option B
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Verify the CLIs are on PATH (fail loudly if not — FOUNDATION §2):
forge-doctor || true        # self-skips in CI; prints install report locally
forge-precommit --help
install-forge-bootstrap --help
```

**Verify:** all three commands resolve. `forge-doctor` reports gh auth +
(absent) plugin.
**Gotcha:** `git+...@dev` is cached by pip per `(name, version)`; later
refreshes need `forge-upgrade --apply` (Phase 8), not bare `pip install`.
**Rollback:** remove the line, reinstall.
**Commit:** `chore: add forge-scripts dev dependency (@dev channel)`.

---

## Phase 2 — FOUNDATION + CLAUDE.md reconcile

**Goal:** replace hand-copied foundation prose with the real `@FOUNDATION.md`
include; preserve jam-machine-specific guidance.

```bash
install-forge-claude-md     # writes FOUNDATION.md + scaffolds CLAUDE.md
```

This writes `FOUNDATION.md` (managed, do not hand-edit) and, on first run,
a `CLAUDE.md` scaffold beginning with `@FOUNDATION.md`. Because jam-machine
already has a rich `CLAUDE.md`, reconcile by hand:

1. **Keep** the new scaffold's `@FOUNDATION.md` line at the top.
2. **Delete** from the old CLAUDE.md everything now owned by FOUNDATION:
   Critical Thinking Directive, generic safety rules, generic git/PR
   workflow, generic design principles — all duplicated, FOUNDATION wins
   (FOUNDATION §12 single source of truth).
3. **Move** genuinely jam-machine-specific content below the include as repo
   rules: Project Overview, the GPT-2/MIDI architecture notes, HF Space deploy
   flow, `jammy` module map, the `test/`-not-`tests/` note, and (if you kept
   pipenv) the "run git inside `pipenv shell`" rule.

```bash
install-forge-claude-md --check   # confirm FOUNDATION.md has no drift
```

**Verify:** `CLAUDE.md` opens with `@FOUNDATION.md`; no duplicated foundation
prose; jam-machine specifics retained.
**Rollback:** `git checkout main -- CLAUDE.md && git rm FOUNDATION.md`.
**Commit:** `docs: adopt forge FOUNDATION.md, slim CLAUDE.md to repo rules`.

---

## Phase 3 — Single root `ruff.toml`

**Goal:** comply with FOUNDATION §5 (one `ruff.toml` at root; no
`[tool.ruff]` in pyproject).

1. Create `ruff.toml` at repo root, port the existing block verbatim, add the
   forge isort convention:

```toml
# ruff.toml
target-version = "py311"
line-length = 100
src = ["src", "test"]

[lint]
select = ["ALL"]
ignore = ["ISC001", "COM812"]   # formatter conflicts (unchanged)

[lint.per-file-ignores]
"test/**/*.py" = ["S101", "PLR2004"]
"src/jammy/app/**/*.py" = ["PLR0913"]
"examples/**/*.py" = ["INP001"]
"hf_space/**/*.py" = ["INP001"]

[lint.pydocstyle]
convention = "google"

[lint.isort]
known-first-party = ["jammy"]
lines-after-imports = 2          # forge convention (new)

[format]
quote-style = "double"
indent-style = "space"
```

2. **Delete** all `[tool.ruff*]` tables from `pyproject.toml`. Leave
   `[tool.bandit]`, `[tool.interrogate]`, `[tool.mypy]`,
   `[tool.pytest.ini_options]` — forge reads those in place.

**Verify:** `ruff check src/` uses the new config (note: `lines-after-imports
= 2` may surface new diffs — fix via Phase 4's fixer, don't suppress).
**Gotcha:** ruff prefers `ruff.toml` over pyproject when both exist; deleting
the pyproject tables avoids silent split-brain config.
**Rollback:** `git checkout main -- pyproject.toml && git rm ruff.toml`.
**Commit:** `refactor: move ruff config to root ruff.toml (FOUNDATION §5)`.

---

## Phase 4 — Swap githooks to forge's

**Goal:** bespoke `.githooks/pre-commit` → forge githook calling
`forge-precommit`.

```bash
install-forge-githooks --refresh   # writes forge pre/post hooks + sidecar
```

This installs forge's version-free hook wrappers and the gitignored
`.githooks/.forge-hook-version` sidecar, and points `core.hooksPath` at
`.githooks`. Then:

1. **Delete** the bespoke pieces now superseded: the old
   `.githooks/pre-commit` body (forge overwrote it — confirm via `git diff`),
   `scripts/docstring-coverage.sh` if only the old hook used it, the curl
   badge logic. Keep `.githooks/badges/` only if you still want badges
   (forge has its own coverage badge via `[tool.forge.docstring_coverage]`).
2. Run the real gate and clear every violation **via the fixer agent — never
   hand-fix or `--no-verify`** (FOUNDATION §2, §4):

```bash
forge-precommit            # generates code_health/*.log
```

Then in Claude Code: invoke `forge:precommit-fixer` to clear all blocking
failures (it reads `code_health/`, dispatches ruff/docstring/naming fixes).

**Verify:** `forge-precommit` exits 0. `code_health/` logs present.
**Gotcha (pipenv):** if you kept Option A, the hook's bare `forge-precommit`
needs an active `pipenv shell`; document it or switch to Option B.
**Gotcha:** forge's `cli_wiring` / `manifest_json` steps self-skip in repos
that don't ship a plugin — jam-machine doesn't, so expect them skipped.
**Rollback:** `git checkout main -- .githooks scripts && git config --unset core.hooksPath`.
**Commit:** `chore: replace bespoke pre-commit with forge githooks`.

---

## Phase 5 — CI workflow → forge recipe

**Goal:** `ci.yml` runs `forge-precommit` instead of raw tools; add the
scheduled upgrade workflow. Base on `forge/docs/ci-recipe.md`.

Rewrite `.github/workflows/ci.yml` (keep the libfluidsynth system dep):

```yaml
name: CI
on:
  push: { branches: [main] }
  pull_request:

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }

      - name: System deps
        run: sudo apt-get update && sudo apt-get install -y --no-install-recommends libfluidsynth3

      - name: Install project + forge-scripts
        run: pip install -e ".[dev]"

      - name: Bootstrap forge artifacts (idempotent)
        run: install-forge-bootstrap

      - name: Verify no drift
        run: install-forge-bootstrap --check

      - name: forge pre-commit
        run: forge-precommit

      - name: Tests
        run: pytest test/ -q --durations=25 --durations-min=1.0 | tee code_health/pytest.log

      - name: Slow tests report
        if: always()
        run: forge-slow-tests-report --log code_health/pytest.log --out code_health/slow_tests.log
```

Add `.github/workflows/forge-upgrade.yml` — copy verbatim from
`forge/docs/ci-recipe.md` §3 (scheduled `forge-upgrade --apply` → opens a PR
on every new forge version). **This is the version trigger (Phase 8).**

**Verify:** push branch; CI green. `doctor`/`audit-deps` self-skip in CI.
**Gotcha:** `install-forge-bootstrap --check` fails on drift — that's the
point; it refuses merges with out-of-sync generated content.
**Rollback:** `git checkout main -- .github/workflows/ci.yml`.
**Commit:** `ci: run forge-precommit + bootstrap drift check; add forge-upgrade`.

---

## Phase 6 — Labels

**Goal:** install the canonical forge label schema (FOUNDATION §14).

```bash
install-forge-labels       # creates any missing tier/state/type/surface labels
```

**Verify:** `gh label list` shows `tier-1-critical` … `quick-win` etc.
jam-machine's existing labels are untouched (additive).
**Commit:** none (mutates GitHub, not the tree) — note it in the PR body.

---

## Phase 7 — Claude Code plugin (agents / skills / hooks)

**Goal:** replace bespoke agents/skills with forge's; remove shadowing.

In Claude Code (not shell):

```
/plugin marketplace add misnaej/forge
/plugin install forge@forge
/reload-plugins
```

Then in the repo tree:

1. **Delete** bespoke files now provided by the plugin:
   - `.claude/agents/{design_agent,git_agent,pr_review_agent,test_agent,documentation_agent}.md`
     → superseded by `forge:design-checker`, `forge:git-commit-push`,
     `forge:pr-manager`, `forge:test-advisor`/`forge:test-writer`,
     `forge:docs-types-checker`.
   - `.claude/skills/{check,commit,lint,next,pr,review}/` → superseded by
     `/forge:fix`, `/forge:commit`, `/forge:next`, `/forge:pr`, `/forge:review`.
2. **Keep-as-wrapper** any genuinely jam-machine-specific agent logic worth
   preserving — rename to a **non-shadowing** name (FOUNDATION §3/§16), e.g.
   `.claude/agents/design-checker-jam.md` that delegates via
   `Task(subagent_type="forge:design-checker", prompt="<jam extras>...")`.
   **Never** name a local file `design-checker.md` — it shadows the plugin
   and makes `forge:design-checker` unreachable.
3. Consumer Claude-hooks (if any kept) live under `.claude/hooks/` and must be
   registered in `.claude/settings.json` with `${CLAUDE_PROJECT_DIR}/...`
   absolute paths (FOUNDATION §11), never relative.

**Verify:** `/forge:commit` and `forge:design-checker` resolve (no "Agent
type not found"); no local file shadows a `forge:` name.
**Gotcha:** plugin cache is per-session — after install run `/reload-plugins`;
for monitor changes restart the session.
**Rollback:** restore deleted files from `pre-forge-migration` tag.
**Commit:** `chore: adopt forge plugin agents/skills, drop bespoke shadows`.

---

## Phase 8 — Version-trigger wiring (the point)

**Goal:** every forge release exercises jam-machine automatically.

1. **Channel pin** (done Phase 1): `forge-scripts @ ...@dev` = every patch +
   minor reaches jam-machine.
2. **Scheduled upgrade PR** (done Phase 5): `forge-upgrade.yml` runs
   `forge-upgrade --apply` on a cron; opens a PR whenever the new forge
   version changes generated content. That PR's `pull_request` event fires
   the Phase-5 CI → **Layer 1 signal** (bootstrap/precommit/CLIs/githooks)
   per forge release.
3. **Layer 2 (agents/skills, needs Claude)** — schedule a Claude run against
   the upgrade PR branch that exercises the agent surface and comments
   pass/fail. Use forge's `/schedule` (cloud routine) or a local `/loop`:
   - `forge:design-checker` + `forge:security-checker` + `forge:docs-types-checker` on a seeded diff
   - `forge:precommit-fixer` clears a seeded violation
   - `/forge:pr` drives a throwaway PR (squash msg via `forge-pr-squash-comment`)
   - `forge:issue-triage` bootstrap + Backlog Index build
4. **Red on either layer = a forge release broke a consumer.** Investigate
   before it reaches real downstreams (FOUNDATION §1).

**Verify:** trigger `forge-upgrade.yml` via `workflow_dispatch`; confirm it
opens a PR and CI runs on it.
**Commit:** captured in Phase 5; Layer 2 schedule config as applicable.

---

## Phase 9 — Verify & cut over

**Goal:** prove the full forge surface works end-to-end, then merge.

```bash
forge-precommit                 # green
install-forge-bootstrap --check # no drift
pytest test/ -q                 # tests green
```

In Claude Code, smoke the surface once manually:
- `/forge:commit` on a trivial change → `forge:precommit-fixer` +
  `forge:git-commit-push` run clean.
- `/forge:pr` → `forge:pr-manager` produces a valid squash message.
- `forge:issue-triage` (bootstrap) → `📋 Backlog Index` issue created.

Open the adoption PR (`chore/adopt-forge` → `main`) via `/forge:pr`. **Do not
self-merge** (FOUNDATION §2) — you merge it yourself with `! gh pr merge`.

**Definition of done:** jam-machine consumes forge-scripts (pip) + forge
plugin (Claude Code); CI runs forge-precommit + drift check; `forge-upgrade`
cron is live; bespoke duplicates removed; no shadowing names.

---

## Phase 10 — `test/` → `tests/` (optional, deferred)

Canonical forge layout is `tests/` (plural). Defer until the core migration
is merged and green — it touches `testpaths`, CI paths, ruff `src`, and any
`from test...` imports. Do as a separate focused PR:

```bash
git mv test tests
# update: pyproject [tool.pytest] testpaths, ruff.toml src=["src","tests"],
#         per-file-ignores "tests/**", ci.yml pytest path, any test imports
forge-precommit && pytest tests/ -q
```

---

## Rollback (whole migration)

```bash
git checkout main
git branch -D chore/adopt-forge      # discard branch
# or reset a partial branch to the snapshot:
git reset --hard pre-forge-migration
```

GitHub labels added in Phase 6 are additive and harmless; remove manually if
desired. Plugin install (Phase 7) is per-machine, not in the repo.

---

## Open decisions to make before starting
1. **pipenv vs pip+venv** (Option A/B above) — recommend B.
2. **Layer 2 cadence/host** — cloud `/schedule` vs local `/loop`; cost.
3. **`test/` rename** now (Phase 10) or later — recommend later.
4. **Single consumer vs matrix** — add a minimal synthetic repo later to
   separate "real-repo noise" from "clean-contract" signal (tracked in the
   issue, not this plan).
