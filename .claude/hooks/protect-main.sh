#!/bin/bash
# Block direct pushes to main. Use a feature branch + PR instead.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if echo "$COMMAND" | grep -qE '^git push\b.*(origin\s+main\b|origin/main\b)'; then
  echo "Blocked: cannot push directly to main. Create a feature branch and PR instead." >&2
  exit 2
fi

exit 0
