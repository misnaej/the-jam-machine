---
name: check
description: Run tests and linting to verify everything passes
user-invocable: true
disable-model-invocation: false
allowed-tools: Bash(pipenv run pytest:*), Bash(pipenv run ruff:*)
---

# Check

Run the full verification suite: tests + lint + format.

1. Run `pipenv run pytest test/ -v`
2. Run `pipenv run ruff check src/ test/ app/ examples/`
3. Run `pipenv run ruff format --check src/ test/ app/ examples/`

Report:
- Number of tests passed/failed
- Any lint or format issues
- Overall pass/fail status
