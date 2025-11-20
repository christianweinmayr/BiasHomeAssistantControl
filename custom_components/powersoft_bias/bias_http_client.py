"""
HTTP REST API Client for Powersoft Bias Amplifiers.

The Bias series (e.g., Bias Q1.5+, Q2, Q5) use an HTTP REST API instead of UDP protocol.
This module provides an async client for communicating with these amplifiers.

Protocol: POST /am with JSON payload
"""
import logging
from typing import Any, Dict, List, Optional, Union
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

# Data type constants
TYPE_STRING = 10
TYPE_FLOAT = 20
TYPE_BOOL = 40

# Action type constants
ACTION_READ = "READ"
ACTION_WRITE = "WRITE"

# Response result codes
RESULT_SUCCESS = 10


class BiasHTTPClient:
    """
    Async HTTP client for Powersoft Bias amplifiers.

    These amplifiers use a JSON REST API over HTTP on port 80.
    """

    def __init__(
        self,
        host: str,
        port: int = 80,
        timeout: float = 5.0,
        client_id: str = "home-assistant"
    ):
        """
        Initialize the Bias HTTP client.

        Args:
            host: IP address of the amplifier
            port: HTTP port (default 80)
            timeout: Request timeout in seconds
            client_id: Client identifier for API requests
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client_id = client_id
        self.base_url = f"http://{host}:{port}"
        self._session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> None:
        """Create HTTP session."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
            _LOGGER.debug("Created HTTP session for %s", self.host)

    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
            _LOGGER.debug("Closed HTTP session for %s", self.host)

    async def read_values(self, paths: List[str]) -> Dict[str, Any]:
        """
        Read values from the amplifier.

        Args:
            paths: List of parameter paths to read
                  e.g., ["/Device/Config/Hardware/Model/Serial"]

        Returns:
            Dictionary mapping paths to their values

        Raises:
            aiohttp.ClientError: If HTTP request fails
            ValueError: If response parsing fails
        """
        if self._session is None:
            await self.connect()

        payload = {
            "clientId": self.client_id,
            "payload": {
                "type": "ACTION",
                "action": {
                    "type": ACTION_READ,
                    "values": [{"id": path, "single": True} for path in paths]
                }
            }
        }

        try:
            async with async_timeout.timeout(self.timeout):
                async with self._session.post(
                    f"{self.base_url}/am",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            # Parse response
            result = {}
            action = data.get("payload", {}).get("action", {})
            for value_obj in action.get("values", []):
                path = value_obj.get("id")
                if value_obj.get("result") != RESULT_SUCCESS:
                    _LOGGER.warning("Failed to read %s: result=%s", path, value_obj.get("result"))
                    continue

                data_obj = value_obj.get("data", {})
                data_type = data_obj.get("type")

                if data_type == TYPE_STRING:
                    result[path] = data_obj.get("stringValue")
                elif data_type == TYPE_FLOAT:
                    result[path] = data_obj.get("floatValue")
                elif data_type == TYPE_BOOL:
                    result[path] = data_obj.get("boolValue")
                else:
                    _LOGGER.warning("Unknown data type %s for %s", data_type, path)

            return result

        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP request failed to %s: %s", self.host, err)
            raise
        except Exception as err:
            _LOGGER.error("Failed to read values from %s: %s", self.host, err)
            raise ValueError(f"Failed to parse response: {err}") from err

    async def write_value(
        self,
        path: str,
        value: Union[str, float, bool]
    ) -> bool:
        """
        Write a value to the amplifier.

        Args:
            path: Parameter path to write
            value: Value to write (type determines data type)

        Returns:
            True if write was successful

        Raises:
            aiohttp.ClientError: If HTTP request fails
            ValueError: If response parsing fails
        """
        if self._session is None:
            await self.connect()

        # Determine data type and build data object
        if isinstance(value, bool):
            data_obj = {"type": TYPE_BOOL, "boolValue": value}
        elif isinstance(value, (int, float)):
            data_obj = {"type": TYPE_FLOAT, "floatValue": float(value)}
        elif isinstance(value, str):
            data_obj = {"type": TYPE_STRING, "stringValue": value}
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

        payload = {
            "clientId": self.client_id,
            "payload": {
                "type": "ACTION",
                "action": {
                    "type": ACTION_WRITE,
                    "values": [{
                        "id": path,
                        "data": data_obj,
                        "single": True
                    }]
                }
            }
        }

        try:
            async with async_timeout.timeout(self.timeout):
                async with self._session.post(
                    f"{self.base_url}/am",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            # Check if write was successful
            action = data.get("payload", {}).get("action", {})
            for value_obj in action.get("values", []):
                if value_obj.get("id") == path:
                    return value_obj.get("result") == RESULT_SUCCESS

            return False

        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP request failed to %s: %s", self.host, err)
            raise
        except Exception as err:
            _LOGGER.error("Failed to write value to %s: %s", self.host, err)
            raise ValueError(f"Failed to parse response: {err}") from err

    async def get_device_info(self) -> Dict[str, Any]:
        """
        Get device information.

        Returns:
            Dictionary with device info (model, serial, etc.)
        """
        paths = [
            "/Device/Config/Hardware/Model/Name",
            "/Device/Config/Hardware/Model/Serial",
            "/Device/Config/Hardware/Manufacturer",
        ]

        values = await self.read_values(paths)

        return {
            "model": values.get("/Device/Config/Hardware/Model/Name", "Unknown"),
            "serial_number": values.get("/Device/Config/Hardware/Model/Serial", "Unknown"),
            "manufacturer": values.get("/Device/Config/Hardware/Manufacturer", "Powersoft"),
        }

    async def capture_current_state(self) -> Dict[str, Any]:
        """
        Capture complete current amplifier state for preset creation.

        Reads all output channel gain/mute/name values and standby state.

        Returns:
            Dictionary with complete preset configuration ready to save

        Raises:
            aiohttp.ClientError: If HTTP request fails
            ValueError: If response parsing fails
        """
        _LOGGER.info("Capturing current amplifier state...")

        # Build list of paths to read
        paths = []

        # Output channels (0-3): Gain, Mute, Name
        for channel in range(4):
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Gain/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Mute/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Name")

        # Standby state (if available)
        paths.append("/Device/Audio/Presets/Live/Generals/Standby/Value")

        # Read all values
        values = await self.read_values(paths)

        # Structure data by channel (use string keys for JSON compatibility)
        output_channels = {}
        for channel in range(4):
            gain_path = f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Gain/Value"
            mute_path = f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Mute/Value"
            name_path = f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Name"

            output_channels[str(channel)] = {
                "gain": values.get(gain_path, 1.0),
                "mute": values.get(mute_path, False),
                "name": values.get(name_path, f"Channel {channel + 1}"),
            }

        # Build preset configuration
        preset_config = {
            "output_channels": output_channels,
            "standby": values.get("/Device/Audio/Presets/Live/Generals/Standby/Value", False),
        }

        _LOGGER.info("Captured state: 4 output channels")
        return preset_config

    async def apply_scene(self, scene_config: Dict[str, Any]) -> None:
        """
        Apply a complete preset configuration.

        Applies all configuration changes (gain, mute) in a batch request
        for maximum efficiency.

        Args:
            scene_config: Dictionary with preset configuration:
                - output_channels: Dict[int, Dict] - Channel configs (gain, mute, name)
                - standby: bool - Standby state (optional)

        Raises:
            ValueError: If configuration is invalid
            aiohttp.ClientError: If HTTP request fails

        Example:
            scene = {
                "output_channels": {
                    "0": {"gain": 0.7, "mute": False, "name": "Main L"},
                    "1": {"gain": 0.7, "mute": False, "name": "Main R"},
                    "2": {"gain": 0.5, "mute": False, "name": "Sub"},
                    "3": {"gain": 0.5, "mute": False, "name": "Fill"}
                },
                "standby": False
            }
            await client.apply_scene(scene)
        """
        # Validate configuration
        if "output_channels" not in scene_config:
            raise ValueError("Scene must contain 'output_channels'")

        output_channels = scene_config["output_channels"]
        if not isinstance(output_channels, dict) or len(output_channels) != 4:
            raise ValueError("Scene must contain 4 output channels (0-3)")

        _LOGGER.info("Applying preset to amplifier...")

        # Build write values array
        write_values = []

        # Apply each channel's settings (handle both int and string keys for compatibility)
        for ch_idx in range(4):
            ch_key = str(ch_idx)  # JSON always uses string keys
            if ch_key not in output_channels and ch_idx not in output_channels:
                raise ValueError(f"Missing channel {ch_idx} in preset")

            ch_config = output_channels.get(ch_key, output_channels.get(ch_idx))

            # Validate and write gain
            if "gain" not in ch_config:
                raise ValueError(f"Channel {ch_idx} missing gain")
            gain = ch_config["gain"]
            if not 0.0 <= gain <= 2.0:
                raise ValueError(f"Channel {ch_idx} gain must be between 0.0 and 2.0")

            gain_path = f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Gain/Value"
            write_values.append({
                "id": gain_path,
                "data": {"type": TYPE_FLOAT, "floatValue": float(gain)},
                "single": True
            })

            # Validate and write mute
            if "mute" not in ch_config:
                raise ValueError(f"Channel {ch_idx} missing mute")
            mute = ch_config["mute"]
            if not isinstance(mute, bool):
                raise ValueError(f"Channel {ch_idx} mute must be boolean")

            mute_path = f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Mute/Value"
            write_values.append({
                "id": mute_path,
                "data": {"type": TYPE_BOOL, "boolValue": mute},
                "single": True
            })

        # Apply standby if specified
        if "standby" in scene_config:
            standby = scene_config["standby"]
            if not isinstance(standby, bool):
                raise ValueError("Standby must be boolean")

            # Note: Standby path may not be writeable on all models
            # We'll try to write it but won't fail if it doesn't work
            write_values.append({
                "id": "/Device/Audio/Presets/Live/Generals/Standby/Value",
                "data": {"type": TYPE_BOOL, "boolValue": standby},
                "single": True
            })

        # Send batch write request
        if self._session is None:
            await self.connect()

        payload = {
            "clientId": self.client_id,
            "payload": {
                "type": "ACTION",
                "action": {
                    "type": ACTION_WRITE,
                    "values": write_values
                }
            }
        }

        try:
            async with async_timeout.timeout(self.timeout):
                async with self._session.post(
                    f"{self.base_url}/am",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            # Check results
            action = data.get("payload", {}).get("action", {})
            failed_writes = []
            for value_obj in action.get("values", []):
                if value_obj.get("result") != RESULT_SUCCESS:
                    path = value_obj.get("id")
                    result = value_obj.get("result")
                    # Don't fail on standby errors (may not be writeable)
                    if "Standby" not in path:
                        failed_writes.append(f"{path} (result={result})")
                    else:
                        _LOGGER.warning("Standby write not successful (may not be supported): %s", path)

            if failed_writes:
                raise ValueError(f"Failed to write: {', '.join(failed_writes)}")

            _LOGGER.info("Successfully applied preset")

        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP request failed to %s: %s", self.host, err)
            raise
        except Exception as err:
            _LOGGER.error("Failed to apply preset to %s: %s", self.host, err)
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
