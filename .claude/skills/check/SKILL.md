---
name: check
description: Run all quality checks — lint, format, docstrings, security, and tests
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash(pipenv run:*), Bash(./scripts/run-tests.sh:*)
---

# Check

Run the full verification suite (same as pre-commit hook + tests).

1. Run `pipenv run ruff check src/ test/ app/ examples/` (auto-fix if needed)
2. Run `pipenv run ruff format --check src/ test/ app/ examples/`
3. Run `pipenv run interrogate src/jammy/ -v --fail-under 95`
4. Run `pipenv run bandit -r src/jammy/ -c pyproject.toml`
5. Run `./scripts/run-tests.sh` (tests with coverage, generates badges)

Report:
- Lint and format status
- Docstring coverage percentage
- Security issues (if any)
- Number of tests passed/failed
- Test coverage percentage
- Overall pass/fail status
