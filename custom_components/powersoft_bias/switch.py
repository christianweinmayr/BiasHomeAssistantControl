"""Switch platform for Powersoft Bias integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BiasDataUpdateCoordinator
from .const import (
    CONF_HOST,
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    MAX_CHANNELS,
    PATH_CHANNEL_MUTE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bias switch entities."""
    coordinator: BiasDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Create mute switch for each channel
    for channel in range(MAX_CHANNELS):
        entities.append(BiasChannelMute(coordinator, entry, channel))

    async_add_entities(entities)


class BiasChannelMute(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias channel mute switch."""

    _attr_icon = "mdi:volume-off"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the mute switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_channel_{channel}_mute"
        self._attr_name = f"Channel {channel + 1} Mute"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the channel is muted."""
        if self.coordinator.data:
            return self.coordinator.data.get("channels", {}).get(self._channel, {}).get("mute")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mute the channel."""
        await self._async_set_mute(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmute the channel."""
        await self._async_set_mute(False)

    async def _async_set_mute(self, mute: bool) -> None:
        """Set mute state."""
        path = PATH_CHANNEL_MUTE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, mute)

            # Update coordinator data immediately
            if self.coordinator.data:
                self.coordinator.data["channels"][self._channel]["mute"] = mute
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set mute for channel %d: %s", self._channel, err)
            raise
