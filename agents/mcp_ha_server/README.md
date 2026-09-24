# MCP Home Assistant Server

MCP (Model Context Protocol) server for Home Assistant integration. This server allows Claude (in Cursor) to query and control your Home Assistant instance.

## Overview

This MCP server exposes tools that allow AI agents to interact with Home Assistant:

- Read entity states, configurations, and calendars
- Search entities by name or domain
- Query historical state data and event logs
- Call services with entity, area, or device targeting
- Render Jinja2 templates for dynamic queries
- Fire events to trigger automations

## Setup

### 1. Install Dependencies

From the `agents/mcp_ha_server` directory:

```bash
pip install -e ".[dev]"
```

Or from repo root:

```bash
pip install httpx websockets pyyaml mcp
```

### 2. Configure Home Assistant API Token

1. Open Home Assistant in your browser: `http://192.168.1.110:8123`
2. Click your profile (bottom-left)
3. Scroll to "Long-Lived Access Tokens"
4. Click "Create Token", name it "MCP Agent"
5. Copy the token to `credentials/ha_api.yaml`:

```yaml
host: "http://192.168.1.110:8123"
token: "<your-token-here>"
```

### 3. Register with Cursor

Copy the `mcp.json` from repo root to your Cursor MCP config, or add manually:

**Windows**: `C:\Users\<username>\.cursor\mcp.json`
**macOS**: `~/.cursor/mcp.json`

```json
{
  "mcpServers": {
    "home-assistant": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "C:/Users/david/Repos/ha_brain/agents/mcp_ha_server",
      "env": {
        "PYTHONPATH": "C:/Users/david/Repos/ha_brain/agents/mcp_ha_server"
      }
    }
  }
}
```

> **Note:** Use absolute paths for reliability. The repo includes an `mcp.json` with relative paths that works when Cursor resolves from workspace root.

### 4. Restart Cursor

Restart Cursor to load the MCP server. Claude should now have access to the HA tools.

## Available Tools

### Read-only (safe)

- `ha_list_entities` - List all entities, optionally filtered by domain
- `ha_get_state` - Get current state and attributes of an entity
- `ha_search_entities` - Search entities by name or ID
- `ha_get_history` - Query historical state changes
- `ha_entity_summary` - Get count of entities by domain
- `ha_get_services` - List available services
- `ha_get_logbook` - Get event log with context (what happened and why)
- `ha_get_config` - Get HA instance info (version, location, units)
- `ha_get_calendars` - List calendars and upcoming events
- `ha_render_template` - Evaluate Jinja2 templates dynamically

### Write (use with care)

- `ha_call_service` - Call a service (supports entity, area, or device targeting)
- `ha_fire_event` - Fire custom events to trigger automations

## Example Usage (in Cursor)

Once configured, you can ask Claude things like:

- "What lights are currently on in my house?"
- "Show me the temperature sensor history for the last 6 hours"
- "What entities do I have in my Home Assistant?"
- "Turn off the living room lights"
- "Turn off all lights in the kitchen" (area targeting)
- "What happened in the last hour?" (logbook)
- "What's on my calendar this week?"
- "What's the average temperature?" (template)

## Development

### Run Server Manually

```bash
cd agents/mcp_ha_server
python -m src
```

### Run Tests

```bash
pytest tests/
```

## Architecture

```
Cursor (Claude) → MCP Protocol → server.py → ha_client.py → HA REST API → Pi
```

The server uses stdio for MCP communication and httpx for async HTTP requests to Home Assistant.
