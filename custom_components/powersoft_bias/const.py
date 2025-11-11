"""Constants for the Powersoft Bias integration."""
from typing import Final

DOMAIN: Final = "powersoft_bias"

# Config
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Defaults
DEFAULT_PORT: Final = 80
DEFAULT_SCAN_INTERVAL: Final = 10  # seconds
DEFAULT_TIMEOUT: Final = 5.0  # seconds

# Device info
MANUFACTURER: Final = "Powersoft"

# API paths - Output channels
PATH_CHANNEL_GAIN: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Gain/Value"
PATH_CHANNEL_MUTE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Mute/Value"

# API paths - Input
PATH_INPUT_GAIN: Final = "/Device/Audio/Presets/Live/InputProcess/Inputs/Input-{input}/Gain/Value"
PATH_INPUT_MUTE: Final = "/Device/Audio/Presets/Live/InputProcess/Inputs/Input-{input}/Mute/Value"

# API paths - Device info
PATH_MODEL_NAME: Final = "/Device/Config/Hardware/Model/Name"
PATH_MODEL_SERIAL: Final = "/Device/Config/Hardware/Model/Serial"
PATH_MANUFACTURER: Final = "/Device/Config/Hardware/Manufacturer"

# Number of channels (Bias Q1.5+ = 4 channels)
MAX_CHANNELS: Final = 4
MAX_INPUTS: Final = 4
