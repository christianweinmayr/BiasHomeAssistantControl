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

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
