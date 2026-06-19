@FOUNDATION.md

# CLAUDE.md — The Jam Machine (repo rules)

Generic engineering rules (critical thinking, safety, mandatory delegation,
git/PR workflow, design principles, documentation/testing standards, logging,
continuation protocol, issue triage) live in `@FOUNDATION.md` above — the
single source of truth. This file holds **only** what is specific to The Jam
Machine.

## Project Overview

The Jam Machine is a generative AI music composition tool that creates MIDI
sequences using a GPT-2 model trained on ~5,000 MIDI songs. See
[README.md](README.md) for full project description and user documentation.

**Live Demo:** https://huggingface.co/spaces/JammyMachina/the-jam-machine-app

## Project Structure

```
src/jammy/                 # Main package (module: jammy)
├── app/                   # Gradio web interface
├── analysis/              # Model visualization tools
├── embedding/             # MIDI <-> text token encoding/decoding
├── generating/            # Music generation engine (GPT-2)
├── preprocessing/         # Data preprocessing and MIDI statistics
└── training/              # Model training pipelines

hf_space/                  # HuggingFace Space deployment files
examples/                  # Example scripts
test/                      # Test suite (singular — see note below)
scripts/                   # Build, test, deploy scripts
docs/                      # GitHub Pages site
.claude/                   # Claude Code config (agents, skills, hooks)
.plans/                    # Refactoring plans
```

## Environment Setup

**Prerequisites:** Python >= 3.11 and **FluidSynth** (system dependency):

```bash
brew install fluidsynth      # macOS
sudo apt install fluidsynth  # Linux
```

**Install (pipenv):**

```bash
pip install pipenv
pipenv sync --dev    # install Pipfile.lock verbatim (deps + dev tooling + forge-scripts)
pipenv shell
```

> **Use `pipenv sync`, not `pipenv install`.** The runtime deps are unpinned in
> `pyproject.toml`, so `pipenv install` / `pipenv lock` re-resolve them to the
> latest releases — which has broken the build before (e.g. transformers 5.12
> breaks `GPT2LMHeadModel`). `pipenv sync` installs the committed lock exactly.
> Only re-lock deliberately, and re-run the test suite when you do.
> `forge-scripts` is declared in the `Pipfile` (not the pyproject `ci` extra) so
> it locks without dragging the runtime deps along.

## pipenv + forge (important)

This repo uses **pipenv** (Option A of the forge migration). The forge CLIs
(`forge-precommit`, `verify-forge-*`, `install-forge-*`, etc.) live in the
pipenv virtualenv, **not** on the bare `PATH`. So:

- Run git **inside `pipenv shell`** so the pre-commit githook's bare
  `forge-precommit` call resolves, **or**
- Prefix every forge CLI with `pipenv run` (e.g. `pipenv run forge-precommit`).

A bare `forge-precommit` outside the venv will fail with "command not found".

## Repo-specific conventions

- **`from __future__ import annotations` in every Python file.** Enables
  postponed annotation evaluation (PEP 563): heavy deps can be imported under
  `TYPE_CHECKING` only, no quoted type hints, no circular-import pain.
- **Test directory is `test/` (singular).** Forge's canonical layout is
  `tests/` (plural) and accepts `test/` via back-compat. A rename is tracked
  separately — until then, all forge config / CI paths point at `test/`.

### Prefer functions over classes

Don't use classes when module-level functions suffice — Python modules are
already namespaces. (This elaborates FOUNDATION §7; not a separate rule.)

```python
# ❌ Over-engineered — class with only static methods
class MidiUtils:
    @staticmethod
    def transpose(notes: list[int], semitones: int) -> list[int]:
        return [n + semitones for n in notes]

# ✅ Pythonic — just a module function
def transpose(notes: list[int], semitones: int) -> list[int]:
    return [n + semitones for n in notes]
```

**Use classes when** you have per-instance state, an object lifecycle, multiple
configured instances, a protocol/interface to implement, or several functions
that repeatedly share the same arguments. **Use functions when** the work is a
stateless transformation (data in → data out) — if you'd write all
`@staticmethod`, make them functions.

## HuggingFace Space deployment

The live app is deployed to a HuggingFace Space (`JammyMachina/the-jam-machine-app`)
via the `sync-hf-space.yml` GitHub workflow; deployment files live in
`hf_space/`. Docker build (`docker.yml`) uses CPU-only PyTorch.

## Continuous integration

`.github/workflows/ci.yml` runs on push/PR to `main`. The quality gate is
delegated to the **forge pre-commit gate** (`pipenv run forge-precommit`) —
ruff, docstrings, pyrefly typecheck (advisory), pip-audit — configured in
`[tool.forge]`. CI adds only: a FOUNDATION drift check, an explicit ruff pass
for `examples/`+`hf_space/` (outside forge's source dirs), and the **test suite**
(`pipenv run pytest test/`). No standalone ruff/interrogate/bandit/mypy steps —
forge owns them (mypy is superseded by pyrefly).

> **Tests in CI are temporary** — kept on during the forge adoption to catch
> dependency-resolution regressions the static gates miss. Once the migration
> is complete, revisit: the suite is long and is otherwise run locally before
> pushing.

`.github/workflows/forge-upgrade.yml` re-syncs forge-scripts from the `@main`
channel on a weekly cron and opens a PR on any change (the version trigger).
`docker.yml` and `sync-hf-space.yml` are build/deploy, unrelated to test CI.

## Plan documents

Session-to-session continuation uses forge's protocol (FOUNDATION §10):
`.plan/CONTINUATION.md` — singular, **gitignored**, auto-appended by the forge
git hooks. This is the live "what was just done / what's next" log.

Longer-lived project planning lives in committed `.plans/` (plural):
- `.plans/MASTER-PLAN.md` — refactoring master plan: phase order, decision log.
- `.plans/ci-badges.md`, `.plans/dependency-tree.md` — reference notes.

> Mind the one-character difference: `.plan/` (gitignored, transient
> continuation log) vs `.plans/` (committed, durable plans).

## Claude Code skills & agents

Agents and skills come from the **forge plugin** (`forge@forge`); the bespoke
local ones predating forge have been removed. The canonical agent roster and
the mandatory-delegation workflow orders live in **FOUNDATION §3** — use the
`forge:*` agents and `/forge:*` skills from there; don't re-list them here.
Add a repo-specific **wrapper** (non-shadowing name, e.g. `design-checker-jam`)
only when jam-machine needs extra rules on top of a forge agent (FOUNDATION §16).

Jam-machine-specific note: run the (long) test suite locally before pushing —
`pipenv run pytest test/`. No forge skill bundles the full local check the way
the old `/check` did.

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `pipenv sync --dev` |
| Activate environment | `pipenv shell` |
| Run tests + coverage | `./scripts/run-tests.sh` |
| Run tests only | `pipenv run pytest test/` |
| Docstring coverage | `./scripts/docstring-coverage.sh` |
| Lint code | `pipenv run ruff check src/ test/` |
| Format code | `pipenv run ruff format src/ test/` |
| Type check | `pipenv run pyrefly check src test` (forge's checker; advisory) |
| Security audit | `pipenv run pip-audit` |
| Forge pre-commit (full gate) | `pipenv run forge-precommit` |
| Deploy HF Space | `./scripts/deploy-hf-space.sh` |
| Enable git hooks | `git config core.hooksPath .githooks` |
| Run Gradio app | `pipenv run python -m jammy.app.playground` |
| Run example | `pipenv run python examples/generate.py` |

### Reports and Logs

Forge writes each pre-commit check's output to `code_health/<check>.log`
(gitignored) — e.g. `ruff.log`, `typecheck.log`, `pip_audit.log`,
`docstring_verification.log`. Read these to see why the gate failed:

```bash
cat code_health/typecheck.log    # pyrefly findings
cat code_health/ruff.log         # lint/format output
```
