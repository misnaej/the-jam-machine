# CLAUDE.md - Development Guide for The Jam Machine

This file provides guidance for AI assistants and developers working on this codebase.

## Project Overview

The Jam Machine is a generative AI music composition tool that creates MIDI sequences using a GPT-2 model trained on ~5,000 MIDI songs. See [README.md](README.md) for full project description and user documentation.

**Live Demo:** https://huggingface.co/spaces/JammyMachina/the-jam-machine-app

## Project Structure

```
src/the_jam_machine/       # Main package
├── embedding/             # MIDI <-> text token encoding/decoding
├── generating/            # Music generation engine (GPT-2)
├── preprocessing/         # Model loading from HuggingFace
└── training/              # Model training pipelines

app/playground.py          # Gradio web interface
examples/                  # Example scripts
test/                      # Test suite
```

## Environment Setup

### Prerequisites

1. **Python >= 3.11**
2. **FluidSynth** (system dependency):
   ```bash
   # macOS
   brew install fluidsynth

   # Linux
   sudo apt install fluidsynth
   ```

### Installation

We use [pipenv](https://pypi.org/project/pipenv/) for dependency management.

```bash
# Install pipenv if not already installed
pip install pipenv

# Install dependencies (including dev/test dependencies)
pipenv install -e ".[ci]"

# Activate the virtual environment
pipenv shell
```

## Running Tests

```bash
# Run all tests
pipenv run pytest test/

# Run specific test
pipenv run pytest test/test_tosort.py::test_generate

# Run with coverage
pipenv run pytest test/ --cov=src/the_jam_machine
```

## Code Quality

### Linting with Ruff

We enforce code quality using [ruff](https://docs.astral.sh/ruff/).

```bash
# Check for issues
pipenv run ruff check src/ test/

# Auto-fix issues
pipenv run ruff check --fix src/ test/

# Format code
pipenv run ruff format src/ test/
```

---

## Development Principles

When contributing to this codebase, adhere to the following principles:

### SOLID Principles

- **S - Single Responsibility:** Each class/function should have one reason to change. Keep modules focused.
- **O - Open/Closed:** Code should be open for extension but closed for modification. Use abstractions.
- **L - Liskov Substitution:** Subtypes must be substitutable for their base types without breaking behavior.
- **I - Interface Segregation:** Prefer small, specific interfaces over large, general ones.
- **D - Dependency Inversion:** Depend on abstractions, not concretions. Use dependency injection where appropriate.

### DRY (Don't Repeat Yourself)

- Extract common logic into reusable functions or classes
- Use constants for magic numbers and repeated strings (see `constants.py`)
- If you copy-paste code, refactor it into a shared utility

### YAGNI (You Aren't Gonna Need It)

- Only implement features that are currently needed
- Avoid speculative generality and over-engineering
- Remove dead code; don't comment it out "for later"

### KISS (Keep It Simple, Stupid)

- Prefer simple, readable solutions over clever ones
- Break complex functions into smaller, well-named pieces
- If a solution feels complicated, step back and reconsider the approach

---

## Documentation Standards

### Docstrings

All public modules, classes, and functions **must** have docstrings following Google style:

```python
def encode_midi(midi_path: str, output_path: str | None = None) -> str:
    """Convert a MIDI file to text token representation.

    Args:
        midi_path: Path to the input MIDI file.
        output_path: Optional path to save the encoded text.
            If None, returns the string without saving.

    Returns:
        The text-encoded representation of the MIDI file.

    Raises:
        FileNotFoundError: If midi_path does not exist.
        ValueError: If the MIDI file is malformed or empty.

    Example:
        >>> encoded = encode_midi("song.mid")
        >>> print(encoded[:50])
        'PIECE_START TRACK_START INST=25 DENSITY=2 BAR_STA'
    """
```

### Type Hints

All function signatures **must** include type hints:

```python
# Good
def generate_piece(
    instruments: list[str],
    densities: list[int],
    temperatures: list[float],
    num_bars: int = 8,
) -> str:
    ...

# Bad - no type hints
def generate_piece(instruments, densities, temperatures, num_bars=8):
    ...
```

Use modern Python typing syntax (Python 3.10+):
- `list[str]` instead of `List[str]`
- `dict[str, int]` instead of `Dict[str, int]`
- `str | None` instead of `Optional[str]`
- `X | Y` instead of `Union[X, Y]`

Use postponed annotation evaluation to avoid quoted type hints:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel

class Generator:
    def __init__(self, model: GPT2LMHeadModel) -> None:  # No quotes needed
        self.model = model
```

- `from __future__ import annotations` makes all annotations strings at runtime (PEP 563)
- This allows importing heavy dependencies only for type checking, avoiding circular imports
- Without it, you'd need quotes: `model: "GPT2LMHeadModel"` - which is error-prone (typos not caught)
- Add this import to **all** Python files in the project

### Comments

- Write self-documenting code; use comments only when the "why" isn't obvious
- Keep comments up to date with code changes
- Use `TODO:` for planned improvements (include your name/date if long-term)
- Use `FIXME:` for known issues that need addressing

---

## Ruff Configuration

Add the following to `pyproject.toml` to enforce standards:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100
src = ["src", "test"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "PTH",    # flake8-use-pathlib
    "RUF",    # Ruff-specific rules
    "D",      # pydocstyle (docstrings)
    "ANN",    # flake8-annotations (type hints)
    "S",      # flake8-bandit (security)
    "N",      # pep8-naming
    "T20",    # flake8-print
]
ignore = [
    "D100",   # missing module docstring (can be noisy initially)
    "D104",   # missing package docstring
    "ANN101", # missing self type (redundant)
    "ANN102", # missing cls type (redundant)
]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.isort]
known-first-party = ["the_jam_machine"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

## Git Workflow

### Branch Strategy

- **Default Branch:** `main` (all feature branches are created from and merged into `main`)

### Development Workflow

1. **Create a feature branch from `main`:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

2. **Branch naming conventions:**
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `refactor/` - Code refactoring
   - `docs/` - Documentation changes
   - `test/` - Test additions/fixes

3. **Make changes and commit:**
   ```bash
   # Stage specific files (preferred over git add -A)
   git add src/the_jam_machine/file.py

   # Commit with descriptive message
   git commit -m "Add feature X to module Y"
   ```

4. **Push and create PR:**
   ```bash
   git push -u origin feature/your-feature-name
   gh pr create --base main --title "Add feature X" --body "Description..."
   ```

5. **PR Requirements:**
   - All tests must pass (`pipenv run pytest test/`)
   - Ruff checks must pass (`pipenv run ruff check src/ test/`)
   - Code must be formatted (`pipenv run ruff format src/ test/`)
   - PR description must explain changes

6. **After PR approval:**
   - Squash and merge into `main`
   - Delete the feature branch

### Git Hooks

Pre-commit hooks are configured in `.githooks/`. To enable:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/*
```

Or run `./scripts/setup-env.sh` which sets up hooks automatically.

The pre-commit hook runs:
- Ruff linting (auto-fixes when possible)
- Ruff formatting (auto-applies)
- pip-audit security scan (informational)

**Important:**
- **Never use `--no-verify`** to skip hooks unless explicitly requested by the user
- Hooks exist to maintain code quality; work with them, not around them

### Pre-Work Lint Check Strategy

Before modifying files, check for pre-existing lint issues that would block commits:

```bash
# Check files you plan to modify
pipenv run ruff check src/the_jam_machine/path/to/files/

# If many issues exist, fix them first
pipenv run ruff check --fix src/the_jam_machine/path/to/files/
pipenv run ruff format src/the_jam_machine/path/to/files/
```

**Workflow for files with many pre-existing issues:**
1. Fix lint issues in a separate "cleanup" commit/PR first
2. Merge the cleanup PR
3. Then create a new PR for the actual feature/refactor work

This keeps PRs focused and makes code review easier.

### Commit and PR Style

- **No AI attribution**: Do not add "Generated with Claude Code", "Co-Authored-By: Claude", or similar AI authorship markers to commits or PRs
- Keep commit messages concise and focused on the "why"
- **Squash and merge title**: Max 100 characters
- PR descriptions should explain changes clearly without boilerplate

---

## AI Session Management

When working on multi-phase refactoring or long tasks:

### Plan Documents

- **Master plan:** `plans/MASTER-PLAN.md` is the central reference for all refactoring work
- **Update progress:** Mark phases as complete (✅) and update the "Current State" table
- **Decision log:** Record important decisions with rationale in the plan's Decision Log section

### Context Preservation

Before context gets auto-compacted (or when clearing context with `/clear`):

1. **Update the plan document** with current progress and any new findings
2. **Write a continuation prompt** at the end of the plan summarizing:
   - What was just completed
   - What to do next
   - Any blockers or decisions needed

Example continuation prompt format:
```markdown
## Continuation Prompt

**Last completed:** Phase 1 - Added postponed annotations to all files
**Next step:** Phase 2 - Fix broken tests (see Tasks section)
**Notes:** Found 2 additional files needing updates in examples/
```

This ensures work can resume smoothly after context resets.

---

## Quick Reference

| Task | Command |
|------|---------|
| Setup environment | `./scripts/setup-env.sh` |
| Install dependencies | `pipenv install -e ".[ci]"` |
| Activate environment | `pipenv shell` |
| Run tests | `pipenv run pytest test/` |
| Lint code | `pipenv run ruff check src/ test/` |
| Format code | `pipenv run ruff format src/ test/` |
| Security audit | `pipenv run pip-audit` |
| Enable git hooks | `git config core.hooksPath .githooks` |
| Run Gradio app | `pipenv run python app/playground.py` |
| Run example | `pipenv run python examples/generation_playground.py` |
