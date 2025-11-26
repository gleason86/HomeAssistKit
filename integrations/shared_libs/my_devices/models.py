"""Data models for device communication."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DeviceState:
    """Represents the state of a device."""

    device_id: str
    status: str
    value: float | None = None
    metadata: dict[str, Any] | None = None

