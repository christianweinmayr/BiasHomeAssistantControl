"""Number platform for Powersoft Bias integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BiasDataUpdateCoordinator
from .const import (
    CONF_HOST,
    DOMAIN,
    MANUFACTURER,
    MAX_CHANNELS,
    PATH_CHANNEL_GAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bias number entities."""
    coordinator: BiasDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Create gain control for each channel
    for channel in range(MAX_CHANNELS):
        entities.append(BiasChannelGain(coordinator, entry, channel))

    async_add_entities(entities)


class BiasChannelGain(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Representation of a Bias channel gain control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0.0
    _attr_native_max_value = 2.0
    _attr_native_step = 0.01
    _attr_native_unit_of_measurement = None
    _attr_icon = "mdi:volume-high"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the gain control."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_channel_{channel}_gain"
        self._attr_name = f"Channel {channel + 1} Gain"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current gain value."""
        if self.coordinator.data:
            return self.coordinator.data.get("channels", {}).get(self._channel, {}).get("gain")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new gain value."""
        path = PATH_CHANNEL_GAIN.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, value)

            # Update coordinator data immediately
            if self.coordinator.data:
                self.coordinator.data["channels"][self._channel]["gain"] = value
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set gain for channel %d: %s", self._channel, err)
            raise
