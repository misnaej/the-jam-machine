# Git Hooks

## Setup

```bash
git config core.hooksPath .githooks
chmod +x .githooks/*
```

Or use `./scripts/setup-env.sh`.

## Pre-commit Hook

Runs automatically before each commit:

| Check | Tool | Blocking | Auto-fix |
|-------|------|----------|----------|
| Linting | ruff check | Yes | Yes (re-stages) |
| Formatting | ruff format | Yes | Yes (re-stages) |
| Docstring coverage | interrogate (95%) | Yes | No |
| Code security | bandit | Yes | No |
| Dependency CVEs | pip-audit | No (informational) | No |

After checks pass, the hook generates badge SVGs in `.githooks/badges/`.

## Logs

All hook output is saved to `.githooks/logs/`:

```
.githooks/logs/
├── latest.log                    # Symlink to most recent run
├── pre-commit-20260325_100641.log
├── pre-commit-20260325_103012.log
└── ...
```

**When a commit fails**, read the log to see what went wrong:

```bash
cat .githooks/logs/latest.log
```

## Badges

Generated SVGs in `.githooks/badges/`:

| Badge | Source |
|-------|--------|
| `docstring-coverage.svg` | interrogate |
| `bandit.svg` | shields.io (pass/fail) |

Referenced from `README.md` as local images.

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
