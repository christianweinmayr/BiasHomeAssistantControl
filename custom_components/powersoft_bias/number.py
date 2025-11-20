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
    MAX_OUTPUT_EQ_BANDS,
    MAX_PRE_OUTPUT_EQ_BANDS,
    MAX_INPUT_EQ_BANDS,
    MAX_XOVER_BANDS,
    PATH_CHANNEL_GAIN,
    PATH_CHANNEL_OUT_DELAY_VALUE,
    PATH_INPUT_GAIN,
    PATH_INPUT_DELAY_VALUE,
    PATH_INPUT_SHADING_GAIN,
    # EQ paths
    PATH_OUTPUT_IIR_FC,
    PATH_OUTPUT_IIR_GAIN,
    PATH_OUTPUT_IIR_Q,
    PATH_OUTPUT_IIR_SLOPE,
    PATH_PRE_OUTPUT_IIR_FC,
    PATH_PRE_OUTPUT_IIR_GAIN,
    PATH_PRE_OUTPUT_IIR_Q,
    PATH_PRE_OUTPUT_IIR_SLOPE,
    PATH_INPUT_ZONE_IIR_FC,
    PATH_INPUT_ZONE_IIR_GAIN,
    PATH_INPUT_ZONE_IIR_Q,
    PATH_INPUT_ZONE_IIR_SLOPE,
    # Crossover paths
    PATH_XOVER_FC,
    PATH_XOVER_SLOPE,
    # Limiter paths
    PATH_LIMITER_CLIP_THRESHOLD,
    PATH_LIMITER_CLIP_ATTACK,
    PATH_LIMITER_CLIP_HOLD,
    PATH_LIMITER_CLIP_RELEASE,
    PATH_LIMITER_PEAK_THRESHOLD,
    PATH_LIMITER_PEAK_ATTACK,
    PATH_LIMITER_PEAK_HOLD,
    PATH_LIMITER_PEAK_RELEASE,
    PATH_LIMITER_VRMS_THRESHOLD,
    PATH_LIMITER_VRMS_ATTACK,
    PATH_LIMITER_VRMS_HOLD,
    PATH_LIMITER_VRMS_RELEASE,
    PATH_LIMITER_IRMS_THRESHOLD,
    PATH_LIMITER_IRMS_ATTACK,
    PATH_LIMITER_IRMS_HOLD,
    PATH_LIMITER_IRMS_RELEASE,
    PATH_LIMITER_CLAMP_THRESHOLD,
    PATH_LIMITER_CLAMP_ATTACK,
    PATH_LIMITER_CLAMP_HOLD,
    PATH_LIMITER_CLAMP_RELEASE,
    PATH_LIMITER_THERMAL_THRESHOLD,
    PATH_LIMITER_THERMAL_ATTACK,
    PATH_LIMITER_THERMAL_HOLD,
    PATH_LIMITER_THERMAL_RELEASE,
    PATH_LIMITER_TRUEPOWER_THRESHOLD,
    PATH_LIMITER_TRUEPOWER_ATTACK,
    PATH_LIMITER_TRUEPOWER_HOLD,
    PATH_LIMITER_TRUEPOWER_RELEASE,
    # Matrix paths
    PATH_MATRIX_IN_GAIN,
    PATH_MATRIX_CHANNEL_GAIN,
)

_LOGGER = logging.getLogger(__name__)

# Gain conversion constants
# The amplifier uses logarithmic dB scale
# Formula: dB = 20 * log10(linear)
# linear 1.0 = 0 dB (unity gain)
# linear 2.0 = +6.02 dB (double amplitude)
# linear 5.623 = +15 dB (verified maximum in Armonia)
# linear 0.001 = -60 dB (practical minimum)
GAIN_DB_MIN = -60.0
GAIN_DB_MAX = 15.0
GAIN_LINEAR_MIN = 0.001  # Avoid log(0), represents -60 dB
GAIN_LINEAR_MAX = 10.0  # Allow headroom beyond +15 dB (actual max ~5.62)


def linear_to_db(linear: float) -> float:
    """Convert linear gain to dB (-60 to +15).

    Uses logarithmic conversion: dB = 20 * log10(linear)
    """
    if linear <= GAIN_LINEAR_MIN:
        return GAIN_DB_MIN
    db = 20 * math.log10(linear)
    return max(GAIN_DB_MIN, min(GAIN_DB_MAX, db))


def db_to_linear(db: float) -> float:
    """Convert dB (-60 to +15) to linear gain.

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

    # v0.4.0 - Output IIR EQ parameters (first 8 bands per channel)
    for channel in range(MAX_CHANNELS):
        for band in range(8):
            entities.append(BiasOutputIIRFrequency(coordinator, entry, channel, band))
            entities.append(BiasOutputIIRGain(coordinator, entry, channel, band))
            entities.append(BiasOutputIIRQ(coordinator, entry, channel, band))

    # v0.4.0 - Pre-Output IIR EQ parameters (8 bands per channel)
    for channel in range(MAX_CHANNELS):
        for band in range(8):
            entities.append(BiasPreOutputIIRFrequency(coordinator, entry, channel, band))
            entities.append(BiasPreOutputIIRGain(coordinator, entry, channel, band))
            entities.append(BiasPreOutputIIRQ(coordinator, entry, channel, band))

    # v0.4.0 - Input IIR EQ parameters (7 bands per channel)
    for channel in range(MAX_CHANNELS):
        for band in range(7):
            entities.append(BiasInputIIRFrequency(coordinator, entry, channel, band))
            entities.append(BiasInputIIRGain(coordinator, entry, channel, band))
            entities.append(BiasInputIIRQ(coordinator, entry, channel, band))

    # v0.4.0 - Limiter thresholds (7 types × 4 channels)
    for channel in range(MAX_CHANNELS):
        entities.append(BiasClipLimiterThreshold(coordinator, entry, channel))
        entities.append(BiasPeakLimiterThreshold(coordinator, entry, channel))
        entities.append(BiasVRMSLimiterThreshold(coordinator, entry, channel))
        entities.append(BiasIRMSLimiterThreshold(coordinator, entry, channel))
        entities.append(BiasClampLimiterThreshold(coordinator, entry, channel))
        entities.append(BiasThermalLimiterThreshold(coordinator, entry, channel))
        entities.append(BiasTruePowerLimiterThreshold(coordinator, entry, channel))

    # v0.4.0 - Crossover controls (2 bands × 4 channels)
    for channel in range(MAX_CHANNELS):
        for band in range(MAX_XOVER_BANDS):
            entities.append(BiasCrossoverFrequency(coordinator, entry, channel, band))
            entities.append(BiasCrossoverSlope(coordinator, entry, channel, band))

    # v0.4.0 - Matrix mixer gains (4 inputs + 16 routing gains)
    for input_ch in range(MAX_CHANNELS):
        entities.append(BiasMatrixInputGain(coordinator, entry, input_ch))
    for channel in range(MAX_CHANNELS):
        for input_ch in range(MAX_CHANNELS):
            entities.append(BiasMatrixChannelGain(coordinator, entry, channel, input_ch))

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


# Note: Due to the large number of entities (~1000+), this is a simplified v0.4.0 implementation
# focusing on the most commonly used parameters. Full EQ/limiter parameter control can be
# added incrementally based on user needs.

# The setup function above registers all entities, but we're implementing
# representative base classes that can be extended.

# This file will be split into separate modules in a future refactor for maintainability.

_LOGGER.warning(
    "v0.4.0 entities loaded - EQ, Limiters, Crossovers, Matrix. "
    "Note: Some advanced parameters may not be fully implemented yet."
)


# =============================================================================
# v0.4.0 - EQ Number Controls (Frequency, Gain, Q)
# =============================================================================

class BiasOutputIIRFrequency(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Output IIR frequency control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 20.0
    _attr_native_max_value = 20000.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "Hz"
    _attr_icon = "mdi:sine-wave"

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_iir_{band}_fc"
        self._attr_name = f"Output {channel + 1} EQ Band {band + 1} Frequency"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("fc")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_OUTPUT_IIR_FC.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)]["fc"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set output IIR fc: %s", err)
            raise


class BiasOutputIIRGain(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Output IIR gain control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -15.0
    _attr_native_max_value = 15.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "dB"
    _attr_icon = "mdi:tune-vertical"

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_iir_{band}_gain"
        self._attr_name = f"Output {channel + 1} EQ Band {band + 1} Gain"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_OUTPUT_IIR_GAIN.format(channel=self._channel, band=self._band)
        linear_value = db_to_linear(value)
        try:
            await self.coordinator.client.write_value(path, linear_value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)]["gain"] = linear_value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set output IIR gain: %s", err)
            raise


class BiasOutputIIRQ(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Output IIR Q factor control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0.1
    _attr_native_max_value = 20.0
    _attr_native_step = 0.1
    _attr_icon = "mdi:sine-wave"

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_iir_{band}_q"
        self._attr_name = f"Output {channel + 1} EQ Band {band + 1} Q"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("q")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_OUTPUT_IIR_Q.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)]["q"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set output IIR Q: %s", err)
            raise


# Pre-Output and Input IIR classes follow the same pattern, abbreviated for file size
# They use the same structure but with different paths and data keys

class BiasPreOutputIIRFrequency(BiasOutputIIRFrequency):
    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator, entry, channel, band)
        self._attr_unique_id = f"{entry.entry_id}_pre_output_{channel}_iir_{band}_fc"
        self._attr_name = f"Pre-Output {channel + 1} EQ Band {band + 1} Frequency"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("fc")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_PRE_OUTPUT_IIR_FC.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)]["fc"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set pre-output IIR fc: %s", err)
            raise


class BiasPreOutputIIRGain(BiasOutputIIRGain):
    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator, entry, channel, band)
        self._attr_unique_id = f"{entry.entry_id}_pre_output_{channel}_iir_{band}_gain"
        self._attr_name = f"Pre-Output {channel + 1} EQ Band {band + 1} Gain"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_PRE_OUTPUT_IIR_GAIN.format(channel=self._channel, band=self._band)
        linear_value = db_to_linear(value)
        try:
            await self.coordinator.client.write_value(path, linear_value)
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)]["gain"] = linear_value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set pre-output IIR gain: %s", err)
            raise


class BiasPreOutputIIRQ(BiasOutputIIRQ):
    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator, entry, channel, band)
        self._attr_unique_id = f"{entry.entry_id}_pre_output_{channel}_iir_{band}_q"
        self._attr_name = f"Pre-Output {channel + 1} EQ Band {band + 1} Q"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("q")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_PRE_OUTPUT_IIR_Q.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)]["q"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set pre-output IIR Q: %s", err)
            raise


# Input IIR classes
class BiasInputIIRFrequency(BiasOutputIIRFrequency):
    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator, entry, channel, band)
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_iir_{band}_fc"
        self._attr_name = f"Input {channel + 1} EQ Band {band + 1} Frequency"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("fc")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_INPUT_ZONE_IIR_FC.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["input_channels"][str(self._channel)]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["input_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)]["fc"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set input IIR fc: %s", err)
            raise


class BiasInputIIRGain(BiasOutputIIRGain):
    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator, entry, channel, band)
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_iir_{band}_gain"
        self._attr_name = f"Input {channel + 1} EQ Band {band + 1} Gain"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("input_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_INPUT_ZONE_IIR_GAIN.format(channel=self._channel, band=self._band)
        linear_value = db_to_linear(value)
        try:
            await self.coordinator.client.write_value(path, linear_value)
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["input_channels"][str(self._channel)]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["input_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)]["gain"] = linear_value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set input IIR gain: %s", err)
            raise


class BiasInputIIRQ(BiasOutputIIRQ):
    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator, entry, channel, band)
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_iir_{band}_q"
        self._attr_name = f"Input {channel + 1} EQ Band {band + 1} Q"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("q")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_INPUT_ZONE_IIR_Q.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["input_channels"][str(self._channel)]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["input_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)]["q"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set input IIR Q: %s", err)
            raise


# =============================================================================
# v0.4.0 - Limiter Threshold Controls
# =============================================================================

class BiasClipLimiterThreshold(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Clip Limiter threshold control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = -20.0
    _attr_native_max_value = 0.0
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "dB"
    _attr_icon = "mdi:shield-half-full"

    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_clip_limiter_threshold"
        self._attr_name = f"Output {channel + 1} Clip Limiter Threshold"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("clip", {}).get("threshold")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_LIMITER_CLIP_THRESHOLD.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "clip" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clip"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clip"]["threshold"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set clip limiter threshold: %s", err)
            raise


# Remaining limiter thresholds follow same pattern - abbreviated for brevity
class BiasPeakLimiterThreshold(BiasClipLimiterThreshold):
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_peak_limiter_threshold"
        self._attr_name = f"Output {channel + 1} Peak Limiter Threshold"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("peak", {}).get("threshold")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_LIMITER_PEAK_THRESHOLD.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "peak" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["peak"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["peak"]["threshold"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set peak limiter threshold: %s", err)
            raise


class BiasVRMSLimiterThreshold(BiasClipLimiterThreshold):
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_vrms_limiter_threshold"
        self._attr_name = f"Output {channel + 1} VRMS Limiter Threshold"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 100.0
        self._attr_native_unit_of_measurement = "V"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("vrms", {}).get("threshold")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_LIMITER_VRMS_THRESHOLD.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "vrms" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["vrms"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["vrms"]["threshold"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set VRMS limiter threshold: %s", err)
            raise


class BiasIRMSLimiterThreshold(BiasClipLimiterThreshold):
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_irms_limiter_threshold"
        self._attr_name = f"Output {channel + 1} IRMS Limiter Threshold"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 50.0
        self._attr_native_unit_of_measurement = "A"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("irms", {}).get("threshold")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_LIMITER_IRMS_THRESHOLD.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "irms" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["irms"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["irms"]["threshold"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set IRMS limiter threshold: %s", err)
            raise


class BiasClampLimiterThreshold(BiasIRMSLimiterThreshold):
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_clamp_limiter_threshold"
        self._attr_name = f"Output {channel + 1} Clamp Threshold"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("clamp", {}).get("threshold")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_LIMITER_CLAMP_THRESHOLD.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "clamp" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clamp"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clamp"]["threshold"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set clamp limiter threshold: %s", err)
            raise


class BiasThermalLimiterThreshold(BiasClipLimiterThreshold):
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_thermal_limiter_threshold"
        self._attr_name = f"Output {channel + 1} Thermal Limiter Threshold"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 100.0
        self._attr_native_unit_of_measurement = "%"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("thermal", {}).get("threshold")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_LIMITER_THERMAL_THRESHOLD.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "thermal" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["thermal"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["thermal"]["threshold"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set thermal limiter threshold: %s", err)
            raise


class BiasTruePowerLimiterThreshold(BiasClipLimiterThreshold):
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_truepower_limiter_threshold"
        self._attr_name = f"Output {channel + 1} TruePower Limiter Threshold"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 5000.0
        self._attr_native_unit_of_measurement = "W"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("truepower", {}).get("threshold")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_LIMITER_TRUEPOWER_THRESHOLD.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "truepower" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["truepower"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["truepower"]["threshold"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set truepower limiter threshold: %s", err)
            raise


# =============================================================================
# v0.4.0 - Crossover Controls
# =============================================================================

class BiasCrossoverFrequency(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Crossover frequency control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 20.0
    _attr_native_max_value = 20000.0
    _attr_native_step = 1.0
    _attr_native_unit_of_measurement = "Hz"
    _attr_icon = "mdi:waveform"

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_xover_{band}_fc"
        self._attr_name = f"Output {channel + 1} Crossover Band {band + 1} Frequency"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("crossover", {}).get(str(self._band), {}).get("fc")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_XOVER_FC.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "crossover" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"][str(self._band)] = {}
                self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"][str(self._band)]["fc"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set crossover frequency: %s", err)
            raise


class BiasCrossoverSlope(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Crossover slope control."""

    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 6.0
    _attr_native_max_value = 48.0
    _attr_native_step = 6.0
    _attr_native_unit_of_measurement = "dB/oct"
    _attr_icon = "mdi:slope-uphill"

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_xover_{band}_slope"
        self._attr_name = f"Output {channel + 1} Crossover Band {band + 1} Slope"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("crossover", {}).get(str(self._band), {}).get("slope")
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_XOVER_SLOPE.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, value)
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "crossover" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"][str(self._band)] = {}
                self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"][str(self._band)]["slope"] = value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set crossover slope: %s", err)
            raise


# =============================================================================
# v0.4.0 - Matrix Mixer Gain Controls
# =============================================================================

class BiasMatrixInputGain(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Matrix mixer input gain control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -60.0
    _attr_native_max_value = 15.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dB"
    _attr_icon = "mdi:volume-high"

    def __init__(self, coordinator, entry, input_ch: int) -> None:
        super().__init__(coordinator)
        self._input_ch = input_ch
        self._attr_unique_id = f"{entry.entry_id}_matrix_input_{input_ch}_gain"
        self._attr_name = f"Matrix Input {input_ch + 1} Gain"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("matrix", {}).get("inputs", {}).get(str(self._input_ch), {}).get("gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_MATRIX_IN_GAIN.format(input=self._input_ch)
        linear_value = db_to_linear(value)
        try:
            await self.coordinator.client.write_value(path, linear_value)
            if self.coordinator.data:
                if "matrix" not in self.coordinator.data:
                    self.coordinator.data["matrix"] = {}
                if "inputs" not in self.coordinator.data["matrix"]:
                    self.coordinator.data["matrix"]["inputs"] = {}
                if str(self._input_ch) not in self.coordinator.data["matrix"]["inputs"]:
                    self.coordinator.data["matrix"]["inputs"][str(self._input_ch)] = {}
                self.coordinator.data["matrix"]["inputs"][str(self._input_ch)]["gain"] = linear_value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set matrix input gain: %s", err)
            raise


class BiasMatrixChannelGain(CoordinatorEntity[BiasDataUpdateCoordinator], NumberEntity):
    """Matrix mixer channel routing gain control."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = -60.0
    _attr_native_max_value = 15.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "dB"
    _attr_icon = "mdi:volume-high"

    def __init__(self, coordinator, entry, channel: int, input_ch: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._input_ch = input_ch
        self._attr_unique_id = f"{entry.entry_id}_matrix_ch{channel}_in{input_ch}_gain"
        self._attr_name = f"Matrix Output {channel + 1} Input {input_ch + 1} Gain"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            linear_gain = self.coordinator.data.get("matrix", {}).get("channels", {}).get(
                str(self._channel), {}
            ).get("routing", {}).get(str(self._input_ch), {}).get("gain")
            if linear_gain is not None:
                return round(linear_to_db(linear_gain), 1)
        return None

    async def async_set_native_value(self, value: float) -> None:
        path = PATH_MATRIX_CHANNEL_GAIN.format(channel=self._channel, input=self._input_ch)
        linear_value = db_to_linear(value)
        try:
            await self.coordinator.client.write_value(path, linear_value)
            if self.coordinator.data:
                if "matrix" not in self.coordinator.data:
                    self.coordinator.data["matrix"] = {}
                if "channels" not in self.coordinator.data["matrix"]:
                    self.coordinator.data["matrix"]["channels"] = {}
                if str(self._channel) not in self.coordinator.data["matrix"]["channels"]:
                    self.coordinator.data["matrix"]["channels"][str(self._channel)] = {}
                if "routing" not in self.coordinator.data["matrix"]["channels"][str(self._channel)]:
                    self.coordinator.data["matrix"]["channels"][str(self._channel)]["routing"] = {}
                if str(self._input_ch) not in self.coordinator.data["matrix"]["channels"][str(self._channel)]["routing"]:
                    self.coordinator.data["matrix"]["channels"][str(self._channel)]["routing"][str(self._input_ch)] = {}
                self.coordinator.data["matrix"]["channels"][str(self._channel)]["routing"][str(self._input_ch)]["gain"] = linear_value
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set matrix channel gain: %s", err)
            raise

