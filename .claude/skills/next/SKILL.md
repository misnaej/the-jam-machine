---
name: next
description: Sync main, clean up stale branches, and start the next task
user-invocable: true
disable-model-invocation: false
---

# Next

Prepare for the next task by syncing the repo and identifying what's next.

## Steps

### 1. Check for uncommitted work
- Run `git status`. If there are uncommitted changes, warn the user and stop.

### 2. Sync main
- `git checkout main`
- `git pull origin main`

### 3. Clean up stale local branches
- List all local branches except `main`
- Check which ones have been merged (their remote was deleted or PR merged)
- Delete merged local branches: `git branch -D <branch>`
- Run `git fetch --prune` to remove stale remote tracking refs

### 4. Confirm clean state
- `git branch` should show only `main`
- `git status` should be clean

### 5. Identify the next task
- Read `.plans/MASTER-PLAN.md` to find the "Next step" pointer
- Read the relevant plan file for details
- If the next step is clear, present it to the user:
  - What is the task?
  - What files will be affected?
  - Estimated scope (small/medium/large)
- Ask for confirmation before starting
- If confirmed, create the feature branch and begin planning
