"""Home Assistant REST API client."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import yaml


class HomeAssistantClient:
    """Async client for Home Assistant REST API."""

    def __init__(
        self,
        host: str | None = None,
        token: str | None = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the HA client.

        Args:
            host: HA instance URL (e.g., "http://192.168.1.110:8123")
            token: Long-lived access token
            timeout: Request timeout in seconds

        If host/token not provided, attempts to load from credentials file.
        """
        if host is None or token is None:
            loaded = self._load_credentials()
            host = host or loaded.get("host")
            token = token or loaded.get("token")

        if not host:
            raise ValueError("Home Assistant host URL is required")
        if not token:
            raise ValueError("Home Assistant access token is required")

        self.host = host.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    def _load_credentials(self) -> dict[str, str]:
        """Load credentials from yaml file."""
        # Look for credentials relative to repo root
        possible_paths = [
            Path("credentials/ha_api.yaml"),
            Path(__file__).parent.parent.parent.parent
            / "credentials"
            / "ha_api.yaml",
        ]

        for cred_path in possible_paths:
            if cred_path.exists():
                with cred_path.open() as f:
                    return yaml.safe_load(f) or {}

        return {}

    @property
    def headers(self) -> dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.host,
                headers=self.headers,
                timeout=self.timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> HomeAssistantClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()

    # =========================================================================
    # API Methods
    # =========================================================================

    async def get_config(self) -> dict[str, Any]:
        """Get Home Assistant configuration."""
        client = await self._get_client()
        response = await client.get("/api/config")
        response.raise_for_status()
        return response.json()

    async def check_api(self) -> bool:
        """Check if the API is accessible."""
        try:
            client = await self._get_client()
            response = await client.get("/api/")
            return response.status_code == 200
        except Exception:
            return False

    async def get_states(self) -> list[dict[str, Any]]:
        """
        Get all entity states.

        Returns:
            List of entity state dictionaries with keys:
            - entity_id: str
            - state: str
            - attributes: dict
            - last_changed: str (ISO timestamp)
            - last_updated: str (ISO timestamp)
        """
        client = await self._get_client()
        response = await client.get("/api/states")
        response.raise_for_status()
        return response.json()

    async def get_state(self, entity_id: str) -> dict[str, Any]:
        """
        Get state of a specific entity.

        Args:
            entity_id: The entity ID (e.g., "light.living_room")

        Returns:
            Entity state dictionary
        """
        client = await self._get_client()
        response = await client.get(f"/api/states/{entity_id}")
        response.raise_for_status()
        return response.json()

    async def get_entities_by_domain(self, domain: str) -> list[dict[str, Any]]:
        """
        Get all entities for a specific domain.

        Args:
            domain: Entity domain (e.g., "light", "switch", "sensor")

        Returns:
            List of entity states in that domain
        """
        states = await self.get_states()
        return [s for s in states if s["entity_id"].startswith(f"{domain}.")]

    async def get_history(
        self,
        entity_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        minimal_response: bool = True,
    ) -> list[list[dict[str, Any]]]:
        """
        Get historical states for entities.

        Args:
            entity_id: Optional entity ID to filter (if None, returns all)
            start_time: Start of history period (default: 1 day ago)
            end_time: End of history period (default: now)
            minimal_response: If True, only return last_changed and state

        Returns:
            List of entity histories, each containing list of state changes
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)
        if end_time is None:
            end_time = datetime.now()

        params: dict[str, Any] = {
            "end_time": end_time.isoformat(),
        }
        if entity_id:
            params["filter_entity_id"] = entity_id
        if minimal_response:
            params["minimal_response"] = "true"

        client = await self._get_client()
        url = f"/api/history/period/{start_time.isoformat()}"
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def call_service(
        self,
        domain: str,
        service: str,
        data: dict[str, Any] | None = None,
        target: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Call a Home Assistant service.

        Args:
            domain: Service domain (e.g., "light", "switch")
            service: Service name (e.g., "turn_on", "turn_off")
            data: Service data (optional)
            target: Target entities/areas/devices (optional)

        Returns:
            List of affected entity states

        Example:
            await client.call_service(
                "light", "turn_on",
                data={"brightness": 255},
                target={"entity_id": "light.living_room"}
            )
        """
        payload: dict[str, Any] = {}
        if data:
            payload.update(data)
        if target:
            payload["target"] = target

        client = await self._get_client()
        response = await client.post(
            f"/api/services/{domain}/{service}",
            json=payload if payload else None,
        )
        response.raise_for_status()
        return response.json()

    async def get_services(self) -> dict[str, Any]:
        """Get all available services."""
        client = await self._get_client()
        response = await client.get("/api/services")
        response.raise_for_status()
        return response.json()

    async def get_events(self) -> list[dict[str, Any]]:
        """Get list of available events."""
        client = await self._get_client()
        response = await client.get("/api/events")
        response.raise_for_status()
        return response.json()

    async def fire_event(
        self,
        event_type: str,
        event_data: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        Fire an event.

        Args:
            event_type: Event type name
            event_data: Optional event data

        Returns:
            Confirmation message
        """
        client = await self._get_client()
        response = await client.post(
            f"/api/events/{event_type}",
            json=event_data or {},
        )
        response.raise_for_status()
        return response.json()

    async def get_error_log(self) -> str:
        """Get the Home Assistant error log."""
        client = await self._get_client()
        response = await client.get("/api/error_log")
        response.raise_for_status()
        return response.text

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def get_entity_domains(self) -> list[str]:
        """Get list of all unique entity domains."""
        states = await self.get_states()
        domains = set()
        for state in states:
            domain = state["entity_id"].split(".")[0]
            domains.add(domain)
        return sorted(domains)

    async def search_entities(self, query: str) -> list[dict[str, Any]]:
        """
        Search entities by ID or friendly name.

        Args:
            query: Search string (case-insensitive)

        Returns:
            List of matching entity states
        """
        query_lower = query.lower()
        states = await self.get_states()
        results = []
        for state in states:
            entity_id = state["entity_id"].lower()
            friendly_name = state.get("attributes", {}).get("friendly_name", "").lower()
            if query_lower in entity_id or query_lower in friendly_name:
                results.append(state)
        return results

    async def get_entity_summary(self) -> dict[str, int]:
        """
        Get a summary count of entities by domain.

        Returns:
            Dict mapping domain names to entity counts
        """
        states = await self.get_states()
        summary: dict[str, int] = {}
        for state in states:
            domain = state["entity_id"].split(".")[0]
            summary[domain] = summary.get(domain, 0) + 1
        return dict(sorted(summary.items()))
