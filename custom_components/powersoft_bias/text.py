"""Text platform for Powersoft Bias integration."""
import logging

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DOMAIN,
    MANUFACTURER,
    SCENE_MANAGER,
    UID_SCENE,
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

    # Get all scenes
    scenes = scene_manager.get_all_scenes()

    # Create rename text entities for each scene
    for scene in scenes:
        entities.append(
            BiasSceneRenameText(
                scene_manager,
                entry,
                scene,
                hass,
            )
        )

    async_add_entities(entities)
    _LOGGER.info("Added %d text entities (scene rename)", len(entities))


class BiasSceneRenameText(TextEntity):
    """Text entity to rename a scene."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:rename-box"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min = 1
    _attr_native_max = 100
    _attr_pattern = r"^.+$"  # At least one character

    def __init__(
        self,
        scene_manager: SceneManager,
        entry: ConfigEntry,
        scene_config: dict,
        hass: HomeAssistant,
    ):
        """Initialize the rename text entity."""
        self._scene_manager = scene_manager
        self._scene_config = scene_config
        self._entry = entry
        self._hass = hass
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": "Bias Amplifier",
        }
        self._attr_unique_id = f"{entry.entry_id}_{UID_SCENE}_{scene_config['id']}_rename"
        self._attr_name = f"Rename {scene_config['name']}"

    @property
    def native_value(self) -> str:
        """Return the current scene name."""
        return self._scene_config["name"]

    async def async_set_value(self, value: str) -> None:
        """Rename the scene."""
        try:
            # Validate the new name
            if not value or not value.strip():
                _LOGGER.error("Scene name cannot be empty")
                return

            new_name = value.strip()

            # Check if name is the same
            if new_name == self._scene_config["name"]:
                _LOGGER.debug("Scene name unchanged: %s", new_name)
                return

            _LOGGER.info(
                "Renaming scene '%s' (ID: %d) to '%s'",
                self._scene_config["name"],
                self._scene_config["id"],
                new_name,
            )

            # Rename the scene
            await self._scene_manager.async_rename_scene(
                self._scene_config["id"],
                new_name,
            )

            # Update local config
            self._scene_config["name"] = new_name
            self._attr_name = f"Rename {new_name}"

            _LOGGER.info("Successfully renamed scene to '%s'", new_name)

            # Reload integration to refresh all entities with new name
            await self._hass.config_entries.async_reload(self._entry.entry_id)

        except ValueError as err:
            _LOGGER.error("Failed to rename scene: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Unexpected error renaming scene: %s", err)
            raise
