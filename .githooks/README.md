# Git Hooks

This directory contains Git hooks for The Jam Machine project.

## Setup

To enable these hooks, run:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/*
```

Or use the setup script:

```bash
./scripts/setup-env.sh
```

## Available Hooks

### pre-commit

Runs automatically before each commit. It performs:

1. **Ruff Linting**: Checks staged Python files for code quality issues
   - Attempts auto-fix for fixable issues
   - Re-stages fixed files automatically
   - Blocks commit if unfixable issues remain

2. **Ruff Formatting**: Ensures consistent code formatting
   - Applies formatting automatically
   - Re-stages formatted files

3. **Security Audit**: Runs pip-audit (informational only)
   - Does not block commits
   - Reports potential vulnerabilities in dependencies

## Bypassing Hooks

If you need to bypass the pre-commit hook (not recommended):

```bash
git commit --no-verify
```

## Troubleshooting

### Hook not running

1. Check hooks path is set:
   ```bash
   git config core.hooksPath
   ```
   Should return `.githooks`

2. Check hook is executable:
   ```bash
   ls -la .githooks/pre-commit
   ```
   Should have `x` permission

3. Re-run setup:
   ```bash
   git config core.hooksPath .githooks
   chmod +x .githooks/*
   ```

### pipenv not found

The hooks require pipenv to be installed and available in PATH:

```bash
pip install pipenv
```

### pip-audit not installed

Install with:

```bash
pipenv run pip install pip-audit
```
