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
    MAX_OUTPUT_EQ_BANDS,
    MAX_PRE_OUTPUT_EQ_BANDS,
    MAX_INPUT_EQ_BANDS,
    MAX_XOVER_BANDS,
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
    # v0.4.0 - EQ paths
    PATH_OUTPUT_IIR_ENABLE,
    PATH_OUTPUT_IIR_TYPE,
    PATH_OUTPUT_IIR_FC,
    PATH_OUTPUT_IIR_GAIN,
    PATH_OUTPUT_IIR_Q,
    PATH_OUTPUT_IIR_SLOPE,
    PATH_PRE_OUTPUT_IIR_ENABLE,
    PATH_PRE_OUTPUT_IIR_TYPE,
    PATH_PRE_OUTPUT_IIR_FC,
    PATH_PRE_OUTPUT_IIR_GAIN,
    PATH_PRE_OUTPUT_IIR_Q,
    PATH_PRE_OUTPUT_IIR_SLOPE,
    PATH_INPUT_ZONE_IIR_ENABLE,
    PATH_INPUT_ZONE_IIR_TYPE,
    PATH_INPUT_ZONE_IIR_FC,
    PATH_INPUT_ZONE_IIR_GAIN,
    PATH_INPUT_ZONE_IIR_Q,
    PATH_INPUT_ZONE_IIR_SLOPE,
    # v0.4.0 - Limiter paths
    PATH_LIMITER_CLIP_ENABLE,
    PATH_LIMITER_CLIP_THRESHOLD,
    PATH_LIMITER_PEAK_ENABLE,
    PATH_LIMITER_PEAK_THRESHOLD,
    PATH_LIMITER_VRMS_ENABLE,
    PATH_LIMITER_VRMS_THRESHOLD,
    PATH_LIMITER_IRMS_ENABLE,
    PATH_LIMITER_IRMS_THRESHOLD,
    PATH_LIMITER_CLAMP_ENABLE,
    PATH_LIMITER_CLAMP_THRESHOLD,
    PATH_LIMITER_THERMAL_ENABLE,
    PATH_LIMITER_THERMAL_THRESHOLD,
    PATH_LIMITER_TRUEPOWER_ENABLE,
    PATH_LIMITER_TRUEPOWER_THRESHOLD,
    # v0.4.0 - Crossover paths
    PATH_XOVER_ENABLE,
    PATH_XOVER_FC,
    PATH_XOVER_SLOPE,
    # v0.4.0 - Matrix paths
    PATH_MATRIX_IN_GAIN,
    PATH_MATRIX_IN_MUTE,
    PATH_MATRIX_CHANNEL_GAIN,
    PATH_MATRIX_CHANNEL_MUTE,
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
        self._batch_index = 0  # Track which DSP parameter batch to fetch

    def _get_dsp_batch_paths(self, batch_index: int) -> list[str]:
        """Get a batch of DSP parameter paths to reduce API load.

        Returns one of 6 batches per call to avoid overwhelming the amplifier.
        Each batch is fetched sequentially on coordinator updates.
        """
        paths = []

        if batch_index == 0:
            # Batch 0: Output IIR EQ (8 bands × 6 params × 4 channels = 192 paths)
            for channel in range(MAX_CHANNELS):
                for band in range(8):
                    paths.append(PATH_OUTPUT_IIR_ENABLE.format(channel=channel, band=band))
                    paths.append(PATH_OUTPUT_IIR_TYPE.format(channel=channel, band=band))
                    paths.append(PATH_OUTPUT_IIR_FC.format(channel=channel, band=band))
                    paths.append(PATH_OUTPUT_IIR_GAIN.format(channel=channel, band=band))
                    paths.append(PATH_OUTPUT_IIR_Q.format(channel=channel, band=band))
                    paths.append(PATH_OUTPUT_IIR_SLOPE.format(channel=channel, band=band))

        elif batch_index == 1:
            # Batch 1: Pre-Output IIR EQ (8 bands × 6 params × 4 channels = 192 paths)
            for channel in range(MAX_CHANNELS):
                for band in range(8):
                    paths.append(PATH_PRE_OUTPUT_IIR_ENABLE.format(channel=channel, band=band))
                    paths.append(PATH_PRE_OUTPUT_IIR_TYPE.format(channel=channel, band=band))
                    paths.append(PATH_PRE_OUTPUT_IIR_FC.format(channel=channel, band=band))
                    paths.append(PATH_PRE_OUTPUT_IIR_GAIN.format(channel=channel, band=band))
                    paths.append(PATH_PRE_OUTPUT_IIR_Q.format(channel=channel, band=band))
                    paths.append(PATH_PRE_OUTPUT_IIR_SLOPE.format(channel=channel, band=band))

        elif batch_index == 2:
            # Batch 2: Input IIR EQ (7 bands × 6 params × 4 channels = 168 paths)
            for channel in range(MAX_CHANNELS):
                for band in range(7):
                    paths.append(PATH_INPUT_ZONE_IIR_ENABLE.format(channel=channel, band=band))
                    paths.append(PATH_INPUT_ZONE_IIR_TYPE.format(channel=channel, band=band))
                    paths.append(PATH_INPUT_ZONE_IIR_FC.format(channel=channel, band=band))
                    paths.append(PATH_INPUT_ZONE_IIR_GAIN.format(channel=channel, band=band))
                    paths.append(PATH_INPUT_ZONE_IIR_Q.format(channel=channel, band=band))
                    paths.append(PATH_INPUT_ZONE_IIR_SLOPE.format(channel=channel, band=band))

        elif batch_index == 3:
            # Batch 3: Limiters (7 types × 2 params × 4 channels = 56 paths)
            for channel in range(MAX_CHANNELS):
                paths.append(PATH_LIMITER_CLIP_ENABLE.format(channel=channel))
                paths.append(PATH_LIMITER_CLIP_THRESHOLD.format(channel=channel))
                paths.append(PATH_LIMITER_PEAK_ENABLE.format(channel=channel))
                paths.append(PATH_LIMITER_PEAK_THRESHOLD.format(channel=channel))
                paths.append(PATH_LIMITER_VRMS_ENABLE.format(channel=channel))
                paths.append(PATH_LIMITER_VRMS_THRESHOLD.format(channel=channel))
                paths.append(PATH_LIMITER_IRMS_ENABLE.format(channel=channel))
                paths.append(PATH_LIMITER_IRMS_THRESHOLD.format(channel=channel))
                paths.append(PATH_LIMITER_CLAMP_ENABLE.format(channel=channel))
                paths.append(PATH_LIMITER_CLAMP_THRESHOLD.format(channel=channel))
                paths.append(PATH_LIMITER_THERMAL_ENABLE.format(channel=channel))
                paths.append(PATH_LIMITER_THERMAL_THRESHOLD.format(channel=channel))
                paths.append(PATH_LIMITER_TRUEPOWER_ENABLE.format(channel=channel))
                paths.append(PATH_LIMITER_TRUEPOWER_THRESHOLD.format(channel=channel))

        elif batch_index == 4:
            # Batch 4: Crossovers (3 bands × 3 params × 4 channels = 36 paths)
            for channel in range(MAX_CHANNELS):
                for band in range(MAX_XOVER_BANDS):
                    paths.append(PATH_XOVER_ENABLE.format(channel=channel, band=band))
                    paths.append(PATH_XOVER_FC.format(channel=channel, band=band))
                    paths.append(PATH_XOVER_SLOPE.format(channel=channel, band=band))

        elif batch_index == 5:
            # Batch 5: Matrix mixer (4 input gains/mutes + 16 routing gains/mutes = 40 paths)
            for input_ch in range(MAX_CHANNELS):
                paths.append(PATH_MATRIX_IN_GAIN.format(input=input_ch))
                paths.append(PATH_MATRIX_IN_MUTE.format(input=input_ch))

            for channel in range(MAX_CHANNELS):
                for input_ch in range(MAX_CHANNELS):
                    paths.append(PATH_MATRIX_CHANNEL_GAIN.format(channel=channel, input=input_ch))
                    paths.append(PATH_MATRIX_CHANNEL_MUTE.format(channel=channel, input=input_ch))

        return paths

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

            # v0.4.0 - DSP Parameters (TEMPORARILY DISABLED for debugging)
            # dsp_batch = self._get_dsp_batch_paths(self._batch_index)
            # paths.extend(dsp_batch)
            # _LOGGER.debug(
            #     "Fetching DSP parameter batch %d (%d paths)",
            #     self._batch_index,
            #     len(dsp_batch)
            # )
            # self._batch_index = (self._batch_index + 1) % 6

            _LOGGER.info("Total paths to fetch: %d", len(paths))

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
                "limiters": {},
                "crossovers": {},
                "matrix": {"inputs": {}, "channels": {}},
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
                    "iir": {},
                    "pre_iir": {},
                }

                # v0.4.0 - Output IIR EQ (8 bands)
                for band in range(8):
                    band_key = str(band)
                    data["output_channels"][ch_key]["iir"][band_key] = {
                        "enable": values.get(PATH_OUTPUT_IIR_ENABLE.format(channel=channel, band=band), False),
                        "type": values.get(PATH_OUTPUT_IIR_TYPE.format(channel=channel, band=band), 0),
                        "fc": values.get(PATH_OUTPUT_IIR_FC.format(channel=channel, band=band), 1000.0),
                        "gain": values.get(PATH_OUTPUT_IIR_GAIN.format(channel=channel, band=band), 1.0),
                        "q": values.get(PATH_OUTPUT_IIR_Q.format(channel=channel, band=band), 1.0),
                        "slope": values.get(PATH_OUTPUT_IIR_SLOPE.format(channel=channel, band=band), 12),
                    }

                # v0.4.0 - Pre-Output IIR EQ (8 bands)
                for band in range(8):
                    band_key = str(band)
                    data["output_channels"][ch_key]["pre_iir"][band_key] = {
                        "enable": values.get(PATH_PRE_OUTPUT_IIR_ENABLE.format(channel=channel, band=band), False),
                        "type": values.get(PATH_PRE_OUTPUT_IIR_TYPE.format(channel=channel, band=band), 0),
                        "fc": values.get(PATH_PRE_OUTPUT_IIR_FC.format(channel=channel, band=band), 1000.0),
                        "gain": values.get(PATH_PRE_OUTPUT_IIR_GAIN.format(channel=channel, band=band), 1.0),
                        "q": values.get(PATH_PRE_OUTPUT_IIR_Q.format(channel=channel, band=band), 1.0),
                        "slope": values.get(PATH_PRE_OUTPUT_IIR_SLOPE.format(channel=channel, band=band), 12),
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
                    "iir": {},
                }

                # v0.4.0 - Input IIR EQ (7 bands)
                for band in range(7):
                    band_key = str(band)
                    data["input_channels"][ch_key]["iir"][band_key] = {
                        "enable": values.get(PATH_INPUT_ZONE_IIR_ENABLE.format(channel=channel, band=band), False),
                        "type": values.get(PATH_INPUT_ZONE_IIR_TYPE.format(channel=channel, band=band), 0),
                        "fc": values.get(PATH_INPUT_ZONE_IIR_FC.format(channel=channel, band=band), 1000.0),
                        "gain": values.get(PATH_INPUT_ZONE_IIR_GAIN.format(channel=channel, band=band), 1.0),
                        "q": values.get(PATH_INPUT_ZONE_IIR_Q.format(channel=channel, band=band), 1.0),
                        "slope": values.get(PATH_INPUT_ZONE_IIR_SLOPE.format(channel=channel, band=band), 12),
                    }

            # v0.4.0 - Parse limiters
            for channel in range(MAX_CHANNELS):
                ch_key = str(channel)
                data["limiters"][ch_key] = {
                    "clip": {
                        "enable": values.get(PATH_LIMITER_CLIP_ENABLE.format(channel=channel), False),
                        "threshold": values.get(PATH_LIMITER_CLIP_THRESHOLD.format(channel=channel), 1.0),
                    },
                    "peak": {
                        "enable": values.get(PATH_LIMITER_PEAK_ENABLE.format(channel=channel), False),
                        "threshold": values.get(PATH_LIMITER_PEAK_THRESHOLD.format(channel=channel), 1.0),
                    },
                    "vrms": {
                        "enable": values.get(PATH_LIMITER_VRMS_ENABLE.format(channel=channel), False),
                        "threshold": values.get(PATH_LIMITER_VRMS_THRESHOLD.format(channel=channel), 1.0),
                    },
                    "irms": {
                        "enable": values.get(PATH_LIMITER_IRMS_ENABLE.format(channel=channel), False),
                        "threshold": values.get(PATH_LIMITER_IRMS_THRESHOLD.format(channel=channel), 1.0),
                    },
                    "clamp": {
                        "enable": values.get(PATH_LIMITER_CLAMP_ENABLE.format(channel=channel), False),
                        "threshold": values.get(PATH_LIMITER_CLAMP_THRESHOLD.format(channel=channel), 1.0),
                    },
                    "thermal": {
                        "enable": values.get(PATH_LIMITER_THERMAL_ENABLE.format(channel=channel), False),
                        "threshold": values.get(PATH_LIMITER_THERMAL_THRESHOLD.format(channel=channel), 1.0),
                    },
                    "truepower": {
                        "enable": values.get(PATH_LIMITER_TRUEPOWER_ENABLE.format(channel=channel), False),
                        "threshold": values.get(PATH_LIMITER_TRUEPOWER_THRESHOLD.format(channel=channel), 1.0),
                    },
                }

            # v0.4.0 - Parse crossovers
            for channel in range(MAX_CHANNELS):
                ch_key = str(channel)
                data["crossovers"][ch_key] = {}
                for band in range(MAX_XOVER_BANDS):
                    band_key = str(band)
                    data["crossovers"][ch_key][band_key] = {
                        "enable": values.get(PATH_XOVER_ENABLE.format(channel=channel, band=band), False),
                        "fc": values.get(PATH_XOVER_FC.format(channel=channel, band=band), 1000.0),
                        "slope": values.get(PATH_XOVER_SLOPE.format(channel=channel, band=band), 12),
                    }

            # v0.4.0 - Parse matrix mixer
            for input_ch in range(MAX_CHANNELS):
                in_key = str(input_ch)
                data["matrix"]["inputs"][in_key] = {
                    "gain": values.get(PATH_MATRIX_IN_GAIN.format(input=input_ch), 1.0),
                    "mute": values.get(PATH_MATRIX_IN_MUTE.format(input=input_ch), False),
                }

            for channel in range(MAX_CHANNELS):
                ch_key = str(channel)
                data["matrix"]["channels"][ch_key] = {"routing": {}}
                for input_ch in range(MAX_CHANNELS):
                    in_key = str(input_ch)
                    data["matrix"]["channels"][ch_key]["routing"][in_key] = {
                        "gain": values.get(PATH_MATRIX_CHANNEL_GAIN.format(channel=channel, input=input_ch), 1.0),
                        "mute": values.get(PATH_MATRIX_CHANNEL_MUTE.format(channel=channel, input=input_ch), False),
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
