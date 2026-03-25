# Plan: CI Workflow, Badges & Security

**Date:** 2026-03-25
**Status:** Planned

---

## Goal

Set up GitHub Actions CI with automated checks and README badges for: tests passing, test coverage, docstring coverage, and security audit. Enable Dependabot for automated dependency updates.

---

## Badges to add

| Badge | Source | Tool |
|-------|--------|------|
| Tests passing | GitHub Actions | `pytest` |
| Test coverage % | Codecov | `pytest-cov` → Codecov |
| Docstring coverage % | GitHub Actions | `interrogate` |
| Security | GitHub Actions | `pip-audit` + `bandit` |

---

## Steps

### Step 1: Add CI dependencies to `pyproject.toml`

Add to `[project.optional-dependencies] ci`:

```toml
ci = [
    "ruff", "pytest", "pytest-cov", "pytest-html", "pip-audit",
    "bandit", "interrogate",
]
```

- `bandit` — static security analysis for Python code (catches hardcoded secrets, SQL injection, insecure functions, etc.)
- `interrogate` — measures docstring coverage (% of functions/classes with docstrings)
- `pytest-cov` — already listed, generates coverage reports

### Step 2: Create GitHub Actions workflow

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install FluidSynth
        run: sudo apt-get install -y fluidsynth

      - name: Install dependencies
        run: |
          pip install pipenv
          pipenv install -e ".[ci]"

      - name: Lint
        run: |
          pipenv run ruff check src/ test/ app/ examples/
          pipenv run ruff format --check src/ test/ app/ examples/

      - name: Tests with coverage
        run: pipenv run pytest test/ -v --cov=jammy --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

      - name: Docstring coverage
        run: |
          pipenv run interrogate src/jammy/ -v --fail-under 80

      - name: Security - pip-audit
        run: pipenv run pip-audit --progress-spinner off
        continue-on-error: true  # Informational — don't block PRs on upstream CVEs

      - name: Security - bandit
        run: pipenv run bandit -r src/jammy/ -c pyproject.toml
```

### Step 3: Add bandit config to `pyproject.toml`

```toml
[tool.bandit]
exclude_dirs = ["test/", "examples/"]
skips = ["B101"]  # skip assert warnings (used in tests)
```

### Step 4: Add interrogate config to `pyproject.toml`

```toml
[tool.interrogate]
ignore-init-method = true
ignore-init-module = true
fail-under = 80
exclude = ["test/", "examples/"]
verbose = 1
```

### Step 5: Add badges to README

```markdown
[![CI](https://github.com/misnaej/the-jam-machine/actions/workflows/ci.yml/badge.svg)](https://github.com/misnaej/the-jam-machine/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/misnaej/the-jam-machine/branch/main/graph/badge.svg)](https://codecov.io/gh/misnaej/the-jam-machine)
[![Interrogate](https://img.shields.io/badge/docstrings-80%25-brightgreen)](https://github.com/misnaej/the-jam-machine)
```

The docstring badge will need to be updated manually (or via a GitHub Action that updates the badge dynamically). Codecov provides its own dynamic badge once connected.

### Step 6: Enable Dependabot

Create `.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
```

This will automatically create PRs when dependencies have security updates or new versions.

### Step 7: Run locally first

Before pushing the workflow, verify everything passes locally:

```bash
# Test coverage
pipenv run pytest test/ -v --cov=jammy --cov-report=term-missing

# Docstring coverage
pipenv run interrogate src/jammy/ -v

# Bandit
pipenv run bandit -r src/jammy/

# pip-audit
pipenv run pip-audit
```

Fix any issues found before enabling CI.

---

## Tool Rationale

### Why pip-audit AND bandit (not redundant)

They check completely different things:
- **pip-audit** — scans *dependencies* for known CVEs (e.g. "gradio 6.5.1 has CVE-2026-28414")
- **bandit** — scans *your code* for security anti-patterns (e.g. hardcoded passwords, shell injection, insecure temp files)

### Why not safety?

`safety` does the same thing as `pip-audit` (dependency CVE scanning). `pip-audit` uses the OSV database which is more comprehensive and actively maintained. No need for both.

### Why Codecov over Coveralls?

Codecov has better GitHub integration, PR comments with coverage diffs, and a generous free tier for open source.

---

## Files Changed

| File | Action |
|------|--------|
| `.github/workflows/ci.yml` | **CREATE** |
| `.github/dependabot.yml` | **CREATE** |
| `pyproject.toml` | **UPDATE** add bandit, interrogate to ci deps + tool config |
| `README.md` | **UPDATE** add CI, coverage, docstring badges |

---

## Verification

```bash
# Full local verification
pipenv install -e ".[ci]"
pipenv run pytest test/ -v --cov=jammy
pipenv run interrogate src/jammy/ -v
pipenv run bandit -r src/jammy/
pipenv run pip-audit

# Push and verify GitHub Actions passes
git push origin feature/ci-badges
# Check https://github.com/misnaej/the-jam-machine/actions
```
