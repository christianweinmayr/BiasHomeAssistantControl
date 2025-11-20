"""Button platform for Powersoft Bias integration."""
import logging
from typing import Any
from datetime import datetime

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory

from .const import (
    DOMAIN,
    COORDINATOR,
    CLIENT,
    SCENE_MANAGER,
    ACTIVE_SCENE_ID,
    UID_SCENE,
    MANUFACTURER,
)
from .bias_http_client import BiasHTTPClient
from .scene_manager import SceneManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bias button entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    client = hass.data[DOMAIN][entry.entry_id][CLIENT]
    scene_manager: SceneManager = hass.data[DOMAIN][entry.entry_id][SCENE_MANAGER]

    # Add "Create Preset" button (always visible)
    entities = [
        BiasCreateSceneButton(
            coordinator,
            client,
            scene_manager,
            entry,
            hass,
        )
    ]

    # Get all scenes
    scenes = scene_manager.get_all_scenes()

    # Create button entities for each scene
    for scene in scenes:
        # Main scene application button
        entities.append(
            BiasSceneButton(
                coordinator,
                client,
                entry,
                scene,
            )
        )

        # Update button
        entities.append(
            BiasSceneUpdateButton(
                coordinator,
                client,
                scene_manager,
                entry,
                scene,
            )
        )

        # Delete button
        entities.append(
            BiasSceneDeleteButton(
                scene_manager,
                entry,
                scene,
                hass,
            )
        )

    async_add_entities(entities, update_before_add=True)

    # Count button types for logging
    scene_buttons = len([e for e in entities if isinstance(e, BiasSceneButton)])
    update_buttons = len([e for e in entities if isinstance(e, BiasSceneUpdateButton)])
    delete_buttons = len([e for e in entities if isinstance(e, BiasSceneDeleteButton)])
    create_buttons = len([e for e in entities if isinstance(e, BiasCreateSceneButton)])

    _LOGGER.info(
        "Added %d total button(s): %d scene, %d update, %d delete, %d create",
        len(entities), scene_buttons, update_buttons, delete_buttons, create_buttons
    )
    _LOGGER.info("Custom presets: %d", scene_manager.get_custom_scene_count())


class BiasSceneButton(CoordinatorEntity, ButtonEntity):
    """Representation of a preset button."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:palette"

    def __init__(
        self,
        coordinator,
        client: BiasHTTPClient,
        entry: ConfigEntry,
        scene_config: dict,
    ):
        """Initialize the preset button."""
        super().__init__(coordinator)
        self._client = client
        self._scene_config = scene_config
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": "Bias Amplifier",
        }
        self._attr_unique_id = f"{entry.entry_id}_{UID_SCENE}_{scene_config['id']}"
        self._attr_name = f"Preset - {scene_config['name']}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        attrs = {
            "scene_id": self._scene_config["id"],
            "output_channels": self._scene_config.get("output_channels", {}),
            "standby": self._scene_config.get("standby", False),
        }

        # Add timestamps if available
        if "created_at" in self._scene_config:
            attrs["created_at"] = self._scene_config["created_at"]
        if "updated_at" in self._scene_config:
            attrs["updated_at"] = self._scene_config["updated_at"]

        return attrs

    async def async_press(self) -> None:
        """Handle the button press - apply the preset."""
        try:
            _LOGGER.info("Applying preset: %s", self._scene_config["name"])
            await self._client.apply_scene(self._scene_config)

            # Update active scene tracking
            self.hass.data[DOMAIN][self._entry.entry_id][ACTIVE_SCENE_ID] = self._scene_config["id"]

            # Force immediate coordinator refresh to show new state
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error(
                "Failed to apply preset %s: %s", self._scene_config["name"], err
            )
            raise


class BiasSceneUpdateButton(CoordinatorEntity, ButtonEntity):
    """Button to update a custom preset with current amplifier state."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:content-save-edit"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator,
        client: BiasHTTPClient,
        scene_manager: SceneManager,
        entry: ConfigEntry,
        scene_config: dict,
    ):
        """Initialize the update button."""
        super().__init__(coordinator)
        self._client = client
        self._scene_manager = scene_manager
        self._scene_config = scene_config
        self._entry = entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": "Bias Amplifier",
        }
        self._attr_unique_id = f"{entry.entry_id}_{UID_SCENE}_{scene_config['id']}_update"
        self._attr_name = f"Preset - Update '{scene_config['name']}'"

    async def async_press(self) -> None:
        """Handle button press - update the preset with current amp state."""
        try:
            _LOGGER.info("Updating preset: %s", self._scene_config["name"])

            # Capture current amplifier state
            config = await self._client.capture_current_state()

            # Update the scene
            await self._scene_manager.async_update_scene(
                self._scene_config["id"], config
            )

            _LOGGER.info("Successfully updated preset '%s'", self._scene_config["name"])

            # Reload integration to refresh all buttons
            await self.hass.config_entries.async_reload(self._entry.entry_id)

        except Exception as err:
            _LOGGER.error(
                "Failed to update preset %s: %s", self._scene_config["name"], err
            )
            raise


class BiasSceneDeleteButton(ButtonEntity):
    """Button to delete a custom preset."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:delete"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        scene_manager: SceneManager,
        entry: ConfigEntry,
        scene_config: dict,
        hass: HomeAssistant,
    ):
        """Initialize the delete button."""
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
        self._attr_unique_id = f"{entry.entry_id}_{UID_SCENE}_{scene_config['id']}_delete"
        self._attr_name = f"Preset - Delete '{scene_config['name']}'"

    async def async_press(self) -> None:
        """Handle button press - delete the preset."""
        try:
            scene_name = self._scene_config["name"]
            scene_id = self._scene_config["id"]

            _LOGGER.warning("Deleting preset '%s' (ID: %d)", scene_name, scene_id)

            # Delete the scene
            await self._scene_manager.async_delete_scene(scene_id)

            _LOGGER.info("Successfully deleted preset '%s'", scene_name)

            # Reload integration to refresh all buttons
            await self._hass.config_entries.async_reload(self._entry.entry_id)

        except Exception as err:
            _LOGGER.error(
                "Failed to delete preset %s: %s", self._scene_config["name"], err
            )
            raise


class BiasCreateSceneButton(CoordinatorEntity, ButtonEntity):
    """Button to create a new preset from current amplifier state."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:plus-circle"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator,
        client: BiasHTTPClient,
        scene_manager: SceneManager,
        entry: ConfigEntry,
        hass: HomeAssistant,
    ):
        """Initialize the create preset button."""
        super().__init__(coordinator)
        self._client = client
        self._scene_manager = scene_manager
        self._entry = entry
        self._hass = hass
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": MANUFACTURER,
            "model": "Bias Amplifier",
        }
        self._attr_unique_id = f"{entry.entry_id}_create_scene"
        self._attr_name = "Preset - Create New"

    async def async_press(self) -> None:
        """Handle button press - create new preset from current amp state."""
        try:
            # Generate preset name with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            scene_name = f"Preset {timestamp}"

            _LOGGER.info("Creating new preset: %s", scene_name)

            # Capture current amplifier state
            config = await self._client.capture_current_state()

            # Create the scene
            scene_id = await self._scene_manager.async_create_scene(scene_name, config)

            _LOGGER.info("Successfully created preset '%s' (ID: %d)", scene_name, scene_id)

            # Create notification to inform user
            await self._hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Preset Created",
                    "message": f"Created new preset: '{scene_name}' (ID: {scene_id})\n\n"
                               f"The preset includes current channel gains, mutes, and names.\n\n"
                               f"Use the 'Update {scene_name}' button to modify it later.",
                    "notification_id": f"{DOMAIN}_scene_created_{scene_id}",
                },
            )

            # Reload integration to show new buttons
            await self._hass.config_entries.async_reload(self._entry.entry_id)

        except Exception as err:
            _LOGGER.error("Failed to create preset: %s", err)
            await self._hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Preset Creation Failed",
                    "message": f"Error creating preset: {err}",
                    "notification_id": f"{DOMAIN}_scene_create_error",
                },
            )
            raise
