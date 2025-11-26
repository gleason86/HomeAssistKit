# MCP Home Assistant Server

MCP (Model Context Protocol) server for Home Assistant integration.

## Overview

This MCP server exposes tools that allow AI agents to interact with Home Assistant:
- Read entity states and configurations
- List automations and scripts
- Propose configuration changes as patches
- Run tests and validations

## Architecture

The server communicates with:
- Home Assistant instance via REST/WebSocket API
- Git repository for reading/writing config and code

## Tools

### Read-only tools (always safe)
- `ha_list_entities(domain?)` - List all entities or filter by domain
- `ha_get_state(entity_id)` - Get current state of an entity
- `ha_list_automations()` - List all automations
- `repo_diff(path?)` - Show git diff for specified path

### Write tools (guarded, require approval)
- `ha_call_service(domain, service, data)` - Call a Home Assistant service
- `ha_propose_automation(diff)` - Propose an automation change as a patch
- `repo_apply_patch(patch)` - Apply a git patch after approval
- `repo_run_tests(target?)` - Run tests for specified target

## Setup

1. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Configure Home Assistant connection in environment or config file

3. Run the server:
   ```bash
   python -m mcp_ha_server
   ```

## Development

See `src/` for implementation and `tests/` for test suite.

