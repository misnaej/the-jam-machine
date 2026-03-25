---
name: lint
description: Run ruff linting and formatting on the codebase
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash(pipenv run ruff:*)
---

# Lint

Run ruff check and format on the project source code.

1. Run `pipenv run ruff check src/ test/ app/ examples/`
2. If issues are found, run `pipenv run ruff check --fix src/ test/ app/ examples/` to auto-fix
3. Run `pipenv run ruff format src/ test/ app/ examples/`
4. Report what was fixed (if anything) or confirm all clean

If $ARGUMENTS is provided, lint only those paths instead of the defaults.
