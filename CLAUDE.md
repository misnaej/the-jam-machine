# CLAUDE.md - Development Guide for The Jam Machine

This file provides guidance for AI assistants and developers working on this codebase.

## Project Overview

The Jam Machine is a generative AI music composition tool that creates MIDI sequences using a GPT-2 model trained on ~5,000 MIDI songs. See [README.md](README.md) for full project description and user documentation.

**Live Demo:** https://huggingface.co/spaces/JammyMachina/the-jam-machine-app

---

## CRITICAL: Use Custom Agents

Custom agents are defined in `agents/` (symlinked to `.claude/agents/`). **You MUST use these agents for their designated tasks:**

| Agent | Name | Use For |
|-------|------|---------|
| `pr_review_agent.md` | `pr-reviewer` | **PR wrap-up**: Review changes, check design/docs, generate squash merge message |
| `design_agent.md` | `design-reviewer` | **Design review**: Check code against SOLID, DRY, YAGNI, KISS principles |
| `documentation_agent.md` | `docs-reviewer` | **Documentation review**: Check docstrings, type hints, comments |

**When to use:**
- **Before merging any PR** → Run `pr-reviewer`
- **After ANY code change** → Run `docs-reviewer` (MANDATORY - docs must match code)
- **After writing new code** → Run `design-reviewer`
- **During code review** → Run both design and docs reviewers

**Why agents are critical:**
- They follow systematic checklists and don't skip steps
- They produce structured, consistent output
- They maintain dedicated context for the task
- They catch issues that ad-hoc reviews miss

---

## Project Structure

```
src/jammy/                 # Main package
├── embedding/             # MIDI <-> text token encoding/decoding
├── generating/            # Music generation engine (GPT-2)
├── preprocessing/         # Model loading from HuggingFace
└── training/              # Model training pipelines

app/playground.py          # Gradio web interface
examples/                  # Example scripts
test/                      # Test suite
agents/                    # Custom agent definitions
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

---

## Code Quality

We enforce code quality using [ruff](https://docs.astral.sh/ruff/). Configuration is in `pyproject.toml`.

```bash
# Check for issues
pipenv run ruff check src/ test/

# Auto-fix issues
pipenv run ruff check --fix src/ test/

# Format code
pipenv run ruff format src/ test/
```

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

### Prefer Functions Over Classes

Don't use classes when module-level functions suffice. Python modules are already namespaces.

```python
# ❌ Over-engineered - class with only static methods
class MidiUtils:
    @staticmethod
    def transpose(notes: list[int], semitones: int) -> list[int]:
        return [n + semitones for n in notes]

    @staticmethod
    def reverse(notes: list[int]) -> list[int]:
        return notes[::-1]

# ✅ Pythonic - just use module functions
# midi_utils.py
def transpose(notes: list[int], semitones: int) -> list[int]:
    return [n + semitones for n in notes]

def reverse(notes: list[int]) -> list[int]:
    return notes[::-1]
```

**Use classes when:**
- You have instance state (attributes that vary per instance)
- Objects have a lifecycle (init, configure, use, cleanup)
- You need multiple instances with different configurations
- Implementing a protocol or interface
- Multiple functions share the same arguments repeatedly (a sign they belong together)
- Modeling real-world entities with both data and behavior

**Use functions when:**
- No shared state is needed
- Operations are stateless transformations (data in → data out)
- You'd end up with all `@staticmethod` or `@classmethod`
- The logic is action-driven rather than object-driven
- You want easier testing (pure functions need minimal setup/mocking)

**Heuristic:** If you find yourself passing the same arguments to multiple functions, consider whether a class would group them better. But if those functions don't share state between calls, keep them as functions.

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

## Git Workflow

### Branch Strategy

- **Default Branch:** `main` (all feature branches are created from and merged into `main`)

### Development Workflow

1. **Plan the work:**
   - For non-trivial tasks, enter plan mode to explore the codebase and design an approach
   - Update `.plans/CONTINUATION-PROMPT.md` with the planned work
   - Get user approval before implementing

2. **Create a feature branch from `main`:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/your-feature-name
   ```

   **Branch naming conventions:**
   - `feature/` - New features
   - `fix/` - Bug fixes
   - `refactor/` - Code refactoring
   - `docs/` - Documentation changes
   - `test/` - Test additions/fixes

3. **Make changes:**
   - Write code following the standards in this document
   - Keep documentation updated (docstrings, type hints, comments)
   - Update `.plans/CONTINUATION-PROMPT.md` after completing each task
   - Run `docs-reviewer` agent after code changes to verify documentation

4. **Verify before commit:**
   ```bash
   # Run tests
   pipenv run pytest test/ -v

   # Run linter (auto-fixes where possible)
   pipenv run ruff check src/ test/ --fix
   pipenv run ruff format src/ test/

   # Stage specific files (preferred over git add -A)
   git add src/jammy/file.py

   # Commit with descriptive message
   git commit -m "Add feature X to module Y"
   ```

5. **Push and create PR:**
   ```bash
   git push -u origin feature/your-feature-name
   gh pr create --base main --title "Add feature X" --body "Description..."
   ```

6. **Before merging - run PR wrap-up:**
   - Run the `pr-reviewer` agent to review changes and generate squash merge message
   - This checks design, documentation, and creates a proper commit message

7. **PR Requirements (verified by pr-reviewer):**
   - All tests must pass (`pipenv run pytest test/`)
   - Ruff checks must pass (`pipenv run ruff check src/ test/`)
   - Code must be formatted (`pipenv run ruff format src/ test/`)
   - PR description must explain changes

8. **After PR approval:**
   - Squash and merge into `main` using the generated commit message
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

### Commit and PR Style

- **No AI attribution**: Do not add "Generated with Claude Code", "Co-Authored-By: Claude", or similar AI authorship markers to commits or PRs
- Keep commit messages concise and focused on the "why"
- **Squash and merge title**: Max 100 characters
- PR descriptions should explain changes clearly without boilerplate

---

## AI Session Management

When working on multi-phase refactoring or long tasks:

### Plan Mode Workflow

**CRITICAL: When entering plan mode, always follow these steps:**

1. **Read essential context files first:**
   - `CLAUDE.md` - coding standards, docstrings, type hints, naming conventions
   - `.plans/MASTER-PLAN.md` - current state, phase order, decision log
   - `.plans/CONTINUATION-PROMPT.md` - what was last completed, what's next

2. **Read task-specific plans if referenced** (e.g., `design-audit-implementation-plan.md`, `test-coverage-audit.md`)

3. **Include a Pre-Implementation Checklist in your plan:**
   ```markdown
   ## Pre-Implementation Checklist

   - [ ] Read `CLAUDE.md` for coding standards
   - [ ] Read `.plans/MASTER-PLAN.md` for context
   - [ ] Read relevant sub-plans
   ```

4. **Include Workflow Requirements in your plan:**
   ```markdown
   ## Workflow Requirements

   After each step:
   1. Update `.plans/CONTINUATION-PROMPT.md` with progress

   After phase complete:
   1. Update `.plans/MASTER-PLAN.md`
   2. Run `docs-reviewer` agent on changed files
   ```

5. **Include a Post-Implementation Tasks section:**
   ```markdown
   ## Post-Implementation Tasks

   1. Update MASTER-PLAN.md
   2. Update CONTINUATION-PROMPT.md
   3. Run agents (docs-reviewer, design-reviewer)
   4. Commit with descriptive message
   ```

**Why this matters:** Plans are often executed across multiple sessions. Including these workflow requirements ensures consistent execution regardless of who (or which session) implements them.

### Plan Documents

- **Master plan:** `.plans/MASTER-PLAN.md` is the central reference for all refactoring work
- **Update progress:** Mark phases as complete (✅) and update the "Current State" table
- **Decision log:** Record important decisions with rationale in the plan's Decision Log section

### CRITICAL: Keep Plans Updated

**Plan files must be updated continuously, not just at session end.** This ensures work can always resume smoothly, even after unexpected context resets.

**Update `.plans/CONTINUATION-PROMPT.md` whenever:**
- You complete a task or phase
- You discover new information that affects the plan
- You make a decision that should be remembered
- Before any long-running operation (tests, builds, etc.)

**Update frequency:** After every significant action, not just at the end of a session.

### Continuation Prompt Format

The `.plans/CONTINUATION-PROMPT.md` file should always contain:
- Current branch and its purpose
- What was just completed
- What to do next (with specific file/function references)
- Any blockers, open questions, or decisions needed

Example:
```markdown
# Continuation Prompt

**Branch:** `main` (all work merges to `main`)

## Current Status
- Phase 1 (Postponed Annotations) ✅ Complete
- Phase 2 in progress: fixing encoder.py

## Next Steps
1. Fix remaining type hints in `src/the_jam_machine/embedding/encoder.py:145-200`
2. Run tests to verify changes
3. Update MASTER-PLAN.md with completion status

## Notes
- Found circular import issue between encoder.py and familizer.py - resolved with TYPE_CHECKING
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
