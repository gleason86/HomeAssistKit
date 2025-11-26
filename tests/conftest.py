"""Pytest configuration and fixtures for ha-brain tests."""

import pytest


@pytest.fixture
def sample_entity_state() -> dict:
    """Provide a sample Home Assistant entity state for testing."""
    return {
        "entity_id": "light.living_room",
        "state": "on",
        "attributes": {
            "friendly_name": "Living Room Light",
            "brightness": 255,
            "color_mode": "brightness",
            "supported_color_modes": ["brightness"],
        },
        "last_changed": "2024-01-01T12:00:00+00:00",
        "last_updated": "2024-01-01T12:00:00+00:00",
    }


@pytest.fixture
def sample_automation_config() -> dict:
    """Provide a sample Home Assistant automation config for testing."""
    return {
        "alias": "Turn on lights at sunset",
        "description": "Automatically turn on lights when the sun sets",
        "trigger": [
            {
                "platform": "sun",
                "event": "sunset",
                "offset": "-00:30:00",
            }
        ],
        "condition": [],
        "action": [
            {
                "service": "light.turn_on",
                "target": {"entity_id": "light.living_room"},
                "data": {"brightness": 200},
            }
        ],
        "mode": "single",
    }
