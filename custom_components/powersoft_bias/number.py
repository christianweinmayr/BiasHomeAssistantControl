"""Number platform for Powersoft Bias integration."""
from __future__ import annotations

import logging
import math
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
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
    PATH_CHANNEL_GAIN,
    PATH_CHANNEL_OUT_DELAY_VALUE,
    PATH_INPUT_GAIN,
    PATH_INPUT_DELAY_VALUE,
    PATH_INPUT_SHADING_GAIN,
)

_LOGGER = logging.getLogger(__name__)

# Gain conversion constants
# The amplifier's linear range 0.0-2.0 maps logarithmically to dB
# Formula: dB = 20 * log10(linear)
# linear 1.0 = 0 dB (unity gain)
# linear 2.0 = +6.02 dB (double amplitude)
# linear 0.001 = -60 dB (practical minimum)
GAIN_DB_MIN = -60.0
GAIN_DB_MAX = 6.0
GAIN_LINEAR_MIN = 0.001  # Avoid log(0), represents -60 dB
GAIN_LINEAR_MAX = 2.0


def linear_to_db(linear: float) -> float:
    """Convert linear gain (0.0-2.0) to dB (-60 to +6).

    Uses logarithmic conversion: dB = 20 * log10(linear)
    """
    if linear <= GAIN_LINEAR_MIN:
        return GAIN_DB_MIN
    db = 20 * math.log10(linear)
    return max(GAIN_DB_MIN, min(GAIN_DB_MAX, db))


def db_to_linear(db: float) -> float:
    """Convert dB (-60 to +6) to linear gain (0.0-2.0).

    Uses inverse logarithmic conversion: linear = 10^(dB/20)
    """
    if db <= GAIN_DB_MIN:
        return GAIN_LINEAR_MIN
    linear = math.pow(10, db / 20)
    return max(0.0, min(GAIN_LINEAR_MAX, linear))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bias number entities."""
    coordinator: BiasDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Output channel controls
    for channel in range(MAX_CHANNELS):
        entities.append(BiasOutputGain(coordinator, entry, channel))
        entities.append(BiasOutputDelay(coordinator, entry, channel))

    # Input channel controls
    for channel in range(MAX_CHANNELS):
        entities.append(BiasInputGain(coordinator, entry, channel))
        entities.append(BiasInputShadingGain(coordinator, entry, channel))
        entities.append(BiasInputDelay(coordinator, entry, channel))

    async_add_entities(entities)


# =============================================================================
# Output Channel Controls
# =============================================================================

class BiasOutputGain(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Representation of a Bias output channel gain control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = GAIN_DB_MIN
    _attr_native_max_value = GAIN_DB_MAX
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dB"
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
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_gain"
        self._attr_name = f"Output {channel + 1} Gain"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current gain value in dB."""
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("output_channels", {}).get(str(self._channel), {}).get("gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new gain value from dB."""
        path = PATH_CHANNEL_GAIN.format(channel=self._channel)

        # Convert dB to linear for API
        linear_value = db_to_linear(value)

        try:
            await self.coordinator.client.write_value(path, linear_value)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["gain"] = linear_value
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set output gain for channel %d: %s", self._channel, err)
            raise


class BiasOutputDelay(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Representation of a Bias output channel delay control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0.0
    _attr_native_max_value = 1000.0  # milliseconds
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "ms"
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the delay control."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_delay"
        self._attr_name = f"Output {channel + 1} Delay"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current delay value."""
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(str(self._channel), {}).get("delay")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new delay value."""
        path = PATH_CHANNEL_OUT_DELAY_VALUE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, value)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["delay"] = value
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set output delay for channel %d: %s", self._channel, err)
            raise


# =============================================================================
# Input Channel Controls
# =============================================================================

class BiasInputGain(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Representation of a Bias input channel gain control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = GAIN_DB_MIN
    _attr_native_max_value = GAIN_DB_MAX
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dB"
    _attr_icon = "mdi:volume-high"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the input gain control."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_gain"
        self._attr_name = f"Input {channel + 1} Gain"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current input gain value in dB."""
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new input gain value from dB."""
        path = PATH_INPUT_GAIN.format(channel=self._channel)

        # Convert dB to linear for API
        linear_value = db_to_linear(value)

        try:
            await self.coordinator.client.write_value(path, linear_value)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["gain"] = linear_value
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set input gain for channel %d: %s", self._channel, err)
            raise


class BiasInputShadingGain(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Representation of a Bias input channel shading gain control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = GAIN_DB_MIN
    _attr_native_max_value = GAIN_DB_MAX
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dB"
    _attr_icon = "mdi:tune-vertical"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the shading gain control."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_shading_gain"
        self._attr_name = f"Input {channel + 1} Shading Gain"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current shading gain value in dB."""
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("shading_gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new shading gain value from dB."""
        path = PATH_INPUT_SHADING_GAIN.format(channel=self._channel)

        # Convert dB to linear for API
        linear_value = db_to_linear(value)

        try:
            await self.coordinator.client.write_value(path, linear_value)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["shading_gain"] = linear_value
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set shading gain for input %d: %s", self._channel, err)
            raise


class BiasInputDelay(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Representation of a Bias input channel delay control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0.0
    _attr_native_max_value = 1000.0  # milliseconds
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "ms"
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the input delay control."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_delay"
        self._attr_name = f"Input {channel + 1} Delay"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current input delay value."""
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("delay")
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new input delay value."""
        path = PATH_INPUT_DELAY_VALUE.format(channel=self._channel)

        try:
            await self.coordinator.client.write_value(path, value)

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["delay"] = value
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error("Failed to set input delay for channel %d: %s", self._channel, err)
            raise
