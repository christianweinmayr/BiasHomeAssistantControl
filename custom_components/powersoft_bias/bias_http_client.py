"""
HTTP REST API Client for Powersoft Bias Amplifiers.

The Bias series (e.g., Bias Q1.5+, Q2, Q5) use an HTTP REST API instead of UDP protocol.
This module provides an async client for communicating with these amplifiers.

Protocol: POST /am with JSON payload
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)

# Data type constants
TYPE_STRING = 10
TYPE_FLOAT = 20
TYPE_INT = 30
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
                elif data_type == TYPE_INT:
                    result[path] = data_obj.get("intValue")
                elif data_type == TYPE_BOOL:
                    result[path] = data_obj.get("boolValue")
                else:
                    _LOGGER.warning("Unknown data type %s for %s", data_type, path)

            return result

        except asyncio.TimeoutError:
            _LOGGER.error(
                "Timeout reading %d paths from %s (timeout=%ds)",
                len(paths), self.host, self.timeout
            )
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error("HTTP request failed to %s: %s", self.host, err)
            raise
        except Exception as err:
            _LOGGER.error(
                "Failed to read values from %s: %s (type: %s, paths: %d)",
                self.host, err, type(err).__name__, len(paths)
            )
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

        Reads all output channel gain/mute/name values and standby state,
        plus v0.4.0 DSP parameters (EQ, limiters, crossovers, matrix).

        Returns:
            Dictionary with complete preset configuration ready to save

        Raises:
            aiohttp.ClientError: If HTTP request fails
            ValueError: If response parsing fails
        """
        _LOGGER.info("Capturing current amplifier state (v0.4.0 comprehensive)...")

        # Build list of paths to read
        paths = []

        # Output channels: All parameters
        for channel in range(4):
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Name")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Gain/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Mute/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutPolarity/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutDelay/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutDelay/Value")

            # v0.4.0 - Output IIR EQ (8 bands)
            for band in range(8):
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Enable")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Type/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Fc/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Gain/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Q/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Slope/Value")

            # v0.4.0 - Pre-Output IIR EQ (8 bands)
            for band in range(8):
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Enable")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Type/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Fc/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Gain/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Q/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Slope/Value")

            # v0.4.0 - Limiters (7 types)
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClipLimiter/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClipLimiter/Threshold/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/PeakLimiter/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/PeakLimiter/Threshold/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/VRMSLimiter/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/VRMSLimiter/Threshold/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/IRMSLimiter/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/IRMSLimiter/Threshold/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClampLimiter/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClampLimiter/Threshold/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ThermalLimiter/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ThermalLimiter/Threshold/Value")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/TruePowerLimiter/Enable")
            paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/TruePowerLimiter/Threshold/Value")

            # v0.4.0 - Crossover (2 bands)
            for band in range(2):
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Xover/Bands/Band-{band}/Enable")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Xover/Bands/Band-{band}/Fc/Value")
                paths.append(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Xover/Bands/Band-{band}/Slope/Value")

        # Input channels: All parameters
        for channel in range(4):
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Enable/Value")
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Gain/Value")
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Mute/Value")
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InPolarity/Value")
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ShadingGain/Value")
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InDelay/Enable/Value")
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InDelay/Value")

            # v0.4.0 - Input IIR EQ (7 bands)
            for band in range(7):
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Enable")
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Type/Value")
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Fc/Value")
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Gain/Value")
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Q/Value")
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Slope/Value")

        # v0.4.0 - Matrix mixer (4×4)
        for input_ch in range(4):
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Inputs/Input-{input_ch}/Gain/Value")
            paths.append(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Inputs/Input-{input_ch}/Mute/Value")
        for channel in range(4):
            for input_ch in range(4):
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Channels/Channel-{channel}/Routing/Input-{input_ch}/Gain/Value")
                paths.append(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Channels/Channel-{channel}/Routing/Input-{input_ch}/Mute/Value")

        # System state
        paths.append("/Device/Audio/Presets/Live/Generals/Standby/Value")

        # Read all values
        values = await self.read_values(paths)

        # Helper to convert to boolean (handles int 0/1, strings, etc.)
        def to_bool(value, default=False):
            if isinstance(value, bool):
                return value
            if isinstance(value, int):
                return bool(value)
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return default

        # Structure output channels data (use string keys for JSON compatibility)
        output_channels = {}
        for channel in range(4):
            ch_key = str(channel)
            output_channels[ch_key] = {
                "name": values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Name", f"Output {channel + 1}"),
                "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Enable", True)),
                "gain": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Gain/Value", 1.0)),
                "mute": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Mute/Value", False)),
                "polarity": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutPolarity/Value", False)),
                "delay_enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutDelay/Enable", False)),
                "delay": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutDelay/Value", 0.0)),
                "iir": {},
                "pre_iir": {},
            }

            # v0.4.0 - Output IIR EQ (8 bands)
            for band in range(8):
                band_key = str(band)
                output_channels[ch_key]["iir"][band_key] = {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Enable", False)),
                    "type": int(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Type/Value", 0)),
                    "fc": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Fc/Value", 1000.0)),
                    "gain": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Gain/Value", 1.0)),
                    "q": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Q/Value", 1.0)),
                    "slope": int(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/Bands/Band-{band}/Slope/Value", 12)),
                }

            # v0.4.0 - Pre-Output IIR EQ (8 bands)
            for band in range(8):
                band_key = str(band)
                output_channels[ch_key]["pre_iir"][band_key] = {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Enable", False)),
                    "type": int(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Type/Value", 0)),
                    "fc": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Fc/Value", 1000.0)),
                    "gain": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Gain/Value", 1.0)),
                    "q": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Q/Value", 1.0)),
                    "slope": int(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PreIIR/Bands/Band-{band}/Slope/Value", 12)),
                }

        # Structure input channels data (use string keys for JSON compatibility)
        input_channels = {}
        for channel in range(4):
            ch_key = str(channel)
            input_channels[ch_key] = {
                "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Enable/Value", True)),
                "gain": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Gain/Value", 1.0)),
                "mute": to_bool(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Mute/Value", False)),
                "polarity": to_bool(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InPolarity/Value", False)),
                "shading_gain": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ShadingGain/Value", 1.0)),
                "delay_enable": to_bool(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InDelay/Enable/Value", False)),
                "delay": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InDelay/Value", 0.0)),
                "iir": {},
            }

            # v0.4.0 - Input IIR EQ (7 bands)
            for band in range(7):
                band_key = str(band)
                input_channels[ch_key]["iir"][band_key] = {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Enable", False)),
                    "type": int(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Type/Value", 0)),
                    "fc": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Fc/Value", 1000.0)),
                    "gain": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Gain/Value", 1.0)),
                    "q": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Q/Value", 1.0)),
                    "slope": int(values.get(f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/Bands/Band-{band}/Slope/Value", 12)),
                }

        # v0.4.0 - Structure limiters data
        limiters = {}
        for channel in range(4):
            ch_key = str(channel)
            limiters[ch_key] = {
                "clip": {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClipLimiter/Enable", False)),
                    "threshold": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClipLimiter/Threshold/Value", 1.0)),
                },
                "peak": {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/PeakLimiter/Enable", False)),
                    "threshold": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/PeakLimiter/Threshold/Value", 1.0)),
                },
                "vrms": {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/VRMSLimiter/Enable", False)),
                    "threshold": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/VRMSLimiter/Threshold/Value", 1.0)),
                },
                "irms": {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/IRMSLimiter/Enable", False)),
                    "threshold": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/IRMSLimiter/Threshold/Value", 1.0)),
                },
                "clamp": {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClampLimiter/Enable", False)),
                    "threshold": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ClampLimiter/Threshold/Value", 1.0)),
                },
                "thermal": {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ThermalLimiter/Enable", False)),
                    "threshold": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/ThermalLimiter/Threshold/Value", 1.0)),
                },
                "truepower": {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/TruePowerLimiter/Enable", False)),
                    "threshold": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Limiters/TruePowerLimiter/Threshold/Value", 1.0)),
                },
            }

        # v0.4.0 - Structure crossovers data
        crossovers = {}
        for channel in range(4):
            ch_key = str(channel)
            crossovers[ch_key] = {}
            for band in range(2):
                band_key = str(band)
                crossovers[ch_key][band_key] = {
                    "enable": to_bool(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Xover/Bands/Band-{band}/Enable", False)),
                    "fc": float(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Xover/Bands/Band-{band}/Fc/Value", 1000.0)),
                    "slope": int(values.get(f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Xover/Bands/Band-{band}/Slope/Value", 12)),
                }

        # v0.4.0 - Structure matrix mixer data
        matrix = {"inputs": {}, "channels": {}}
        for input_ch in range(4):
            in_key = str(input_ch)
            matrix["inputs"][in_key] = {
                "gain": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Inputs/Input-{input_ch}/Gain/Value", 1.0)),
                "mute": to_bool(values.get(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Inputs/Input-{input_ch}/Mute/Value", False)),
            }

        for channel in range(4):
            ch_key = str(channel)
            matrix["channels"][ch_key] = {"routing": {}}
            for input_ch in range(4):
                in_key = str(input_ch)
                matrix["channels"][ch_key]["routing"][in_key] = {
                    "gain": float(values.get(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Channels/Channel-{channel}/Routing/Input-{input_ch}/Gain/Value", 1.0)),
                    "mute": to_bool(values.get(f"/Device/Audio/Presets/Live/InputProcess/Matrix/Channels/Channel-{channel}/Routing/Input-{input_ch}/Mute/Value", False)),
                }

        # Build comprehensive preset configuration
        preset_config = {
            "output_channels": output_channels,
            "input_channels": input_channels,
            "limiters": limiters,
            "crossovers": crossovers,
            "matrix": matrix,
            "standby": to_bool(values.get("/Device/Audio/Presets/Live/Generals/Standby/Value", False)),
        }

        _LOGGER.info("Captured state: v0.4.0 comprehensive (channels, EQ, limiters, crossovers, matrix)")
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

        _LOGGER.info("Applying comprehensive preset to amplifier...")

        # Build write values array
        write_values = []

        # =================================================================
        # Apply output channel settings
        # =================================================================
        for ch_idx in range(4):
            ch_key = str(ch_idx)  # JSON always uses string keys
            if ch_key not in output_channels and ch_idx not in output_channels:
                raise ValueError(f"Missing output channel {ch_idx} in preset")

            ch_config = output_channels.get(ch_key, output_channels.get(ch_idx))

            # Enable
            if "enable" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Enable",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["enable"]},
                    "single": True
                })

            # Gain
            if "gain" in ch_config:
                gain = ch_config["gain"]
                if not 0.0 <= gain <= 10.0:
                    raise ValueError(f"Output channel {ch_idx} gain must be between 0.0 and 10.0")
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Gain/Value",
                    "data": {"type": TYPE_FLOAT, "floatValue": float(gain)},
                    "single": True
                })

            # Mute
            if "mute" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Mute/Value",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["mute"]},
                    "single": True
                })

            # Polarity
            if "polarity" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/OutPolarity/Value",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["polarity"]},
                    "single": True
                })

            # Delay enable
            if "delay_enable" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/OutDelay/Enable",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["delay_enable"]},
                    "single": True
                })

            # Delay value
            if "delay" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/OutDelay/Value",
                    "data": {"type": TYPE_FLOAT, "floatValue": float(ch_config["delay"])},
                    "single": True
                })

        # =================================================================
        # Apply input channel settings (if present in preset)
        # =================================================================
        input_channels = scene_config.get("input_channels", {})
        for ch_idx in range(4):
            ch_key = str(ch_idx)
            if ch_key not in input_channels and ch_idx not in input_channels:
                continue  # Input channels are optional in preset

            ch_config = input_channels.get(ch_key, input_channels.get(ch_idx))

            # Enable
            if "enable" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/Enable/Value",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["enable"]},
                    "single": True
                })

            # Gain
            if "gain" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/Gain/Value",
                    "data": {"type": TYPE_FLOAT, "floatValue": float(ch_config["gain"])},
                    "single": True
                })

            # Mute
            if "mute" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/Mute/Value",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["mute"]},
                    "single": True
                })

            # Polarity
            if "polarity" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/InPolarity/Value",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["polarity"]},
                    "single": True
                })

            # Shading gain
            if "shading_gain" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/ShadingGain/Value",
                    "data": {"type": TYPE_FLOAT, "floatValue": float(ch_config["shading_gain"])},
                    "single": True
                })

            # Delay enable
            if "delay_enable" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/InDelay/Enable/Value",
                    "data": {"type": TYPE_BOOL, "boolValue": ch_config["delay_enable"]},
                    "single": True
                })

            # Delay value
            if "delay" in ch_config:
                write_values.append({
                    "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/InDelay/Value",
                    "data": {"type": TYPE_FLOAT, "floatValue": float(ch_config["delay"])},
                    "single": True
                })

            # v0.4.0 - Input IIR EQ parameters (if present)
            if "iir" in ch_config:
                for band_idx in range(7):
                    band_key = str(band_idx)
                    if band_key in ch_config["iir"]:
                        band_config = ch_config["iir"][band_key]

                        if "enable" in band_config:
                            write_values.append({
                                "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/ZoneBlock/IIR/Bands/Band-{band_idx}/Enable",
                                "data": {"type": TYPE_BOOL, "boolValue": band_config["enable"]},
                                "single": True
                            })
                        if "type" in band_config:
                            write_values.append({
                                "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/ZoneBlock/IIR/Bands/Band-{band_idx}/Type/Value",
                                "data": {"type": TYPE_INT, "intValue": int(band_config["type"])},
                                "single": True
                            })
                        if "fc" in band_config:
                            write_values.append({
                                "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/ZoneBlock/IIR/Bands/Band-{band_idx}/Fc/Value",
                                "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["fc"])},
                                "single": True
                            })
                        if "gain" in band_config:
                            write_values.append({
                                "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/ZoneBlock/IIR/Bands/Band-{band_idx}/Gain/Value",
                                "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["gain"])},
                                "single": True
                            })
                        if "q" in band_config:
                            write_values.append({
                                "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/ZoneBlock/IIR/Bands/Band-{band_idx}/Q/Value",
                                "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["q"])},
                                "single": True
                            })
                        if "slope" in band_config:
                            write_values.append({
                                "id": f"/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{ch_idx}/ZoneBlock/IIR/Bands/Band-{band_idx}/Slope/Value",
                                "data": {"type": TYPE_INT, "intValue": int(band_config["slope"])},
                                "single": True
                            })

        # =================================================================
        # v0.4.0 - Apply output channel EQ parameters (if present)
        # =================================================================
        if "output_channels" in scene_config:
            for ch_idx in range(4):
                ch_key = str(ch_idx)
                if ch_key not in scene_config["output_channels"]:
                    continue

                ch_config = scene_config["output_channels"][ch_key]

                # Output IIR EQ (8 bands)
                if "iir" in ch_config:
                    for band_idx in range(8):
                        band_key = str(band_idx)
                        if band_key in ch_config["iir"]:
                            band_config = ch_config["iir"][band_key]

                            if "enable" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/IIR/Bands/Band-{band_idx}/Enable",
                                    "data": {"type": TYPE_BOOL, "boolValue": band_config["enable"]},
                                    "single": True
                                })
                            if "type" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/IIR/Bands/Band-{band_idx}/Type/Value",
                                    "data": {"type": TYPE_INT, "intValue": int(band_config["type"])},
                                    "single": True
                                })
                            if "fc" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/IIR/Bands/Band-{band_idx}/Fc/Value",
                                    "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["fc"])},
                                    "single": True
                                })
                            if "gain" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/IIR/Bands/Band-{band_idx}/Gain/Value",
                                    "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["gain"])},
                                    "single": True
                                })
                            if "q" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/IIR/Bands/Band-{band_idx}/Q/Value",
                                    "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["q"])},
                                    "single": True
                                })
                            if "slope" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/IIR/Bands/Band-{band_idx}/Slope/Value",
                                    "data": {"type": TYPE_INT, "intValue": int(band_config["slope"])},
                                    "single": True
                                })

                # Pre-Output IIR EQ (8 bands)
                if "pre_iir" in ch_config:
                    for band_idx in range(8):
                        band_key = str(band_idx)
                        if band_key in ch_config["pre_iir"]:
                            band_config = ch_config["pre_iir"][band_key]

                            if "enable" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/PreIIR/Bands/Band-{band_idx}/Enable",
                                    "data": {"type": TYPE_BOOL, "boolValue": band_config["enable"]},
                                    "single": True
                                })
                            if "type" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/PreIIR/Bands/Band-{band_idx}/Type/Value",
                                    "data": {"type": TYPE_INT, "intValue": int(band_config["type"])},
                                    "single": True
                                })
                            if "fc" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/PreIIR/Bands/Band-{band_idx}/Fc/Value",
                                    "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["fc"])},
                                    "single": True
                                })
                            if "gain" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/PreIIR/Bands/Band-{band_idx}/Gain/Value",
                                    "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["gain"])},
                                    "single": True
                                })
                            if "q" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/PreIIR/Bands/Band-{band_idx}/Q/Value",
                                    "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["q"])},
                                    "single": True
                                })
                            if "slope" in band_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/PreIIR/Bands/Band-{band_idx}/Slope/Value",
                                    "data": {"type": TYPE_INT, "intValue": int(band_config["slope"])},
                                    "single": True
                                })

        # =================================================================
        # v0.4.0 - Apply limiter settings (if present)
        # =================================================================
        if "limiters" in scene_config:
            for ch_idx in range(4):
                ch_key = str(ch_idx)
                if ch_key not in scene_config["limiters"]:
                    continue

                limiter_config = scene_config["limiters"][ch_key]

                # Clip limiter
                if "clip" in limiter_config:
                    if "enable" in limiter_config["clip"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/ClipLimiter/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": limiter_config["clip"]["enable"]},
                            "single": True
                        })
                    if "threshold" in limiter_config["clip"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/ClipLimiter/Threshold/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(limiter_config["clip"]["threshold"])},
                            "single": True
                        })

                # Peak limiter
                if "peak" in limiter_config:
                    if "enable" in limiter_config["peak"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/PeakLimiter/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": limiter_config["peak"]["enable"]},
                            "single": True
                        })
                    if "threshold" in limiter_config["peak"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/PeakLimiter/Threshold/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(limiter_config["peak"]["threshold"])},
                            "single": True
                        })

                # VRMS limiter
                if "vrms" in limiter_config:
                    if "enable" in limiter_config["vrms"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/VRMSLimiter/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": limiter_config["vrms"]["enable"]},
                            "single": True
                        })
                    if "threshold" in limiter_config["vrms"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/VRMSLimiter/Threshold/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(limiter_config["vrms"]["threshold"])},
                            "single": True
                        })

                # IRMS limiter
                if "irms" in limiter_config:
                    if "enable" in limiter_config["irms"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/IRMSLimiter/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": limiter_config["irms"]["enable"]},
                            "single": True
                        })
                    if "threshold" in limiter_config["irms"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/IRMSLimiter/Threshold/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(limiter_config["irms"]["threshold"])},
                            "single": True
                        })

                # Clamp limiter
                if "clamp" in limiter_config:
                    if "enable" in limiter_config["clamp"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/ClampLimiter/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": limiter_config["clamp"]["enable"]},
                            "single": True
                        })
                    if "threshold" in limiter_config["clamp"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/ClampLimiter/Threshold/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(limiter_config["clamp"]["threshold"])},
                            "single": True
                        })

                # Thermal limiter
                if "thermal" in limiter_config:
                    if "enable" in limiter_config["thermal"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/ThermalLimiter/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": limiter_config["thermal"]["enable"]},
                            "single": True
                        })
                    if "threshold" in limiter_config["thermal"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/ThermalLimiter/Threshold/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(limiter_config["thermal"]["threshold"])},
                            "single": True
                        })

                # TruePower limiter
                if "truepower" in limiter_config:
                    if "enable" in limiter_config["truepower"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/TruePowerLimiter/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": limiter_config["truepower"]["enable"]},
                            "single": True
                        })
                    if "threshold" in limiter_config["truepower"]:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Limiters/TruePowerLimiter/Threshold/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(limiter_config["truepower"]["threshold"])},
                            "single": True
                        })

        # =================================================================
        # v0.4.0 - Apply crossover settings (if present)
        # =================================================================
        if "crossovers" in scene_config:
            for ch_idx in range(4):
                ch_key = str(ch_idx)
                if ch_key not in scene_config["crossovers"]:
                    continue

                xover_config = scene_config["crossovers"][ch_key]
                for band_idx in range(2):
                    band_key = str(band_idx)
                    if band_key not in xover_config:
                        continue

                    band_config = xover_config[band_key]

                    if "enable" in band_config:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Xover/Bands/Band-{band_idx}/Enable",
                            "data": {"type": TYPE_BOOL, "boolValue": band_config["enable"]},
                            "single": True
                        })
                    if "fc" in band_config:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Xover/Bands/Band-{band_idx}/Fc/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(band_config["fc"])},
                            "single": True
                        })
                    if "slope" in band_config:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{ch_idx}/Xover/Bands/Band-{band_idx}/Slope/Value",
                            "data": {"type": TYPE_INT, "intValue": int(band_config["slope"])},
                            "single": True
                        })

        # =================================================================
        # v0.4.0 - Apply matrix mixer settings (if present)
        # =================================================================
        if "matrix" in scene_config:
            matrix_config = scene_config["matrix"]

            # Matrix input gains/mutes
            if "inputs" in matrix_config:
                for input_idx in range(4):
                    in_key = str(input_idx)
                    if in_key not in matrix_config["inputs"]:
                        continue

                    input_config = matrix_config["inputs"][in_key]

                    if "gain" in input_config:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/InputProcess/Matrix/Inputs/Input-{input_idx}/Gain/Value",
                            "data": {"type": TYPE_FLOAT, "floatValue": float(input_config["gain"])},
                            "single": True
                        })
                    if "mute" in input_config:
                        write_values.append({
                            "id": f"/Device/Audio/Presets/Live/InputProcess/Matrix/Inputs/Input-{input_idx}/Mute/Value",
                            "data": {"type": TYPE_BOOL, "boolValue": input_config["mute"]},
                            "single": True
                        })

            # Matrix channel routing gains/mutes
            if "channels" in matrix_config:
                for ch_idx in range(4):
                    ch_key = str(ch_idx)
                    if ch_key not in matrix_config["channels"]:
                        continue

                    channel_config = matrix_config["channels"][ch_key]

                    if "routing" in channel_config:
                        for input_idx in range(4):
                            in_key = str(input_idx)
                            if in_key not in channel_config["routing"]:
                                continue

                            routing_config = channel_config["routing"][in_key]

                            if "gain" in routing_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/InputProcess/Matrix/Channels/Channel-{ch_idx}/Routing/Input-{input_idx}/Gain/Value",
                                    "data": {"type": TYPE_FLOAT, "floatValue": float(routing_config["gain"])},
                                    "single": True
                                })
                            if "mute" in routing_config:
                                write_values.append({
                                    "id": f"/Device/Audio/Presets/Live/InputProcess/Matrix/Channels/Channel-{ch_idx}/Routing/Input-{input_idx}/Mute/Value",
                                    "data": {"type": TYPE_BOOL, "boolValue": routing_config["mute"]},
                                    "single": True
                                })

        # =================================================================
        # Apply standby if specified
        # =================================================================
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
