# Git Hooks

## Setup

```bash
git config core.hooksPath .githooks
chmod +x .githooks/*
```

Or use `./scripts/setup-env.sh`.

## Pre-commit Hook

Runs automatically before each commit. If any blocking check fails, the commit is rejected.

### Checks

#### 1. Ruff Linting (blocking, auto-fix)

**What:** Runs `ruff check` on staged Python files to catch code quality issues — unused imports, undefined names, style violations, etc.

**How:** If issues are found, the hook tries `ruff check --fix` to auto-fix them and re-stages the files. If unfixable issues remain, the commit is blocked.

**Why:** Catches problems before they enter the codebase. Auto-fix means most issues are resolved without manual intervention. Configuration is in `pyproject.toml` under `[tool.ruff]`.

#### 2. Ruff Formatting (blocking, auto-fix)

**What:** Runs `ruff format` to enforce consistent code style — indentation, quotes, line length, import ordering.

**How:** If formatting differs, the hook applies it and re-stages the files. The commit proceeds with the formatted version.

**Why:** Eliminates style debates in code review. Everyone's code looks the same regardless of editor settings.

#### 3. Docstring Coverage (blocking)

**What:** Runs `interrogate` to measure what percentage of public modules, classes, and functions have docstrings. Threshold is 95%.

**How:** Scans all files in `src/jammy/`. If coverage drops below 95%, the commit is blocked and the hook prints which files are missing docstrings.

**Why:** Docstrings are required by the project standards (see CLAUDE.md). This prevents undocumented code from being committed. Configuration is in `pyproject.toml` under `[tool.interrogate]`.

#### 4. Bandit Security Scan (blocking)

**What:** Runs `bandit` to find security anti-patterns in source code — hardcoded secrets, shell injection risks, insecure function usage, unpinned downloads.

**How:** Scans `src/jammy/` using the config in `pyproject.toml` (skips B101 assert warnings, B311 random for non-security use, B105/B106 token string false positives). If real issues are found, the commit is blocked.

**Why:** Catches security problems at the source. Different from pip-audit — bandit scans *your code*, not your dependencies.

#### 5. pip-audit Dependency Scan (informational, non-blocking)

**What:** Runs `pip-audit` to check installed packages against known CVE databases.

**How:** Reports any dependencies with known vulnerabilities. Does not block the commit — these are upstream issues you can't fix immediately.

**Why:** Keeps you aware of supply chain risks. When a vulnerability is reported, you can upgrade the dependency or track it until a fix is released.

#### 6. Badge Generation (non-blocking)

**What:** Generates SVG badge images for docstring coverage and security status.

**How:** Uses `interrogate --generate-badge` for docstring coverage and downloads a shields.io badge for bandit pass/fail. Badges are saved to `.githooks/badges/` and auto-staged.

**Why:** The README references these local badge images so that GitHub displays up-to-date project health indicators without needing a CI service.

### Generated Artifacts

#### Logs

All hook output is saved to `.githooks/logs/`:

```
.githooks/logs/
├── latest.log                         # Symlink → most recent run
├── pre-commit-20260325_100641.log
└── ...
```

Read the latest log to diagnose failures:

```bash
cat .githooks/logs/latest.log
```

#### Badges

SVG images in `.githooks/badges/`, referenced by `README.md`:

| Badge | Source | Updates |
|-------|--------|---------|
| `docstring-coverage.svg` | interrogate | Every commit |
| `bandit.svg` | shields.io | Every commit |

## Troubleshooting

**Hook not running?**
```bash
git config core.hooksPath  # should return .githooks
ls -la .githooks/pre-commit  # should have x permission
```

**Tools not found?**
```bash
pipenv install -e ".[ci]"
```

**Reading the failure log:**
```bash
cat .githooks/logs/latest.log
```
