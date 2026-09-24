"""MCP Server for Home Assistant integration."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .ha_client import HomeAssistantClient

# Initialize MCP server
server = Server("ha-mcp-server")

# Global HA client instance (initialized on first use)
_ha_client: HomeAssistantClient | None = None


def get_ha_client() -> HomeAssistantClient:
    """Get or create the HA client instance."""
    global _ha_client
    if _ha_client is None:
        _ha_client = HomeAssistantClient()
    return _ha_client


# =============================================================================
# Tool Definitions
# =============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="ha_list_entities",
            description="List all Home Assistant entities, optionally filtered by domain (e.g., 'light', 'switch', 'sensor')",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Optional domain to filter by (e.g., 'light', 'switch', 'sensor', 'binary_sensor')",
                    },
                },
            },
        ),
        Tool(
            name="ha_get_state",
            description="Get the current state and attributes of a specific Home Assistant entity",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID (e.g., 'light.living_room', 'sensor.temperature')",
                    },
                },
                "required": ["entity_id"],
            },
        ),
        Tool(
            name="ha_search_entities",
            description="Search for entities by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to match against entity IDs and friendly names",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="ha_get_history",
            description="Get historical state changes for an entity over a time period",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "The entity ID to get history for",
                    },
                    "hours": {
                        "type": "number",
                        "description": "Number of hours of history to retrieve (default: 24, max: 168)",
                    },
                },
                "required": ["entity_id"],
            },
        ),
        Tool(
            name="ha_entity_summary",
            description="Get a summary of all entity domains and counts in Home Assistant",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="ha_call_service",
            description="Call a Home Assistant service (e.g., turn on/off lights, run scripts). Use with caution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Service domain (e.g., 'light', 'switch', 'script')",
                    },
                    "service": {
                        "type": "string",
                        "description": "Service name (e.g., 'turn_on', 'turn_off', 'toggle')",
                    },
                    "entity_id": {
                        "type": "string",
                        "description": "Target entity ID (or comma-separated list of entity IDs)",
                    },
                    "area_id": {
                        "type": "string",
                        "description": "Target area ID (e.g., 'living_room', 'kitchen') - affects all entities in area",
                    },
                    "device_id": {
                        "type": "string",
                        "description": "Target device ID - affects all entities on device",
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional service data (e.g., brightness, color)",
                    },
                },
                "required": ["domain", "service"],
            },
        ),
        Tool(
            name="ha_get_services",
            description="List all available services in Home Assistant",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Optional domain to filter services by",
                    },
                },
            },
        ),
        Tool(
            name="ha_get_logbook",
            description="Get logbook entries showing what happened in Home Assistant (events with context)",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Optional entity ID to filter logbook entries",
                    },
                    "hours": {
                        "type": "number",
                        "description": "Number of hours of history to retrieve (default: 24, max: 168)",
                    },
                },
            },
        ),
        Tool(
            name="ha_render_template",
            description="Render a Jinja2 template to query Home Assistant dynamically",
            inputSchema={
                "type": "object",
                "properties": {
                    "template": {
                        "type": "string",
                        "description": "Jinja2 template string (e.g., \"{{ states('sensor.temperature') }}\")",
                    },
                },
                "required": ["template"],
            },
        ),
        Tool(
            name="ha_get_config",
            description="Get Home Assistant instance configuration (version, location, units, etc.)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="ha_fire_event",
            description="Fire a custom event in Home Assistant to trigger automations",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "description": "Event type name (e.g., 'custom_event')",
                    },
                    "event_data": {
                        "type": "object",
                        "description": "Optional event data payload",
                    },
                },
                "required": ["event_type"],
            },
        ),
        Tool(
            name="ha_get_calendars",
            description="Get calendar entities and their upcoming events",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Optional calendar entity ID to get events for",
                    },
                    "days": {
                        "type": "number",
                        "description": "Number of days ahead to look for events (default: 7)",
                    },
                },
            },
        ),
    ]


# =============================================================================
# Tool Handlers
# =============================================================================


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        result = await _handle_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e!s}")]


async def _handle_tool(name: str, arguments: dict[str, Any]) -> str:
    """Route tool calls to handlers."""
    client = get_ha_client()

    # Map tool names to handlers
    handlers = {
        "ha_list_entities": lambda: _handle_list_entities(client, arguments),
        "ha_get_state": lambda: _handle_get_state(client, arguments),
        "ha_search_entities": lambda: _handle_search_entities(client, arguments),
        "ha_get_history": lambda: _handle_get_history(client, arguments),
        "ha_entity_summary": lambda: _handle_entity_summary(client),
        "ha_call_service": lambda: _handle_call_service(client, arguments),
        "ha_get_services": lambda: _handle_get_services(client, arguments),
        "ha_get_logbook": lambda: _handle_get_logbook(client, arguments),
        "ha_render_template": lambda: _handle_render_template(client, arguments),
        "ha_get_config": lambda: _handle_get_config(client),
        "ha_fire_event": lambda: _handle_fire_event(client, arguments),
        "ha_get_calendars": lambda: _handle_get_calendars(client, arguments),
    }

    handler = handlers.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")

    return await handler()


async def _handle_list_entities(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_list_entities tool."""
    domain = arguments.get("domain")

    if domain:
        states = await client.get_entities_by_domain(domain)
    else:
        states = await client.get_states()

    # Format as concise list
    entities = []
    for state in states:
        entity_id = state["entity_id"]
        current_state = state["state"]
        friendly_name = state.get("attributes", {}).get("friendly_name", "")

        if friendly_name and friendly_name != entity_id:
            entities.append(f"- {entity_id}: {current_state} ({friendly_name})")
        else:
            entities.append(f"- {entity_id}: {current_state}")

    header = f"Found {len(entities)} entities"
    if domain:
        header += f" in domain '{domain}'"

    return f"{header}:\n" + "\n".join(entities)


async def _handle_get_state(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_get_state tool."""
    entity_id = arguments["entity_id"]
    state = await client.get_state(entity_id)

    # Format nicely
    result = {
        "entity_id": state["entity_id"],
        "state": state["state"],
        "last_changed": state.get("last_changed"),
        "last_updated": state.get("last_updated"),
        "attributes": state.get("attributes", {}),
    }
    return json.dumps(result, indent=2)


async def _handle_search_entities(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_search_entities tool."""
    query = arguments["query"]
    states = await client.search_entities(query)

    if not states:
        return f"No entities found matching '{query}'"

    entities = []
    for state in states:
        entity_id = state["entity_id"]
        current_state = state["state"]
        friendly_name = state.get("attributes", {}).get("friendly_name", "")

        if friendly_name:
            entities.append(f"- {entity_id}: {current_state} ({friendly_name})")
        else:
            entities.append(f"- {entity_id}: {current_state}")

    return f"Found {len(entities)} entities matching '{query}':\n" + "\n".join(entities)


async def _handle_get_history(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_get_history tool."""
    entity_id = arguments["entity_id"]
    hours = min(arguments.get("hours", 24), 168)  # Cap at 1 week

    start_time = datetime.now() - timedelta(hours=hours)
    history = await client.get_history(
        entity_id=entity_id,
        start_time=start_time,
    )

    if not history or not history[0]:
        return f"No history found for {entity_id} in the last {hours} hours"

    # Format history
    changes = history[0]
    lines = [
        f"History for {entity_id} (last {hours} hours, {len(changes)} state changes):"
    ]

    for entry in changes[-20:]:  # Show last 20 changes
        timestamp = entry.get("last_changed", "unknown")
        state = entry.get("state", "unknown")
        lines.append(f"  {timestamp}: {state}")

    if len(changes) > 20:
        lines.append(f"  ... ({len(changes) - 20} earlier entries not shown)")

    return "\n".join(lines)


async def _handle_entity_summary(client: HomeAssistantClient) -> str:
    """Handle ha_entity_summary tool."""
    summary = await client.get_entity_summary()

    total = sum(summary.values())
    lines = [f"Home Assistant Entity Summary ({total} total entities):", ""]

    for domain, count in summary.items():
        lines.append(f"  {domain}: {count}")

    return "\n".join(lines)


async def _handle_call_service(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_call_service tool."""
    domain = arguments["domain"]
    service = arguments["service"]
    entity_id = arguments.get("entity_id")
    area_id = arguments.get("area_id")
    device_id = arguments.get("device_id")
    data = arguments.get("data", {})

    # Build target dict
    target: dict[str, Any] = {}
    target_desc = []

    if entity_id:
        # Support comma-separated entity IDs
        if "," in entity_id:
            target["entity_id"] = [e.strip() for e in entity_id.split(",")]
            target_desc.append(f"entities: {entity_id}")
        else:
            target["entity_id"] = entity_id
            target_desc.append(f"entity: {entity_id}")

    if area_id:
        target["area_id"] = area_id
        target_desc.append(f"area: {area_id}")

    if device_id:
        target["device_id"] = device_id
        target_desc.append(f"device: {device_id}")

    if not target:
        return (
            "Error: At least one target (entity_id, area_id, or device_id) is required"
        )

    # Call the service
    result = await client.call_service(
        domain=domain,
        service=service,
        data=data,
        target=target,
    )

    return f"Service {domain}.{service} called on {', '.join(target_desc)}. Affected entities: {len(result)}"


async def _handle_get_services(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_get_services tool."""
    services = await client.get_services()
    domain_filter = arguments.get("domain")

    lines = []
    for service_domain in services:
        domain = service_domain.get("domain", "")

        if domain_filter and domain != domain_filter:
            continue

        domain_services = service_domain.get("services", {})
        lines.append(f"\n{domain}:")

        for service_name, service_info in domain_services.items():
            description = service_info.get("description", "")
            if description:
                lines.append(f"  - {service_name}: {description[:80]}")
            else:
                lines.append(f"  - {service_name}")

    if not lines:
        if domain_filter:
            return f"No services found for domain '{domain_filter}'"
        return "No services found"

    return "Available services:" + "\n".join(lines)


async def _handle_get_logbook(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_get_logbook tool."""
    entity_id = arguments.get("entity_id")
    hours = min(arguments.get("hours", 24), 168)  # Cap at 1 week

    start_time = datetime.now() - timedelta(hours=hours)
    entries = await client.get_logbook(
        entity_id=entity_id,
        start_time=start_time,
    )

    if not entries:
        msg = f"No logbook entries found in the last {hours} hours"
        if entity_id:
            msg += f" for {entity_id}"
        return msg

    lines = [f"Logbook entries (last {hours} hours, {len(entries)} events):"]

    for entry in entries[-50:]:  # Show last 50 entries
        when = entry.get("when", "unknown")
        name = entry.get("name", "Unknown")
        message = entry.get("message", "")
        state = entry.get("state", "")
        entity = entry.get("entity_id", "")

        line = f"  [{when}] {name}"
        if message:
            line += f": {message}"
        elif state:
            line += f" -> {state}"
        if entity and entity != entity_id:
            line += f" ({entity})"
        lines.append(line)

    if len(entries) > 50:
        lines.append(f"  ... ({len(entries) - 50} earlier entries not shown)")

    return "\n".join(lines)


async def _handle_render_template(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_render_template tool."""
    template = arguments["template"]
    result = await client.render_template(template)
    return f"Template result:\n{result}"


async def _handle_get_config(client: HomeAssistantClient) -> str:
    """Handle ha_get_config tool."""
    config = await client.get_config()

    # Extract useful info
    result = {
        "location_name": config.get("location_name"),
        "version": config.get("version"),
        "unit_system": config.get("unit_system"),
        "time_zone": config.get("time_zone"),
        "latitude": config.get("latitude"),
        "longitude": config.get("longitude"),
        "elevation": config.get("elevation"),
        "currency": config.get("currency"),
        "state": config.get("state"),
    }
    return json.dumps(result, indent=2)


async def _handle_fire_event(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_fire_event tool."""
    event_type = arguments["event_type"]
    event_data = arguments.get("event_data", {})

    result = await client.fire_event(event_type, event_data)
    return f"Event '{event_type}' fired successfully. {result.get('message', '')}"


async def _handle_get_calendars(
    client: HomeAssistantClient,
    arguments: dict[str, Any],
) -> str:
    """Handle ha_get_calendars tool."""
    entity_id = arguments.get("entity_id")
    days = min(arguments.get("days", 7), 30)  # Cap at 30 days

    if entity_id:
        # Get events for specific calendar
        end_time = datetime.now() + timedelta(days=days)
        events = await client.get_calendar_events(
            entity_id=entity_id,
            end=end_time,
        )

        if not events:
            return f"No upcoming events in {entity_id} for the next {days} days"

        lines = [f"Events in {entity_id} (next {days} days):"]
        for event in events[:20]:
            summary = event.get("summary", "Untitled")
            start = event.get("start", {})
            start_time = start.get("dateTime") or start.get("date", "Unknown")
            lines.append(f"  - {start_time}: {summary}")

        if len(events) > 20:
            lines.append(f"  ... ({len(events) - 20} more events)")

        return "\n".join(lines)
    else:
        # List all calendars
        calendars = await client.get_calendars()

        if not calendars:
            return "No calendar entities found"

        lines = [f"Found {len(calendars)} calendars:"]
        for cal in calendars:
            cal_id = cal.get("entity_id", "")
            name = cal.get("name", cal_id)
            lines.append(f"  - {cal_id}: {name}")

        return "\n".join(lines)


# =============================================================================
# Main Entry Point
# =============================================================================


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run():
    """Entry point for running the server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
