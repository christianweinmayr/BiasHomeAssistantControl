"""Select platform for Powersoft Bias integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.select import SelectEntity
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
    MAX_OUTPUT_EQ_BANDS,
    MAX_PRE_OUTPUT_EQ_BANDS,
    MAX_INPUT_EQ_BANDS,
    EQ_FILTER_TYPES,
    PATH_OUTPUT_IIR_TYPE,
    PATH_PRE_OUTPUT_IIR_TYPE,
    PATH_INPUT_ZONE_IIR_TYPE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bias select entities."""
    coordinator: BiasDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # Output IIR filter types (16 bands × 4 channels)
    for channel in range(MAX_CHANNELS):
        for band in range(MAX_OUTPUT_EQ_BANDS):
            entities.append(BiasOutputIIRTypeSelect(coordinator, entry, channel, band))

    # Pre-Output IIR filter types (8 bands × 4 channels)
    for channel in range(MAX_CHANNELS):
        for band in range(MAX_PRE_OUTPUT_EQ_BANDS):
            entities.append(BiasPreOutputIIRTypeSelect(coordinator, entry, channel, band))

    # Input Zone IIR filter types (7 bands × 4 channels)
    for channel in range(MAX_CHANNELS):
        for band in range(MAX_INPUT_EQ_BANDS):
            entities.append(BiasInputIIRTypeSelect(coordinator, entry, channel, band))

    async_add_entities(entities)


class BiasOutputIIRTypeSelect(CoordinatorEntity[BiasDataUpdateCoordinator], SelectEntity):
    """Select entity for output IIR filter type."""

    _attr_icon = "mdi:waveform"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
        band: int,
    ) -> None:
        """Initialize the filter type select."""
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_iir_{band}_type"
        self._attr_name = f"Output {channel + 1} EQ Band {band + 1} Type"
        self._attr_options = list(EQ_FILTER_TYPES.values())

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def current_option(self) -> str | None:
        """Return the current filter type."""
        if self.coordinator.data:
            type_value = self.coordinator.data.get("output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("type")
            if type_value is not None:
                return EQ_FILTER_TYPES.get(str(int(type_value)), "Peaking")
        return None

    async def async_select_option(self, option: str) -> None:
        """Set the filter type."""
        # Reverse lookup: option name -> type value
        type_value = next(
            (k for k, v in EQ_FILTER_TYPES.items() if v == option),
            "0"
        )

        path = PATH_OUTPUT_IIR_TYPE.format(channel=self._channel, band=self._band)

        try:
            await self.coordinator.client.write_value(path, int(type_value))

            # Update coordinator data immediately
            if self.coordinator.data:
                if "output_channels" not in self.coordinator.data:
                    self.coordinator.data["output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["output_channels"]:
                    self.coordinator.data["output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["output_channels"][str(self._channel)]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)] = {}

                self.coordinator.data["output_channels"][str(self._channel)]["iir"][str(self._band)]["type"] = int(type_value)
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error(
                "Failed to set output IIR type for channel %d band %d: %s",
                self._channel, self._band, err
            )
            raise


class BiasPreOutputIIRTypeSelect(CoordinatorEntity[BiasDataUpdateCoordinator], SelectEntity):
    """Select entity for pre-output IIR filter type."""

    _attr_icon = "mdi:waveform"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
        band: int,
    ) -> None:
        """Initialize the filter type select."""
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_pre_output_{channel}_iir_{band}_type"
        self._attr_name = f"Speaker {channel + 1} EQ Band {band + 1} Type"
        self._attr_options = list(EQ_FILTER_TYPES.values())

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def current_option(self) -> str | None:
        """Return the current filter type."""
        if self.coordinator.data:
            type_value = self.coordinator.data.get("pre_output_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("type")
            if type_value is not None:
                return EQ_FILTER_TYPES.get(str(int(type_value)), "Peaking")
        return None

    async def async_select_option(self, option: str) -> None:
        """Set the filter type."""
        type_value = next(
            (k for k, v in EQ_FILTER_TYPES.items() if v == option),
            "0"
        )

        path = PATH_PRE_OUTPUT_IIR_TYPE.format(channel=self._channel, band=self._band)

        try:
            await self.coordinator.client.write_value(path, int(type_value))

            # Update coordinator data immediately
            if self.coordinator.data:
                if "pre_output_channels" not in self.coordinator.data:
                    self.coordinator.data["pre_output_channels"] = {}
                if str(self._channel) not in self.coordinator.data["pre_output_channels"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["pre_output_channels"][str(self._channel)]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)] = {}

                self.coordinator.data["pre_output_channels"][str(self._channel)]["iir"][str(self._band)]["type"] = int(type_value)
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error(
                "Failed to set pre-output IIR type for channel %d band %d: %s",
                self._channel, self._band, err
            )
            raise


class BiasInputIIRTypeSelect(CoordinatorEntity[BiasDataUpdateCoordinator], SelectEntity):
    """Select entity for input IIR filter type."""

    _attr_icon = "mdi:waveform"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
        band: int,
    ) -> None:
        """Initialize the filter type select."""
        super().__init__(coordinator)
        self._channel = channel
        self._band = band
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_iir_{band}_type"
        self._attr_name = f"Input {channel + 1} EQ Band {band + 1} Type"
        self._attr_options = list(EQ_FILTER_TYPES.values())

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def current_option(self) -> str | None:
        """Return the current filter type."""
        if self.coordinator.data:
            type_value = self.coordinator.data.get("input_channels", {}).get(
                str(self._channel), {}
            ).get("iir", {}).get(str(self._band), {}).get("type")
            if type_value is not None:
                return EQ_FILTER_TYPES.get(str(int(type_value)), "Peaking")
        return None

    async def async_select_option(self, option: str) -> None:
        """Set the filter type."""
        type_value = next(
            (k for k, v in EQ_FILTER_TYPES.items() if v == option),
            "0"
        )

        path = PATH_INPUT_ZONE_IIR_TYPE.format(channel=self._channel, band=self._band)

        try:
            await self.coordinator.client.write_value(path, int(type_value))

            # Update coordinator data immediately
            if self.coordinator.data:
                if "input_channels" not in self.coordinator.data:
                    self.coordinator.data["input_channels"] = {}
                if str(self._channel) not in self.coordinator.data["input_channels"]:
                    self.coordinator.data["input_channels"][str(self._channel)] = {}
                if "iir" not in self.coordinator.data["input_channels"][str(self._channel)]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"] = {}
                if str(self._band) not in self.coordinator.data["input_channels"][str(self._channel)]["iir"]:
                    self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)] = {}

                self.coordinator.data["input_channels"][str(self._channel)]["iir"][str(self._band)]["type"] = int(type_value)
                self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error(
                "Failed to set input IIR type for channel %d band %d: %s",
                self._channel, self._band, err
            )
            raise
