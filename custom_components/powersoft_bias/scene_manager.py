"""
Scene Manager for Powersoft Bias Integration.

Manages preset storage, loading, and persistence.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "powersoft_bias_presets"

# Custom scene IDs start at 1
CUSTOM_SCENE_ID_START = 1


class SceneManager:
    """
    Manages scene storage and operations.

    Handles loading, saving, updating, and deleting custom presets/scenes.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str):
        """
        Initialize the scene manager.

        Args:
            hass: Home Assistant instance
            entry_id: Config entry ID for unique storage
        """
        self.hass = hass
        self.entry_id = entry_id
        self._store = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY}_{entry_id}",
        )
        self._custom_scenes: List[Dict[str, Any]] = []
        self._next_id = CUSTOM_SCENE_ID_START

    async def async_load(self) -> None:
        """Load scenes from storage."""
        data = await self._store.async_load()

        if data is None:
            _LOGGER.info("No custom presets found, starting fresh")
            self._custom_scenes = []
            self._next_id = CUSTOM_SCENE_ID_START
            return

        self._custom_scenes = data.get("scenes", [])

        # Calculate next available ID
        if self._custom_scenes:
            max_id = max(scene["id"] for scene in self._custom_scenes)
            self._next_id = max(max_id + 1, CUSTOM_SCENE_ID_START)
        else:
            self._next_id = CUSTOM_SCENE_ID_START

        _LOGGER.info("Loaded %d custom preset(s)", len(self._custom_scenes))

    async def async_save(self) -> None:
        """Save scenes to storage."""
        data = {
            "version": STORAGE_VERSION,
            "scenes": self._custom_scenes,
        }
        await self._store.async_save(data)
        _LOGGER.debug("Saved %d custom preset(s)", len(self._custom_scenes))

    def get_all_scenes(self) -> List[Dict[str, Any]]:
        """
        Get all scenes.

        Returns:
            List of all scene configurations
        """
        return self._custom_scenes.copy()

    def get_scene_by_id(self, scene_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific scene by ID.

        Args:
            scene_id: Scene ID to retrieve

        Returns:
            Scene configuration or None if not found
        """
        for scene in self._custom_scenes:
            if scene["id"] == scene_id:
                return scene
        return None

    def validate_scene_config(self, config: Dict[str, Any]) -> None:
        """
        Validate scene configuration.

        Args:
            config: Scene configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        # Check required fields
        if "name" not in config:
            raise ValueError("Scene missing required field: name")

        if "output_channels" not in config:
            raise ValueError("Scene missing required field: output_channels")

        # Validate output channels
        output_channels = config["output_channels"]
        if not isinstance(output_channels, dict):
            raise ValueError("output_channels must be a dictionary")

        # We expect 4 channels (0-3)
        for ch_idx in range(4):
            if ch_idx not in output_channels:
                raise ValueError(f"Missing output channel {ch_idx}")

            ch_config = output_channels[ch_idx]

            # Validate gain
            if "gain" not in ch_config:
                raise ValueError(f"Channel {ch_idx} missing gain")
            if not isinstance(ch_config["gain"], (int, float)) or not 0.0 <= ch_config["gain"] <= 2.0:
                raise ValueError(f"Channel {ch_idx} gain must be between 0.0 and 2.0")

            # Validate mute
            if "mute" not in ch_config:
                raise ValueError(f"Channel {ch_idx} missing mute")
            if not isinstance(ch_config["mute"], bool):
                raise ValueError(f"Channel {ch_idx} mute must be boolean")

            # Name is optional but if present must be string
            if "name" in ch_config and not isinstance(ch_config["name"], str):
                raise ValueError(f"Channel {ch_idx} name must be string")

        # Validate standby if present
        if "standby" in config:
            if not isinstance(config["standby"], bool):
                raise ValueError("Standby must be boolean")

        # Validate input channels if present (optional for v1)
        if "input_channels" in config:
            input_channels = config["input_channels"]
            if not isinstance(input_channels, dict):
                raise ValueError("input_channels must be a dictionary")

    async def async_create_scene(
        self,
        name: str,
        config: Dict[str, Any],
        scene_id: Optional[int] = None
    ) -> int:
        """
        Create a new scene.

        Args:
            name: Scene name
            config: Scene configuration (output_channels, standby, etc.)
            scene_id: Optional specific ID (for testing or overwrites)

        Returns:
            ID of created scene

        Raises:
            ValueError: If configuration is invalid or scene_id conflicts
        """
        # Validate configuration
        scene_config = config.copy()
        scene_config["name"] = name
        self.validate_scene_config(scene_config)

        # Determine ID
        if scene_id is not None:
            # Check if ID is in valid range
            if scene_id < CUSTOM_SCENE_ID_START:
                raise ValueError(
                    f"Cannot use scene_id < {CUSTOM_SCENE_ID_START}"
                )
            # Check if ID already exists
            if any(s["id"] == scene_id for s in self._custom_scenes):
                raise ValueError(f"Scene ID {scene_id} already exists")
            use_id = scene_id
        else:
            use_id = self._next_id
            self._next_id += 1

        # Create scene with metadata
        now = datetime.utcnow().isoformat() + "Z"
        scene = {
            "id": use_id,
            "name": name,
            "output_channels": scene_config["output_channels"],
            "input_channels": scene_config.get("input_channels", {}),
            "standby": scene_config.get("standby", False),
            "created_at": now,
            "updated_at": now,
        }

        self._custom_scenes.append(scene)
        await self.async_save()

        _LOGGER.info("Created preset '%s' (ID: %d)", name, use_id)
        return use_id

    async def async_update_scene(self, scene_id: int, config: Dict[str, Any]) -> None:
        """
        Update an existing scene.

        Args:
            scene_id: ID of scene to update
            config: New scene configuration

        Raises:
            ValueError: If scene not found
        """
        # Find the scene
        scene = None
        scene_idx = None
        for idx, s in enumerate(self._custom_scenes):
            if s["id"] == scene_id:
                scene = s
                scene_idx = idx
                break

        if scene is None:
            raise ValueError(f"Scene ID {scene_id} not found")

        # Validate new configuration
        updated_config = config.copy()
        updated_config["name"] = scene["name"]  # Preserve name if not provided
        if "name" in config:
            updated_config["name"] = config["name"]
        self.validate_scene_config(updated_config)

        # Update scene
        now = datetime.utcnow().isoformat() + "Z"
        self._custom_scenes[scene_idx].update({
            "name": updated_config["name"],
            "output_channels": updated_config["output_channels"],
            "input_channels": updated_config.get("input_channels", {}),
            "standby": updated_config.get("standby", False),
            "updated_at": now,
        })

        await self.async_save()
        _LOGGER.info("Updated preset ID %d", scene_id)

    async def async_delete_scene(self, scene_id: int) -> None:
        """
        Delete a scene.

        Args:
            scene_id: ID of scene to delete

        Raises:
            ValueError: If scene not found
        """
        # Find and remove the scene
        initial_count = len(self._custom_scenes)
        self._custom_scenes = [s for s in self._custom_scenes if s["id"] != scene_id]

        if len(self._custom_scenes) == initial_count:
            raise ValueError(f"Scene ID {scene_id} not found")

        await self.async_save()
        _LOGGER.info("Deleted preset ID %d", scene_id)

    async def async_rename_scene(self, scene_id: int, new_name: str) -> None:
        """
        Rename a scene.

        Args:
            scene_id: ID of scene to rename
            new_name: New name for the scene

        Raises:
            ValueError: If scene not found or name is empty
        """
        if not new_name or not new_name.strip():
            raise ValueError("Scene name cannot be empty")

        # Find the scene
        scene = None
        scene_idx = None
        for idx, s in enumerate(self._custom_scenes):
            if s["id"] == scene_id:
                scene = s
                scene_idx = idx
                break

        if scene is None:
            raise ValueError(f"Scene ID {scene_id} not found")

        # Update the name
        old_name = scene["name"]
        self._custom_scenes[scene_idx]["name"] = new_name.strip()
        self._custom_scenes[scene_idx]["updated_at"] = datetime.utcnow().isoformat() + "Z"

        await self.async_save()
        _LOGGER.info("Renamed preset ID %d from '%s' to '%s'", scene_id, old_name, new_name)

    def get_custom_scene_count(self) -> int:
        """Get count of custom scenes."""
        return len(self._custom_scenes)

    def get_total_scene_count(self) -> int:
        """Get total count of all scenes."""
        return len(self._custom_scenes)
