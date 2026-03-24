---
name: pr
description: Run PR wrap-up review and generate squash merge message
user-invocable: true
disable-model-invocation: false
---

# PR Wrap-up

Run the pr-reviewer agent to review the current PR and generate a squash merge commit message.

1. Determine the PR number:
   - If $ARGUMENTS is provided, use it as the PR number
   - Otherwise, find the open PR for the current branch using `gh pr view --json number`

2. Launch the **pr-reviewer** agent with the PR number and branch info

3. The agent will:
   - Review all changes in the PR (design + docs)
   - Generate a squash merge commit message following project conventions
   - Post findings as a PR comment

IMPORTANT:
- Use the `pr-reviewer` subagent type
- Per CLAUDE.md: do NOT add AI attribution ("Generated with Claude Code", "Co-Authored-By: Claude") to the commit message
- Squash merge title: max 100 characters
- Squash merge body: max 50 words, ideally less. Focus on what was done in broad strokes — no details, counts, or line numbers
