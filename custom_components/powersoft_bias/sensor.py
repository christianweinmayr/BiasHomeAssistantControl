"""Sensor platform for Powersoft Bias integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
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
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bias sensor entities."""
    coordinator: BiasDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = []

    # System monitoring sensors
    entities.append(BiasStandbySensor(coordinator, entry))
    entities.append(BiasFirmwareVersionSensor(coordinator, entry))
    entities.append(BiasModelNameSensor(coordinator, entry))
    entities.append(BiasSerialNumberSensor(coordinator, entry))

    # Debug sensors - raw gain values
    for channel in range(MAX_CHANNELS):
        entities.append(BiasOutputGainRawSensor(coordinator, entry, channel))
        entities.append(BiasInputGainRawSensor(coordinator, entry, channel))
        entities.append(BiasInputShadingGainRawSensor(coordinator, entry, channel))

    async_add_entities(entities)


# =============================================================================
# System Monitoring Sensors
# =============================================================================

class BiasStandbySensor(CoordinatorEntity[BiasDataUpdateCoordinator], SensorEntity):
    """Representation of amplifier standby state sensor."""

    _attr_icon = "mdi:power-standby"
    _attr_device_class = None
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the standby sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_standby"
        self._attr_name = "Standby"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> str | None:
        """Return the standby state."""
        if self.coordinator.data:
            standby = self.coordinator.data.get("standby")
            if standby is not None:
                return "On" if standby else "Off"
        return None


class BiasFirmwareVersionSensor(CoordinatorEntity[BiasDataUpdateCoordinator], SensorEntity):
    """Representation of firmware version sensor."""

    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the firmware version sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_firmware_version"
        self._attr_name = "Firmware Version"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> str | None:
        """Return the firmware version."""
        if self.coordinator.data:
            return self.coordinator.data.get("device_info", {}).get("firmware_version")
        return None


class BiasModelNameSensor(CoordinatorEntity[BiasDataUpdateCoordinator], SensorEntity):
    """Representation of model name sensor."""

    _attr_icon = "mdi:information-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the model name sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_model_name"
        self._attr_name = "Model Name"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> str | None:
        """Return the model name."""
        if self.coordinator.data:
            return self.coordinator.data.get("device_info", {}).get("model_name")
        return None


class BiasSerialNumberSensor(CoordinatorEntity[BiasDataUpdateCoordinator], SensorEntity):
    """Representation of serial number sensor."""

    _attr_icon = "mdi:barcode"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the serial number sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_serial_number"
        self._attr_name = "Serial Number"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> str | None:
        """Return the serial number."""
        if self.coordinator.data:
            return self.coordinator.data.get("device_info", {}).get("serial_number")
        return None


# =============================================================================
# Debug Sensors - Raw Gain Values
# =============================================================================

class BiasOutputGainRawSensor(CoordinatorEntity[BiasDataUpdateCoordinator], SensorEntity):
    """Debug sensor showing raw linear output gain value."""

    _attr_icon = "mdi:bug"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the debug sensor."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_output_{channel}_gain_raw"
        self._attr_name = f"Output {channel + 1} Gain (Raw Linear)"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the raw linear gain value."""
        if self.coordinator.data:
            return self.coordinator.data.get("output_channels", {}).get(str(self._channel), {}).get("gain")
        return None


class BiasInputGainRawSensor(CoordinatorEntity[BiasDataUpdateCoordinator], SensorEntity):
    """Debug sensor showing raw linear input gain value."""

    _attr_icon = "mdi:bug"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the debug sensor."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_gain_raw"
        self._attr_name = f"Input {channel + 1} Gain (Raw Linear)"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the raw linear gain value."""
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("gain")
        return None


class BiasInputShadingGainRawSensor(CoordinatorEntity[BiasDataUpdateCoordinator], SensorEntity):
    """Debug sensor showing raw linear input shading gain value."""

    _attr_icon = "mdi:bug"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: BiasDataUpdateCoordinator,
        entry: ConfigEntry,
        channel: int,
    ) -> None:
        """Initialize the debug sensor."""
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry.entry_id}_input_{channel}_shading_gain_raw"
        self._attr_name = f"Input {channel + 1} Shading Gain (Raw Linear)"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> float | None:
        """Return the raw linear shading gain value."""
        if self.coordinator.data:
            return self.coordinator.data.get("input_channels", {}).get(str(self._channel), {}).get("shading_gain")
        return None
