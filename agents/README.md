# Agent Prompts

This directory contains prompt templates for code review agents used in The Jam Machine project.

## Available Agents

### DesignAgent (`design_agent.md`)

Reviews code for design principles violations:

- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **DRY**: Don't Repeat Yourself
- **YAGNI**: You Aren't Gonna Need It
- **KISS**: Keep It Simple, Stupid
- **Error Handling**: Exception handling patterns
- **Input Validation**: Boundary validation
- **Type Safety**: Type correctness
- **Security**: Hardcoded secrets, injection risks

### DocumentationAgent (`documentation_agent.md`)

Reviews code for documentation quality:

- **Docstrings**: Google-style docstring completeness
- **Type Hints**: Modern Python 3.10+ type annotations
- **Module Documentation**: Module-level docstrings and `__all__`
- **Comments**: Inline comment quality and relevance

## Usage

### With Claude Code

When using Claude Code, you can invoke these agents by:

1. Reading the agent prompt file
2. Providing the code file(s) to analyze
3. Asking for an analysis following the agent's guidelines

Example:

```
Read agents/design_agent.md and src/the_jam_machine/generating/generate.py, then analyze generate.py following the DesignAgent guidelines.
```

### Output Format

Both agents produce structured output with:

- **File:Line** - Exact location of the issue
- **Type/Principle** - Category of the issue
- **Severity** - Critical/High/Medium/Low
- **Description** - What's wrong
- **Suggestion** - How to fix it

## Priority Files to Audit

Based on the initial code audit, these files should be prioritized:

1. `src/the_jam_machine/generating/generate.py` - Largest class, multiple issues
2. `src/the_jam_machine/preprocessing/midi_stats.py` - DRY violations (40+ similar functions)
3. `src/the_jam_machine/embedding/encoder.py` - Static method overuse
4. `src/the_jam_machine/embedding/decoder.py` - Error handling issues
5. `app/playground.py` - Global state, hardcoded values

## Issue Tracking

Issues found by agents should be tracked in GitHub Issues with labels:

- `design` - Design principle violations
- `documentation` - Documentation gaps
- `security` - Security concerns
- `bug` - Logic errors or bugs
- `refactor` - Refactoring opportunities
