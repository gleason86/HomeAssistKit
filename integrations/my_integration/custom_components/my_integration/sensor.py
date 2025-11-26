"""Sensor platform for My Integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MyIntegrationDataUpdateCoordinator

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="example",
        name="Example Sensor",
        native_unit_of_measurement="units",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up My Integration sensor entities."""
    coordinator: MyIntegrationDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        MyIntegrationSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    )


class MyIntegrationSensor(
    CoordinatorEntity[MyIntegrationDataUpdateCoordinator], SensorEntity
):
    """My Integration Sensor."""

    def __init__(
        self,
        coordinator: MyIntegrationDataUpdateCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        # TODO: Return actual sensor value from coordinator.data
        return self.coordinator.data.get(self.entity_description.key)

