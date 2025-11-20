"""The Powersoft Bias Amplifier integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .bias_http_client import BiasHTTPClient
from .scene_manager import SceneManager
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_CHANNELS,
    # Output paths
    PATH_CHANNEL_NAME,
    PATH_CHANNEL_ENABLE,
    PATH_CHANNEL_GAIN,
    PATH_CHANNEL_MUTE,
    PATH_CHANNEL_POLARITY,
    PATH_CHANNEL_OUT_DELAY_ENABLE,
    PATH_CHANNEL_OUT_DELAY_VALUE,
    # Input paths
    PATH_INPUT_ENABLE,
    PATH_INPUT_GAIN,
    PATH_INPUT_MUTE,
    PATH_INPUT_POLARITY,
    PATH_INPUT_SHADING_GAIN,
    PATH_INPUT_DELAY_ENABLE,
    PATH_INPUT_DELAY_VALUE,
    # System paths
    PATH_STANDBY,
    PATH_FIRMWARE_VERSION,
    PATH_MODEL_NAME,
    PATH_MODEL_SERIAL,
    # Coordinator keys
    COORDINATOR,
    CLIENT,
    SCENE_MANAGER,
    ACTIVE_SCENE_ID,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SWITCH, Platform.BUTTON, Platform.SENSOR, Platform.SELECT, Platform.TEXT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Powersoft Bias from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Create HTTP client
    client = BiasHTTPClient(
        host=host,
        port=port,
        timeout=DEFAULT_TIMEOUT,
        client_id=f"home-assistant-{entry.entry_id[:8]}"
    )

    # Create coordinator
    coordinator = BiasDataUpdateCoordinator(
        hass=hass,
        client=client,
        update_interval=timedelta(seconds=scan_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Create and load scene manager
    scene_manager = SceneManager(hass, entry.entry_id)
    await scene_manager.async_load()
    _LOGGER.info(
        "Scene manager initialized: %d preset(s)",
        scene_manager.get_custom_scene_count()
    )

    # Store coordinator, client, scene manager, and active scene tracking
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        CLIENT: client,
        SCENE_MANAGER: scene_manager,
        ACTIVE_SCENE_ID: None,  # Track currently active scene
    }

    # Register services (only once for the domain)
    if not hass.services.has_service(DOMAIN, "save_preset"):
        await async_register_services(hass)

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up coordinator and client
        data = hass.data[DOMAIN].pop(entry.entry_id)
        client: BiasHTTPClient = data[CLIENT]
        await client.disconnect()

    return unload_ok


async def async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""
    import voluptuous as vol
    from homeassistant.helpers import config_validation as cv

    _LOGGER.info("Registering Powersoft Bias services")

    async def handle_save_preset(call):
        """Handle save_preset service call."""
        name = call.data["name"]
        _LOGGER.info("Service call: save_preset with name='%s'", name)

        # Get the first available entry (services are domain-level, not per-entry)
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        data = hass.data[DOMAIN][entry_id]
        client: BiasHTTPClient = data[CLIENT]
        scene_manager: SceneManager = data[SCENE_MANAGER]

        try:
            # Capture current amplifier state
            config = await client.capture_current_state()

            # Save as new scene
            scene_id = await scene_manager.async_create_scene(name, config)

            _LOGGER.info("Successfully created preset '%s' (ID: %d)", name, scene_id)

            # Reload integration to refresh button entities
            await hass.config_entries.async_reload(entry_id)

        except Exception as err:
            _LOGGER.error("Failed to save preset '%s': %s", name, err)
            raise

    async def handle_update_preset(call):
        """Handle update_preset service call."""
        scene_id = call.data["scene_id"]
        _LOGGER.info("Service call: update_preset with scene_id=%d", scene_id)

        # Get the first available entry
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        data = hass.data[DOMAIN][entry_id]
        client: BiasHTTPClient = data[CLIENT]
        scene_manager: SceneManager = data[SCENE_MANAGER]

        try:
            # Capture current amplifier state
            config = await client.capture_current_state()

            # Update existing scene
            await scene_manager.async_update_scene(scene_id, config)

            _LOGGER.info("Successfully updated preset ID %d", scene_id)

            # Reload integration to refresh button entities
            await hass.config_entries.async_reload(entry_id)

        except Exception as err:
            _LOGGER.error("Failed to update preset %d: %s", scene_id, err)
            raise

    async def handle_delete_preset(call):
        """Handle delete_preset service call."""
        scene_id = call.data["scene_id"]
        _LOGGER.info("Service call: delete_preset with scene_id=%d", scene_id)

        # Get the first available entry
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        data = hass.data[DOMAIN][entry_id]
        scene_manager: SceneManager = data[SCENE_MANAGER]

        try:
            # Delete the scene
            await scene_manager.async_delete_scene(scene_id)

            _LOGGER.info("Successfully deleted preset ID %d", scene_id)

            # Reload integration to refresh button entities
            await hass.config_entries.async_reload(entry_id)

        except Exception as err:
            _LOGGER.error("Failed to delete preset %d: %s", scene_id, err)
            raise

    async def handle_rename_preset(call):
        """Handle rename_preset service call."""
        scene_id = call.data["scene_id"]
        new_name = call.data["name"]
        _LOGGER.info("Service call: rename_preset with scene_id=%d, name='%s'", scene_id, new_name)

        # Get the first available entry
        entry_id = next(iter(hass.data[DOMAIN].keys()))
        data = hass.data[DOMAIN][entry_id]
        scene_manager: SceneManager = data[SCENE_MANAGER]

        try:
            # Rename the scene
            await scene_manager.async_rename_scene(scene_id, new_name)

            _LOGGER.info("Successfully renamed preset ID %d", scene_id)

            # Reload integration to refresh button names
            await hass.config_entries.async_reload(entry_id)

        except Exception as err:
            _LOGGER.error("Failed to rename preset %d: %s", scene_id, err)
            raise

    # Register services
    hass.services.async_register(
        DOMAIN,
        "save_preset",
        handle_save_preset,
        schema=vol.Schema({
            vol.Required("name"): cv.string,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        "update_preset",
        handle_update_preset,
        schema=vol.Schema({
            vol.Required("scene_id"): cv.positive_int,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        "delete_preset",
        handle_delete_preset,
        schema=vol.Schema({
            vol.Required("scene_id"): cv.positive_int,
        }),
    )

    hass.services.async_register(
        DOMAIN,
        "rename_preset",
        handle_rename_preset,
        schema=vol.Schema({
            vol.Required("scene_id"): cv.positive_int,
            vol.Required("name"): cv.string,
        }),
    )


class BiasDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Bias amplifier data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BiasHTTPClient,
        update_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch data from API endpoint."""
        try:
            # Build list of paths to read
            paths = []

            # Output channels - comprehensive parameters
            for channel in range(MAX_CHANNELS):
                paths.append(PATH_CHANNEL_NAME.format(channel=channel))
                paths.append(PATH_CHANNEL_ENABLE.format(channel=channel))
                paths.append(PATH_CHANNEL_GAIN.format(channel=channel))
                paths.append(PATH_CHANNEL_MUTE.format(channel=channel))
                paths.append(PATH_CHANNEL_POLARITY.format(channel=channel))
                paths.append(PATH_CHANNEL_OUT_DELAY_ENABLE.format(channel=channel))
                paths.append(PATH_CHANNEL_OUT_DELAY_VALUE.format(channel=channel))

            # Input channels - comprehensive parameters
            for channel in range(MAX_CHANNELS):
                paths.append(PATH_INPUT_ENABLE.format(channel=channel))
                paths.append(PATH_INPUT_GAIN.format(channel=channel))
                paths.append(PATH_INPUT_MUTE.format(channel=channel))
                paths.append(PATH_INPUT_POLARITY.format(channel=channel))
                paths.append(PATH_INPUT_SHADING_GAIN.format(channel=channel))
                paths.append(PATH_INPUT_DELAY_ENABLE.format(channel=channel))
                paths.append(PATH_INPUT_DELAY_VALUE.format(channel=channel))

            # System parameters
            paths.append(PATH_STANDBY)
            paths.append(PATH_FIRMWARE_VERSION)
            paths.append(PATH_MODEL_NAME)
            paths.append(PATH_MODEL_SERIAL)

            # Read all values
            values = await self.client.read_values(paths)

            # Structure data
            data = {
                "output_channels": {},
                "input_channels": {},
                "device_info": {},
                "standby": None,
            }

            # Parse output channels (use string keys for JSON compatibility)
            for channel in range(MAX_CHANNELS):
                ch_key = str(channel)
                data["output_channels"][ch_key] = {
                    "name": values.get(PATH_CHANNEL_NAME.format(channel=channel), f"Output {channel + 1}"),
                    "enable": values.get(PATH_CHANNEL_ENABLE.format(channel=channel), True),
                    "gain": values.get(PATH_CHANNEL_GAIN.format(channel=channel), 1.0),
                    "mute": values.get(PATH_CHANNEL_MUTE.format(channel=channel), False),
                    "polarity": values.get(PATH_CHANNEL_POLARITY.format(channel=channel), False),
                    "delay_enable": values.get(PATH_CHANNEL_OUT_DELAY_ENABLE.format(channel=channel), False),
                    "delay": values.get(PATH_CHANNEL_OUT_DELAY_VALUE.format(channel=channel), 0.0),
                }

            # Parse input channels (use string keys for JSON compatibility)
            for channel in range(MAX_CHANNELS):
                ch_key = str(channel)
                data["input_channels"][ch_key] = {
                    "enable": values.get(PATH_INPUT_ENABLE.format(channel=channel), True),
                    "gain": values.get(PATH_INPUT_GAIN.format(channel=channel), 1.0),
                    "mute": values.get(PATH_INPUT_MUTE.format(channel=channel), False),
                    "polarity": values.get(PATH_INPUT_POLARITY.format(channel=channel), False),
                    "shading_gain": values.get(PATH_INPUT_SHADING_GAIN.format(channel=channel), 1.0),
                    "delay_enable": values.get(PATH_INPUT_DELAY_ENABLE.format(channel=channel), False),
                    "delay": values.get(PATH_INPUT_DELAY_VALUE.format(channel=channel), 0.0),
                }

            # Parse system/device info
            data["standby"] = values.get(PATH_STANDBY, False)
            data["device_info"] = {
                "firmware_version": values.get(PATH_FIRMWARE_VERSION, "Unknown"),
                "model_name": values.get(PATH_MODEL_NAME, "Bias Amplifier"),
                "serial_number": values.get(PATH_MODEL_SERIAL, "Unknown"),
            }

            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
