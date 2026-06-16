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
pipenv install -e ".[ci]"    # includes dev/test tooling + forge-scripts
pipenv shell
```

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

## Plan documents

Long / multi-phase work is tracked in `.plans/`:

- `.plans/MASTER-PLAN.md` — central reference: current state, phase order,
  decision log. Mark phases complete (✅); record decisions with rationale.
- `.plans/CONTINUATION-PROMPT.md` — current branch + purpose, what was just
  done, what's next (with file/function references), blockers/open questions.
  Update after every significant action, not just at session end.

> Note: FOUNDATION §10 also defines a continuation protocol at
> `.plan/CONTINUATION.md` (singular, gitignored). This repo predates it and
> uses the committed `.plans/` docs above; reconcile if/when convenient.

## Claude Code skills & agents

> Migration note: these are the **bespoke** agents/skills predating forge.
> They are being replaced by the forge plugin's `forge:*` agents and
> `/forge:*` skills. Until that phase lands, the local ones below apply.

| Skill | What it does |
|-------|-------------|
| `/check` | Run tests + lint + format |
| `/lint` | Run ruff check + format |
| `/commit` | Lint, commit, and push to current branch |
| `/review` | design-reviewer + docs-reviewer agents in parallel |
| `/pr` | pr-reviewer agent → squash merge message |
| `/next` | Sync main, clean stale branches, start next task |

| Agent | Use for |
|-------|---------|
| `design-reviewer` | SOLID, DRY, YAGNI, KISS checks |
| `docs-reviewer` | Docstrings, type hints, comments |
| `test-writer` | Write tests + review test quality |
| `pr-reviewer` | PR wrap-up + squash merge message |
| `git-workflow` | Git operations |

## Quick Reference

| Task | Command |
|------|---------|
| Install dependencies | `pipenv install -e ".[ci]"` |
| Activate environment | `pipenv shell` |
| Run tests + coverage | `./scripts/run-tests.sh` |
| Run tests only | `pipenv run pytest test/` |
| Docstring coverage | `./scripts/docstring-coverage.sh` |
| Lint code | `pipenv run ruff check src/ test/` |
| Format code | `pipenv run ruff format src/ test/` |
| Type check | `pipenv run mypy src/jammy/` |
| Security audit | `pipenv run pip-audit` |
| Forge pre-commit | `pipenv run forge-precommit` |
| Deploy HF Space | `./scripts/deploy-hf-space.sh` |
| Enable git hooks | `git config core.hooksPath .githooks` |
| Run Gradio app | `pipenv run python -m jammy.app.playground` |
| Run example | `pipenv run python examples/generate.py` |

### Reports and Logs

| Report | Location |
|--------|----------|
| Pre-commit hook logs | `.githooks/logs/latest.log` |
| Test coverage (HTML) | `output/reports/coverage/index.html` |
| Docstring coverage | `output/reports/docstring-coverage.txt` |
| Badges (SVG) | `.githooks/badges/` |

**If a pre-commit hook fails**, read the log:
```bash
cat .githooks/logs/latest.log
```
