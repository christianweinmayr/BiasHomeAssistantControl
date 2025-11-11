"""Config flow for Powersoft Bias integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .bias_http_client import BiasHTTPClient
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=300)
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Powersoft Bias."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Try to connect to the amplifier
                info = await self._async_try_connect(
                    user_input[CONF_HOST],
                    user_input.get(CONF_PORT, DEFAULT_PORT),
                )

                # Set unique ID based on serial number
                await self.async_set_unique_id(info["serial_number"])
                self._abort_if_unique_id_configured()

                # Create entry
                return self.async_create_entry(
                    title=f"{info.get('model', 'Bias Amplifier')} ({info['serial_number']})",
                    data=user_input,
                )

            except ConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _async_try_connect(self, host: str, port: int) -> dict[str, Any]:
        """Try to connect to the amplifier and get device info."""
        async with BiasHTTPClient(host=host, port=port, timeout=DEFAULT_TIMEOUT) as client:
            info = await client.get_device_info()

            if not info.get("serial_number"):
                raise ConnectionError("Could not get device info")

            return info
