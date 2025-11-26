"""MCP Home Assistant Server."""

__version__ = "0.1.0"

from .ha_client import HomeAssistantClient
from .server import run, server

__all__ = ["HomeAssistantClient", "run", "server"]
