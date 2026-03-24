---
name: review
description: Run design and documentation review agents on changed files
user-invocable: true
disable-model-invocation: false
---

# Review

Run both the design-reviewer and docs-reviewer agents in parallel on recently changed files.

1. Determine which files were changed:
   - If on a feature branch, use `git diff --name-only origin/main..HEAD -- '*.py'` to find changed Python files
   - If $ARGUMENTS is provided, review those specific files instead

2. Launch both agents in parallel using the Agent tool:
   - **design-reviewer**: Check the changed files for SOLID, DRY, YAGNI, KISS violations
   - **docs-reviewer**: Check docstrings, type hints, and comments for accuracy and completeness

3. Summarize findings from both agents, grouped by severity (High → Medium → Low)

IMPORTANT: Use the `design-reviewer` and `docs-reviewer` subagent types as defined in the project's agent definitions.
