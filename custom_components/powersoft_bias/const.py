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

# Number of channels/bands
MAX_CHANNELS: Final = 4
MAX_INPUTS: Final = 4
MAX_OUTPUT_EQ_BANDS: Final = 16  # Output IIR filters
MAX_PRE_OUTPUT_EQ_BANDS: Final = 8  # Pre-output IIR filters
MAX_INPUT_EQ_BANDS: Final = 7  # Input zone block IIR filters
MAX_XOVER_BANDS: Final = 2  # Crossover bands per channel
MAX_DYNAMIC_EQ_BANDS: Final = 3  # Dynamic EQ bands per channel

# =============================================================================
# API PATH TEMPLATES - Output Process (Currently Implemented)
# =============================================================================

PATH_CHANNEL_NAME: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Name"
PATH_CHANNEL_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Enable"
PATH_CHANNEL_GAIN: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Gain/Value"
PATH_CHANNEL_MUTE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/Mute/Value"
PATH_CHANNEL_POLARITY: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutPolarity/Value"
PATH_CHANNEL_OUT_DELAY_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutDelay/Enable"
PATH_CHANNEL_OUT_DELAY_VALUE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/OutDelay/Value"

# =============================================================================
# API PATH TEMPLATES - Input Process
# =============================================================================

PATH_INPUT_ENABLE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Enable/Value"
PATH_INPUT_GAIN: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Gain/Value"
PATH_INPUT_MUTE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/Mute/Value"
PATH_INPUT_POLARITY: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InPolarity/Value"
PATH_INPUT_SHADING_GAIN: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ShadingGain/Value"
PATH_INPUT_DELAY_ENABLE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InDelay/Enable/Value"
PATH_INPUT_DELAY_VALUE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InDelay/Value"

# Input Zone Block EQ (7 bands per input)
PATH_INPUT_EQ_ENABLE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/InputEQ/Enable/Value"
PATH_INPUT_ZONE_ENABLE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/Enable/Value"
PATH_INPUT_ZONE_GAIN: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/Gain/Value"
PATH_INPUT_ZONE_IIR_ENABLE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/IIR-{band}/Enable"
PATH_INPUT_ZONE_IIR_FC: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/IIR-{band}/Fc/Value"
PATH_INPUT_ZONE_IIR_GAIN: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/IIR-{band}/Gain/Value"
PATH_INPUT_ZONE_IIR_Q: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/IIR-{band}/Q/Value"
PATH_INPUT_ZONE_IIR_SLOPE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/IIR-{band}/Slope/Value"
PATH_INPUT_ZONE_IIR_TYPE: Final = "/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{channel}/ZoneBlock/IIR/IIR-{band}/Type/Value"

# =============================================================================
# API PATH TEMPLATES - Output IIR EQ (16 bands per output)
# =============================================================================

PATH_OUTPUT_IIR_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Enable"
PATH_OUTPUT_IIR_FC: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Fc/Value"
PATH_OUTPUT_IIR_GAIN: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Gain/Value"
PATH_OUTPUT_IIR_Q: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Q/Value"
PATH_OUTPUT_IIR_SLOPE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Slope/Value"
PATH_OUTPUT_IIR_TYPE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Type/Value"

# =============================================================================
# API PATH TEMPLATES - Pre-Output Process
# =============================================================================

PATH_PRE_OUTPUT_GAIN: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/Gain/Value"
PATH_PRE_OUTPUT_MUTE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/Mute/Value"
PATH_PRE_OUTPUT_POLARITY: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/Polarity/Value"
PATH_PRE_OUTPUT_DELAY_ENABLE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/Delay/Enable"
PATH_PRE_OUTPUT_DELAY_VALUE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/Delay/Value"

# Pre-Output IIR EQ (8 bands)
PATH_PRE_OUTPUT_IIR_ENABLE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Enable"
PATH_PRE_OUTPUT_IIR_FC: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Fc/Value"
PATH_PRE_OUTPUT_IIR_GAIN: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Gain/Value"
PATH_PRE_OUTPUT_IIR_Q: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Q/Value"
PATH_PRE_OUTPUT_IIR_SLOPE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Slope/Value"
PATH_PRE_OUTPUT_IIR_TYPE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/IIR/IIR-{band}/Type/Value"

# =============================================================================
# API PATH TEMPLATES - Crossovers (2 bands per channel)
# =============================================================================

PATH_XOVER_ENABLE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/XOver/XOver-{band}/Enable"
PATH_XOVER_FC: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/XOver/XOver-{band}/Fc/Value"
PATH_XOVER_SLOPE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/XOver/XOver-{band}/Slope/Value"
PATH_XOVER_TYPE: Final = "/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{channel}/XOver/XOver-{band}/Type/Value"

# =============================================================================
# API PATH TEMPLATES - Limiters (7 types per channel)
# =============================================================================

# Clip Limiter
PATH_LIMITER_CLIP_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ClipLimiter/Enable"
PATH_LIMITER_CLIP_THRESHOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ClipLimiter/Threshold/Value"
PATH_LIMITER_CLIP_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ClipLimiter/AttackTime/Value"
PATH_LIMITER_CLIP_HOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ClipLimiter/HoldTime/Value"
PATH_LIMITER_CLIP_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ClipLimiter/ReleaseTime/Value"

# Peak Limiter
PATH_LIMITER_PEAK_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PeakLimiter/Enable"
PATH_LIMITER_PEAK_THRESHOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PeakLimiter/Threshold/Value"
PATH_LIMITER_PEAK_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PeakLimiter/AttackTime/Value"
PATH_LIMITER_PEAK_HOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PeakLimiter/HoldTime/Value"
PATH_LIMITER_PEAK_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PeakLimiter/ReleaseTime/Value"

# Voltage Limiter RMS
PATH_LIMITER_VRMS_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/VoltageLimiterRMS/Enable"
PATH_LIMITER_VRMS_THRESHOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/VoltageLimiterRMS/Threshold/Value"
PATH_LIMITER_VRMS_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/VoltageLimiterRMS/AttackTime/Value"
PATH_LIMITER_VRMS_HOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/VoltageLimiterRMS/HoldTime/Value"
PATH_LIMITER_VRMS_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/VoltageLimiterRMS/ReleaseTime/Value"

# Current Limiter RMS
PATH_LIMITER_IRMS_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentLimiterRMS/Enable"
PATH_LIMITER_IRMS_THRESHOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentLimiterRMS/Threshold/Value"
PATH_LIMITER_IRMS_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentLimiterRMS/AttackTime/Value"
PATH_LIMITER_IRMS_HOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentLimiterRMS/HoldTime/Value"
PATH_LIMITER_IRMS_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentLimiterRMS/ReleaseTime/Value"

# Current Clamp
PATH_LIMITER_CLAMP_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentClamp/Enable"
PATH_LIMITER_CLAMP_THRESHOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentClamp/Threshold/Value"
PATH_LIMITER_CLAMP_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentClamp/AttackTime/Value"
PATH_LIMITER_CLAMP_HOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentClamp/HoldTime/Value"
PATH_LIMITER_CLAMP_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/CurrentClamp/ReleaseTime/Value"

# Thermal Limiter
PATH_LIMITER_THERMAL_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ThermalLimiter/Enable"
PATH_LIMITER_THERMAL_THRESHOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ThermalLimiter/Threshold/Value"
PATH_LIMITER_THERMAL_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ThermalLimiter/AttackTime/Value"
PATH_LIMITER_THERMAL_HOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ThermalLimiter/HoldTime/Value"
PATH_LIMITER_THERMAL_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/ThermalLimiter/ReleaseTime/Value"

# TruePower Limiter
PATH_LIMITER_TRUEPOWER_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/TruePowerLimiter/Enable"
PATH_LIMITER_TRUEPOWER_THRESHOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/TruePowerLimiter/Threshold/Value"
PATH_LIMITER_TRUEPOWER_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/TruePowerLimiter/AttackTime/Value"
PATH_LIMITER_TRUEPOWER_HOLD: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/TruePowerLimiter/HoldTime/Value"
PATH_LIMITER_TRUEPOWER_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/TruePowerLimiter/ReleaseTime/Value"

# =============================================================================
# API PATH TEMPLATES - Dynamic EQ (3 bands per channel)
# =============================================================================

PATH_DYNAMIC_EQ_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/DynamicEq/DYNAMICEQ-{band}/Enable"
PATH_DYNAMIC_EQ_TYPE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/DynamicEq/DYNAMICEQ-{band}/FilterType/Value"
PATH_DYNAMIC_EQ_FC: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/DynamicEq/DYNAMICEQ-{band}/Fc/Value"
PATH_DYNAMIC_EQ_Q: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/DynamicEq/DYNAMICEQ-{band}/Q/Value"
PATH_DYNAMIC_EQ_RATIO: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/DynamicEq/DYNAMICEQ-{band}/Ratio/Value"
PATH_DYNAMIC_EQ_ATTACK: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/DynamicEq/DYNAMICEQ-{band}/AttackTime/Value"
PATH_DYNAMIC_EQ_RELEASE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/DynamicEq/DYNAMICEQ-{band}/ReleaseTime/Value"

# =============================================================================
# API PATH TEMPLATES - Monitoring
# =============================================================================

PATH_PILOT_TONE_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PilotTone/Enable"
PATH_PILOT_TONE_FREQ: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/PilotTone/Freq/Value"
PATH_LOAD_MONITOR_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/LoadMonitor/Enable"
PATH_LOAD_MONITOR_FREQ: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/LoadMonitor/Freq/Value"
PATH_NOMINAL_IMPEDANCE_ENABLE: Final = "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{channel}/NominalImpedance/Enable"

# =============================================================================
# API PATH TEMPLATES - Input Matrix (Mixer)
# =============================================================================

PATH_MATRIX_IN_GAIN: Final = "/Device/Audio/Presets/Live/InputMatrix/InGain-{input}/Value"
PATH_MATRIX_IN_MUTE: Final = "/Device/Audio/Presets/Live/InputMatrix/InMute-{input}/Value"
PATH_MATRIX_CHANNEL_GAIN: Final = "/Device/Audio/Presets/Live/InputMatrix/Channels/Channel-{channel}/Gain-{input}/Value"
PATH_MATRIX_CHANNEL_MUTE: Final = "/Device/Audio/Presets/Live/InputMatrix/Channels/Channel-{channel}/Mute-{input}/Value"

# =============================================================================
# API PATH TEMPLATES - Source Selection & Routing
# =============================================================================

PATH_ANALOG_INPUT_GAIN: Final = "/Device/Audio/Presets/Live/SourceSelection/AnalogInput/Gain/Value"
PATH_ANALOG_INPUT_DELAY: Final = "/Device/Audio/Presets/Live/SourceSelection/AnalogInput/Delay/Value"
PATH_AES3_INPUT_GAIN: Final = "/Device/Audio/Presets/Live/SourceSelection/AES3Input/Gain/Value"
PATH_AES3_INPUT_DELAY: Final = "/Device/Audio/Presets/Live/SourceSelection/AES3Input/Delay/Value"
PATH_NET_STREAM_0_GAIN: Final = "/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain0/Gain/Value"
PATH_NET_STREAM_0_DELAY: Final = "/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain0/Delay/Value"
PATH_NET_STREAM_1_GAIN: Final = "/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain1/Gain/Value"
PATH_NET_STREAM_1_DELAY: Final = "/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain1/Delay/Value"

PATH_ROUTING_SRC: Final = "/Device/Audio/Presets/Live/SourceSelection/RoutingChannel-{channel}/Src-{src}/Value"

# =============================================================================
# API PATH TEMPLATES - System
# =============================================================================

PATH_STANDBY: Final = "/Device/Audio/Presets/Live/Generals/Standby/Value"
PATH_SIGNAL_GENERATOR_ENABLE: Final = "/Device/Audio/Presets/Live/Generals/SignalGenerator/Enable/Value"
PATH_SIGNAL_GENERATOR_GAIN: Final = "/Device/Audio/Presets/Live/Generals/SignalGenerator/Gain/Value"

# =============================================================================
# API PATH TEMPLATES - Device info
# =============================================================================

PATH_DEVICE_NAME: Final = "/Device/Config/Name"
PATH_MODEL_NAME: Final = "/Device/Config/Hardware/Model/Name"
PATH_MODEL_SERIAL: Final = "/Device/Config/Hardware/Model/Serial"
PATH_MANUFACTURER: Final = "/Device/Config/Hardware/Manufacturer"
PATH_FIRMWARE_VERSION: Final = "/Device/Config/Software/Firmware/Version"
PATH_MAC_ADDRESS: Final = "/Device/Config/Hardware/Model/Mac"

# =============================================================================
# EQ Filter Types
# =============================================================================

EQ_FILTER_TYPES: Final = {
    "0": "Peaking",
    "1": "Low Shelf",
    "2": "High Shelf",
    "3": "Low Pass",
    "4": "High Pass",
    "5": "Band Pass",
    "6": "Notch",
    "7": "All Pass",
}

# =============================================================================
# Data coordinator keys
# =============================================================================

COORDINATOR: Final = "coordinator"
CLIENT: Final = "client"
SCENE_MANAGER: Final = "scene_manager"
ACTIVE_SCENE_ID: Final = "active_scene_id"

# Entity unique ID prefixes
UID_SCENE: Final = "scene"

# Default scenes (empty - users create their own)
DEFAULT_SCENES: Final = []
