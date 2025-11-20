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
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    MAX_CHANNELS,
    PATH_CHANNEL_ENABLE,
    PATH_CHANNEL_MUTE,
    PATH_CHANNEL_POLARITY,
    PATH_CHANNEL_OUT_DELAY_ENABLE,
    PATH_INPUT_ENABLE,
    PATH_INPUT_MUTE,
    PATH_INPUT_POLARITY,
    PATH_INPUT_DELAY_ENABLE,
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

    # Output channel controls
    for channel in range(MAX_CHANNELS):
        entities.append(BiasOutputMute(coordinator, entry, channel))
        entities.append(BiasOutputEnable(coordinator, entry, channel))
        entities.append(BiasOutputPolarity(coordinator, entry, channel))
        entities.append(BiasOutputDelayEnable(coordinator, entry, channel))

    # Input channel controls
    for channel in range(MAX_CHANNELS):
        entities.append(BiasInputMute(coordinator, entry, channel))
        entities.append(BiasInputEnable(coordinator, entry, channel))
        entities.append(BiasInputPolarity(coordinator, entry, channel))
        entities.append(BiasInputDelayEnable(coordinator, entry, channel))

    async_add_entities(entities)


# =============================================================================
# Output Channel Controls
# =============================================================================

class BiasOutputMute(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias output channel mute switch."""

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
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_mute"
        self._attr_name = f"Output {channel + 1} Mute"

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
            return self.coordinator.data.get("output_channels", {}).get(str(self._channel), {}).get("mute")
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
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["mute"] = mute
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set output mute for channel %d: %s", self._channel, err)
            raise


class BiasOutputEnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias output channel enable switch."""

    _attr_icon = "mdi:power"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the enable switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_enable"
        self._attr_name = f"Output {channel + 1} Enable"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the channel is enabled."""
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(str(self._channel), {}).get("enable")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the channel."""
        await self._async_set_enable(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the channel."""
        await self._async_set_enable(False)

    async def _async_set_enable(self, enable: bool) -> None:
        """Set enable state."""
        path = PATH_CHANNEL_ENABLE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, enable)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["enable"] = enable
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set output enable for channel %d: %s", self._channel, err)
            raise


class BiasOutputPolarity(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias output channel polarity (phase inversion) switch."""

    _attr_icon = "mdi:sine-wave"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the polarity switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_polarity"
        self._attr_name = f"Output {channel + 1} Polarity Invert"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if polarity is inverted."""
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(str(self._channel), {}).get("polarity")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Invert polarity."""
        await self._async_set_polarity(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Normal polarity."""
        await self._async_set_polarity(False)

    async def _async_set_polarity(self, inverted: bool) -> None:
        """Set polarity state."""
        path = PATH_CHANNEL_POLARITY.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, inverted)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["polarity"] = inverted
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set output polarity for channel %d: %s", self._channel, err)
            raise


class BiasOutputDelayEnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias output channel delay enable switch."""

    _attr_icon = "mdi:timer"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the delay enable switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_delay_enable"
        self._attr_name = f"Output {channel + 1} Delay Enable"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if delay is enabled."""
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(str(self._channel), {}).get("delay_enable")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable delay."""
        await self._async_set_delay_enable(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable delay."""
        await self._async_set_delay_enable(False)

    async def _async_set_delay_enable(self, enable: bool) -> None:
        """Set delay enable state."""
        path = PATH_CHANNEL_OUT_DELAY_ENABLE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, enable)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["delay_enable"] = enable
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set output delay enable for channel %d: %s", self._channel, err)
            raise


# =============================================================================
# Input Channel Controls
# =============================================================================

class BiasInputMute(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias input channel mute switch."""

    _attr_icon = "mdi:microphone-off"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the input mute switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_mute"
        self._attr_name = f"Input {channel + 1} Mute"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the input is muted."""
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("mute")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Mute the input."""
        await self._async_set_mute(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Unmute the input."""
        await self._async_set_mute(False)

    async def _async_set_mute(self, mute: bool) -> None:
        """Set mute state."""
        path = PATH_INPUT_MUTE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, mute)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["mute"] = mute
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set input mute for channel %d: %s", self._channel, err)
            raise


class BiasInputEnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias input channel enable switch."""

    _attr_icon = "mdi:power"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the input enable switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_enable"
        self._attr_name = f"Input {channel + 1} Enable"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the input is enabled."""
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("enable")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the input."""
        await self._async_set_enable(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the input."""
        await self._async_set_enable(False)

    async def _async_set_enable(self, enable: bool) -> None:
        """Set enable state."""
        path = PATH_INPUT_ENABLE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, enable)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["enable"] = enable
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set input enable for channel %d: %s", self._channel, err)
            raise


class BiasInputPolarity(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias input channel polarity (phase inversion) switch."""

    _attr_icon = "mdi:sine-wave"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the input polarity switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_polarity"
        self._attr_name = f"Input {channel + 1} Polarity Invert"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if polarity is inverted."""
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("polarity")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Invert polarity."""
        await self._async_set_polarity(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Normal polarity."""
        await self._async_set_polarity(False)

    async def _async_set_polarity(self, inverted: bool) -> None:
        """Set polarity state."""
        path = PATH_INPUT_POLARITY.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, inverted)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["polarity"] = inverted
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set input polarity for channel %d: %s", self._channel, err)
            raise


class BiasInputDelayEnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Representation of a Bias input channel delay enable switch."""

    _attr_icon = "mdi:timer"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the input delay enable switch."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_delay_enable"
        self._attr_name = f"Input {channel + 1} Delay Enable"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if input delay is enabled."""
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("delay_enable")
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable input delay."""
        await self._async_set_delay_enable(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable input delay."""
        await self._async_set_delay_enable(False)

    async def _async_set_delay_enable(self, enable: bool) -> None:
        """Set delay enable state."""
        path = PATH_INPUT_DELAY_ENABLE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, enable)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["delay_enable"] = enable
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set input delay enable for channel %d: %s", self._channel, err)
            raise
