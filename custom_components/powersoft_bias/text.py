"""Text platform for Powersoft Bias integration - Preset renaming."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    MANUFACTURER,
    SCENE_MANAGER,
)
from .scene_manager import SceneManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bias text entities."""
    scene_manager: SceneManager = hass.data[DOMAIN][entry.entry_id][SCENE_MANAGER]

    entities = []

    # Create text entity for each preset
    scenes = await scene_manager.async_get_all_scenes()
    for scene in scenes:
        entities.append(BiasPresetNameText(hass, entry, scene_manager, scene))

    async_add_entities(entities)


class BiasPresetNameText(TextEntity):
    """Text entity to rename a preset."""

    _attr_icon = "mdi:rename-box"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = "text"
    _attr_native_min = 1
    _attr_native_max = 100
    _attr_pattern = None

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        scene_manager: SceneManager,
        scene: dict[str, Any],
    ) -> None:
        """Initialize the preset name text entity."""
        self._hass = hass
        self._entry = entry
        self._scene_manager = scene_manager
        self._scene_id = scene["id"]
        self._scene_name = scene["name"]

        # Sanitize name for entity_id
        safe_name = scene["name"].lower().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

        self._attr_unique_id = f"{entry.entry_id}_preset_{self._scene_id}_name"
        self._attr_name = f"Preset '{scene['name']}' Name"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model="Bias Amplifier",
        )

    @property
    def native_value(self) -> str:
        """Return the current preset name."""
        return self._scene_name

    async def async_set_value(self, value: str) -> None:
        """Rename the preset."""
        if not value or not value.strip():
            _LOGGER.error("Preset name cannot be empty")
            return

        new_name = value.strip()

        try:
            # Rename the preset
            await self._scene_manager.async_rename_scene(self._scene_id, new_name)
            self._scene_name = new_name
            _LOGGER.info("Renamed preset %d to '%s'", self._scene_id, new_name)

            # Reload integration to update button entity names
            await self._hass.config_entries.async_reload(self._entry.entry_id)

        except Exception as err:
            _LOGGER.error("Failed to rename preset %d: %s", self._scene_id, err)
            raise
