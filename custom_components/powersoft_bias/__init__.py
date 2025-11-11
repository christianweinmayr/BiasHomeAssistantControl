"""The Powersoft Bias Amplifier integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .bias_http_client import BiasHTTPClient
from .const import (
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MAX_CHANNELS,
    PATH_CHANNEL_GAIN,
    PATH_CHANNEL_MUTE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SWITCH]


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

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Clean up coordinator
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.disconnect()

    return unload_ok


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
            for channel in range(MAX_CHANNELS):
                paths.append(PATH_CHANNEL_GAIN.format(channel=channel))
                paths.append(PATH_CHANNEL_MUTE.format(channel=channel))

            # Read all values
            values = await self.client.read_values(paths)

            # Structure data by channel
            data = {"channels": {}}
            for channel in range(MAX_CHANNELS):
                gain_path = PATH_CHANNEL_GAIN.format(channel=channel)
                mute_path = PATH_CHANNEL_MUTE.format(channel=channel)

                data["channels"][channel] = {
                    "gain": values.get(gain_path, 1.0),
                    "mute": values.get(mute_path, False),
                }

            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
