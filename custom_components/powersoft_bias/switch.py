"""Switch platform for Powersoft Bias integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import BiasDataUpdateCoordinator
from .const import (
    COORDINATOR,
    DOMAIN,
    MANUFACTURER,
    MAX_CHANNELS,
    MAX_XOVER_BANDS,
    PATH_CHANNEL_ENABLE,
    PATH_CHANNEL_MUTE,
    PATH_CHANNEL_POLARITY,
    PATH_CHANNEL_OUT_DELAY_ENABLE,
    PATH_INPUT_ENABLE,
    PATH_INPUT_MUTE,
    PATH_INPUT_POLARITY,
    PATH_INPUT_DELAY_ENABLE,
    # EQ enables
    PATH_OUTPUT_IIR_ENABLE,
    PATH_PRE_OUTPUT_IIR_ENABLE,
    PATH_INPUT_ZONE_IIR_ENABLE,
    # Limiter enables
    PATH_LIMITER_CLIP_ENABLE,
    PATH_LIMITER_PEAK_ENABLE,
    PATH_LIMITER_VRMS_ENABLE,
    PATH_LIMITER_IRMS_ENABLE,
    PATH_LIMITER_CLAMP_ENABLE,
    PATH_LIMITER_THERMAL_ENABLE,
    PATH_LIMITER_TRUEPOWER_ENABLE,
    # Crossover enables
    PATH_XOVER_ENABLE,
    # Matrix mutes
    PATH_MATRIX_IN_MUTE,
    PATH_MATRIX_CHANNEL_MUTE,
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

    # v0.4.0 - Output IIR EQ enables (first 8 bands per channel)
    for channel in range(MAX_CHANNELS):
        for band in range(8):
            entities.append(BiasOutputIIREnable(coordinator, entry, channel, band))

    # v0.4.0 - Pre-Output IIR EQ enables (8 bands per channel)
    for channel in range(MAX_CHANNELS):
        for band in range(8):
            entities.append(BiasPreOutputIIREnable(coordinator, entry, channel, band))

    # v0.4.0 - Input IIR EQ enables (7 bands per channel)
    for channel in range(MAX_CHANNELS):
        for band in range(7):
            entities.append(BiasInputIIREnable(coordinator, entry, channel, band))

    # v0.4.0 - Limiter enables (7 types × 4 channels = 28)
    for channel in range(MAX_CHANNELS):
        entities.append(BiasClipLimiterEnable(coordinator, entry, channel))
        entities.append(BiasPeakLimiterEnable(coordinator, entry, channel))
        entities.append(BiasVRMSLimiterEnable(coordinator, entry, channel))
        entities.append(BiasIRMSLimiterEnable(coordinator, entry, channel))
        entities.append(BiasClampLimiterEnable(coordinator, entry, channel))
        entities.append(BiasThermalLimiterEnable(coordinator, entry, channel))
        entities.append(BiasTruePowerLimiterEnable(coordinator, entry, channel))

    # v0.4.0 - Crossover enables (2 bands × 4 channels = 8)
    for channel in range(MAX_CHANNELS):
        for band in range(MAX_XOVER_BANDS):
            entities.append(BiasCrossoverEnable(coordinator, entry, channel, band))

    # v0.4.0 - Matrix mixer mutes (4 inputs + 16 routing points)
    for input_ch in range(MAX_CHANNELS):
        entities.append(BiasMatrixInputMute(coordinator, entry, input_ch))
    for channel in range(MAX_CHANNELS):
        for input_ch in range(MAX_CHANNELS):
            entities.append(BiasMatrixChannelMute(coordinator, entry, channel, input_ch))

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
    _attr_entity_category = EntityCategory.CONFIG

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
    _attr_entity_category = EntityCategory.CONFIG

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
    _attr_entity_category = EntityCategory.CONFIG

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
    _attr_entity_category = EntityCategory.CONFIG

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
    _attr_entity_category = EntityCategory.CONFIG

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
    _attr_entity_category = EntityCategory.CONFIG

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


# =============================================================================
# v0.4.0 - EQ Enable Switches
# =============================================================================

class BiasOutputIIREnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Output IIR EQ band enable switch."""

    _attr_icon = "mdi:equalizer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_iir_{band}_enable"
        self._attr_name = f"Output {channel + 1} EQ Band {band + 1} Enable"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("enable")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        path = PATH_OUTPUT_IIR_ENABLE.format(channel=self._channel, band=self._band)
        await self._set_state(path, True)

    async def async_turn_off(self, **kwargs) -> None:
        path = PATH_OUTPUT_IIR_ENABLE.format(channel=self._channel, band=self._band)
        await self._set_state(path, False)

    async def _set_state(self, path: str, state: bool) -> None:
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set output IIR enable for channel %d band %d: %s", self._channel, self._band, err)
            raise


class BiasPreOutputIIREnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Pre-Output IIR EQ band enable switch."""

    _attr_icon = "mdi:equalizer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_pre_output_{channel}_iir_{band}_enable"
        self._attr_name = f"Pre-Output {channel + 1} EQ Band {band + 1} Enable"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("enable")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        path = PATH_PRE_OUTPUT_IIR_ENABLE.format(channel=self._channel, band=self._band)
        await self._set_state(path, True)

    async def async_turn_off(self, **kwargs) -> None:
        path = PATH_PRE_OUTPUT_IIR_ENABLE.format(channel=self._channel, band=self._band)
        await self._set_state(path, False)

    async def _set_state(self, path: str, state: bool) -> None:
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set pre-output IIR enable for channel %d band %d: %s", self._channel, self._band, err)
            raise


class BiasInputIIREnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Input IIR EQ band enable switch."""

    _attr_icon = "mdi:equalizer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_iir_{band}_enable"
        self._attr_name = f"Input {channel + 1} EQ Band {band + 1} Enable"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("enable")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        path = PATH_INPUT_ZONE_IIR_ENABLE.format(channel=self._channel, band=self._band)
        await self._set_state(path, True)

    async def async_turn_off(self, **kwargs) -> None:
        path = PATH_INPUT_ZONE_IIR_ENABLE.format(channel=self._channel, band=self._band)
        await self._set_state(path, False)

    async def _set_state(self, path: str, state: bool) -> None:
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["input_channels"][str(self._channel)]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["input_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)] = {}
                self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set input IIR enable for channel %d band %d: %s", self._channel, self._band, err)
            raise


# =============================================================================
# v0.4.0 - Limiter Enable Switches
# =============================================================================

class BiasClipLimiterEnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Clip Limiter enable switch."""

    _attr_icon = "mdi:shield-half-full"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_clip_limiter_enable"
        self._attr_name = f"Output {channel + 1} Clip Limiter"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("clip", {}).get("enable")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        path = PATH_LIMITER_CLIP_ENABLE.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "clip" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clip"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clip"]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set clip limiter enable for channel %d: %s", self._channel, err)
            raise


# Similar pattern for remaining limiters - abbreviated for file size
class BiasPeakLimiterEnable(BiasClipLimiterEnable):
    """Peak Limiter enable switch."""
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_peak_limiter_enable"
        self._attr_name = f"Output {channel + 1} Peak Limiter"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("peak", {}).get("enable")
        return None

    async def _set_state(self, state: bool) -> None:
        path = PATH_LIMITER_PEAK_ENABLE.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "peak" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["peak"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["peak"]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set peak limiter enable for channel %d: %s", self._channel, err)
            raise


class BiasVRMSLimiterEnable(BiasClipLimiterEnable):
    """Voltage RMS Limiter enable switch."""
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_vrms_limiter_enable"
        self._attr_name = f"Output {channel + 1} Voltage RMS Limiter"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("vrms", {}).get("enable")
        return None

    async def _set_state(self, state: bool) -> None:
        path = PATH_LIMITER_VRMS_ENABLE.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "vrms" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["vrms"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["vrms"]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set VRMS limiter enable for channel %d: %s", self._channel, err)
            raise


class BiasIRMSLimiterEnable(BiasClipLimiterEnable):
    """Current RMS Limiter enable switch."""
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_irms_limiter_enable"
        self._attr_name = f"Output {channel + 1} Current RMS Limiter"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("irms", {}).get("enable")
        return None

    async def _set_state(self, state: bool) -> None:
        path = PATH_LIMITER_IRMS_ENABLE.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "irms" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["irms"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["irms"]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set IRMS limiter enable for channel %d: %s", self._channel, err)
            raise


class BiasClampLimiterEnable(BiasClipLimiterEnable):
    """Current Clamp enable switch."""
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_clamp_limiter_enable"
        self._attr_name = f"Output {channel + 1} Current Clamp"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("clamp", {}).get("enable")
        return None

    async def _set_state(self, state: bool) -> None:
        path = PATH_LIMITER_CLAMP_ENABLE.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "clamp" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clamp"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["clamp"]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set clamp limiter enable for channel %d: %s", self._channel, err)
            raise


class BiasThermalLimiterEnable(BiasClipLimiterEnable):
    """Thermal Limiter enable switch."""
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_thermal_limiter_enable"
        self._attr_name = f"Output {channel + 1} Thermal Limiter"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("thermal", {}).get("enable")
        return None

    async def _set_state(self, state: bool) -> None:
        path = PATH_LIMITER_THERMAL_ENABLE.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "thermal" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["thermal"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["thermal"]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set thermal limiter enable for channel %d: %s", self._channel, err)
            raise


class BiasTruePowerLimiterEnable(BiasClipLimiterEnable):
    """TruePower Limiter enable switch."""
    def __init__(self, coordinator, entry, channel: int) -> None:
        super().__init__(coordinator, entry, channel)
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_truepower_limiter_enable"
        self._attr_name = f"Output {channel + 1} TruePower Limiter"

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("limiters", {}).get("truepower", {}).get("enable")
        return None

    async def _set_state(self, state: bool) -> None:
        path = PATH_LIMITER_TRUEPOWER_ENABLE.format(channel=self._channel)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "limiters" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"] = {}
                if "truepower" not in self.coordinator.data["output_channels"][str(self._channel)]["limiters"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["truepower"] = {}
                self.coordinator.data["output_channels"][str(self._channel)]["limiters"]["truepower"]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set truepower limiter enable for channel %d: %s", self._channel, err)
            raise


# =============================================================================
# v0.4.0 - Crossover Enable Switches
# =============================================================================

class BiasCrossoverEnable(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Crossover band enable switch."""

    _attr_icon = "mdi:waveform"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, channel: int, band: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_xover_{band}_enable"
        self._attr_name = f"Output {channel + 1} Crossover Band {band + 1}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("crossover", {}).get(str(self._band), {}).get("enable")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        path = PATH_XOVER_ENABLE.format(channel=self._channel, band=self._band)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "crossover" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"][str(self._band)] = {}
                self.coordinator.data["pre_output_channels"][str(self._channel)]["crossover"][str(self._band)]["enable"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set crossover enable for channel %d band %d: %s", self._channel, self._band, err)
            raise


# =============================================================================
# v0.4.0 - Matrix Mixer Mute Switches
# =============================================================================

class BiasMatrixInputMute(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Matrix mixer input mute switch."""

    _attr_icon = "mdi:volume-mute"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, input_ch: int) -> None:
        super().__init__(coordinator)
        self._input_ch = input_ch
        self._attr_unique_id = f"{entry.entry_id}_matrix_input_{input_ch}_mute"
        self._attr_name = f"Matrix Input {input_ch + 1} Mute"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("matrix", {}).get("inputs", {}).get(str(self._input_ch), {}).get("mute")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        path = PATH_MATRIX_IN_MUTE.format(input=self._input_ch)
        try:
            await self.coordinator.client.write_value(path, state)
            if self.coordinator.data:
                if "matrix" not in self.coordinator.data:
                    self.coordinator.data["matrix"] = {}
                if "inputs" not in self.coordinator.data["matrix"]:
                    self.coordinator.data["matrix"]["inputs"] = {}
                if str(self._input_ch) not in self.coordinator.data["matrix"]["inputs"]:
                    self.coordinator.data["matrix"]["inputs"][str(self._input_ch)] = {}
                self.coordinator.data["matrix"]["inputs"][str(self._input_ch)]["mute"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set matrix input mute for input %d: %s", self._input_ch, err)
            raise


class BiasMatrixChannelMute(CoordinatorEntity[BiasDataUpdateCoordinator], SwitchEntity):
    """Matrix mixer channel routing mute switch."""

    _attr_icon = "mdi:volume-mute"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, entry, channel: int, input_ch: int) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._input_ch = input_ch
        self._attr_unique_id = f"{entry.entry_id}_matrix_ch{channel}_in{input_ch}_mute"
        self._attr_name = f"Matrix Output {channel + 1} Input {input_ch + 1} Mute"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            return self.coordinator.data.get("matrix", {}).get("channels", {}).get(
                str(self._channel), {}
            ).get("routing", {}).get(str(self._input_ch), {}).get("mute")
        return None

    async def async_turn_on(self, **kwargs) -> None:
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        path = PATH_MATRIX_CHANNEL_MUTE.format(channel=self._channel, input=self._input_ch)
        try:
            await self.coordinator.client.write_value(path, state)
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
                self.coordinator.data["matrix"]["channels"][str(self._channel)]["routing"][str(self._input_ch)]["mute"] = state
                self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Failed to set matrix channel mute for channel %d input %d: %s", self._channel, self._input_ch, err)
            raise
