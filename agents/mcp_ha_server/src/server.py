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
                        "description": "Target entity ID",
                    },
                    "data": {
                        "type": "object",
                        "description": "Optional service data (e.g., brightness, color)",
                    },
                },
                "required": ["domain", "service", "entity_id"],
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

    if name == "ha_list_entities":
        return await _handle_list_entities(client, arguments)
    elif name == "ha_get_state":
        return await _handle_get_state(client, arguments)
    elif name == "ha_search_entities":
        return await _handle_search_entities(client, arguments)
    elif name == "ha_get_history":
        return await _handle_get_history(client, arguments)
    elif name == "ha_entity_summary":
        return await _handle_entity_summary(client)
    elif name == "ha_call_service":
        return await _handle_call_service(client, arguments)
    elif name == "ha_get_services":
        return await _handle_get_services(client, arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


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
    entity_id = arguments["entity_id"]
    data = arguments.get("data", {})

    # Call the service
    result = await client.call_service(
        domain=domain,
        service=service,
        data=data,
        target={"entity_id": entity_id},
    )

    return f"Service {domain}.{service} called on {entity_id}. Affected entities: {len(result)}"


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
