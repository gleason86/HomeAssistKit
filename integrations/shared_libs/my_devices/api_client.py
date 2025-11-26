"""API client for device communication."""
from __future__ import annotations

import aiohttp
from typing import Any


class DeviceAPIClient:
    """Client for interacting with device APIs."""

    def __init__(self, host: str, port: int, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize the API client."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self._session = session

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch data from the device API."""
        # TODO: Implement actual API call
        async with self._session or aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/data") as response:
                response.raise_for_status()
                return await response.json()

    async def async_close(self) -> None:
        """Close the session if we own it."""
        if self._session:
            await self._session.close()

