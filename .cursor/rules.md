# Cursor Workspace Rules for `ha-brain`

## Scope awareness

- Treat this repo as three main domains:
  1. `homeassistant-config`: YAML configurations and automations.
  2. `integrations`: Python code for custom HA integrations and shared libs.
  3. `agents`: MCP servers and agent orchestration code.

- When editing, always mention which domain you're working in and why.

## Editing rules

- For YAML:
  - Keep indentation consistent (2 spaces).
  - Don't reorder keys unnecessarily; keep diffs small.
  - Validate syntax after edits using available linters or by producing `yamllint` commands.

- For Python integrations:
  - Respect existing patterns for async, type hints, and error handling.
  - Prefer extending existing helper functions rather than duplicating logic.

## Git / change management

- Prefer creating **small, focused changes**:
  - One concern per change (e.g., "new automation" or "fix integration timeout").
- Always summarize:
  - What changed
  - Why it changed
  - Any risk or migration needed

## Safety

- Do not assume direct access to production Home Assistant.
- Any suggestion that could turn devices on/off or modify schedules should:
  - Be expressed as a **configuration or code change** rather than a direct action.
  - Include a testing plan (e.g. "apply in dev, verify logs, then roll out").

## Using MCP tools

- Prefer MCP tools that:
  - Read states and config
  - Generate diffs and test commands
- Only use tools that change HA state when:
  - Explicitly asked to run an experiment, or
  - A rule or test plan has been clearly established.
