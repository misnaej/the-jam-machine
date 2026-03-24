---
name: commit
description: Lint, commit, and push changes to the current feature branch
user-invocable: true
disable-model-invocation: false
---

# Commit and Push

1. Run `pipenv run ruff check --fix src/ test/ app/ examples/` and `pipenv run ruff format src/ test/ app/ examples/`
2. Run `git status` and `git diff` to review changes
3. Stage relevant files (prefer specific files over `git add -A`)
4. Commit with a concise message focused on the "why" — no AI attribution
5. Push to the current branch (never to main)

If $ARGUMENTS is provided, use it as the commit message.

Follow all commit guidelines from CLAUDE.md → "Commit and PR Style".
