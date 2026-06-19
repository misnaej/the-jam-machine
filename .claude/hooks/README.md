# Consumer Claude Code hooks

This directory holds **consumer-specific** Claude Code hook scripts.
Forge ships its own hooks via the plugin manifest — those load
automatically from `${CLAUDE_PLUGIN_ROOT}/claude-hooks/...` and you do
not register them here.

## Path convention

Register every hook in `.claude/settings.json` with a **path rooted at
`${CLAUDE_PROJECT_DIR}`**, never a relative path. Relative paths break
when a hook fires from a subagent, a subdirectory, or any context where
the shell's cwd is not the repo root — you get errors like:

```
/bin/sh: 1: .claude/hooks/<name>.sh: not found
```

### Right

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/your_hook.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Wrong

```json
{ "type": "command", "command": ".claude/hooks/your_hook.sh" }
```

`${CLAUDE_PROJECT_DIR}` is populated by Claude Code with the absolute
path to the repo root regardless of shell cwd.

## Adding a hook

1. Drop the script under `.claude/hooks/<name>.sh`. Make it executable
   (`chmod +x`).
2. Register it in `.claude/settings.json` with the `${CLAUDE_PROJECT_DIR}`
   form shown above.
3. Restart Claude Code (or `/reload-plugins`) so the new hook is picked
   up.

Forge does not ship any consumer-specific hooks — only the directory
layout and this convention. The directory is created (empty) by
`install-forge-claude-md` so the path resolves on day one.
