# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration for **Powersoft Bias series amplifiers** (Q1.5+, Q2, Q5, etc.). Unlike the Mezzo series which use UDP PBus protocol, Bias amplifiers communicate via HTTP REST API on port 80.

## Architecture

### Core Components

**HTTP Client (`bias_http_client.py`)**
- Implements async HTTP communication with Bias amplifiers
- Sends POST requests to `/am` endpoint with JSON payload structure
- Handles three data types: STRING (10), FLOAT (20), BOOL (40)
- Supports READ and WRITE actions with success code validation (RESULT_SUCCESS = 10)
- Manages aiohttp session lifecycle

**Coordinator (`__init__.py:BiasDataUpdateCoordinator`)**
- Uses Home Assistant's DataUpdateCoordinator pattern for polling
- Fetches all channel states (gain + mute) in a single batch request
- Structures data as: `{"channels": {0: {"gain": float, "mute": bool}, ...}}`
- Configurable poll interval (5-300 seconds)

**Config Flow (`config_flow.py`)**
- Validates connection by fetching device info during setup
- Uses serial number as unique_id to prevent duplicate entries
- Collects: host (required), port (default 80), scan_interval (default 10s)

**Platform Entities**
- `number.py`: Gain controls (0.0-2.0 range, 0.01 step) for 4 channels
- `switch.py`: Mute switches for 4 channels
- Both extend CoordinatorEntity and update coordinator data immediately on write

### API Structure

**Request Format:**
```json
{
  "clientId": "home-assistant-{entry_id}",
  "payload": {
    "type": "ACTION",
    "action": {
      "type": "READ|WRITE",
      "values": [
        {"id": "/Device/Audio/...", "single": true}
      ]
    }
  }
}
```

**Response Format:**
- Check `value_obj.get("result") == RESULT_SUCCESS` (10)
- Extract value based on `data.type`: stringValue, floatValue, or boolValue

**Key API Paths:**
- Channel control: `/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{0-3}/Gain|Mute/Value`
- Device info: `/Device/Config/Hardware/Model/Name|Serial`

### Constants (`const.py`)

All API paths use `.format()` for channel indexing:
- `PATH_CHANNEL_GAIN` and `PATH_CHANNEL_MUTE` for output channels
- `PATH_INPUT_GAIN` and `PATH_INPUT_MUTE` defined but not yet implemented
- `MAX_CHANNELS = 4`, `MAX_INPUTS = 4` (for future expansion)

## Development

### Testing Connection

To manually test the API, use curl:
```bash
curl -X POST http://<amplifier-ip>/am \
  -H "Content-Type: application/json" \
  -d '{
    "clientId": "test",
    "payload": {
      "type": "ACTION",
      "action": {
        "type": "READ",
        "values": [
          {"id": "/Device/Config/Hardware/Model/Serial", "single": true}
        ]
      }
    }
  }'
```

### Adding New Parameters

1. Add path constant to `const.py` with `{channel}` or `{input}` placeholder
2. Update coordinator's `_async_update_data()` to include new paths in batch read
3. Create entity class extending `CoordinatorEntity` with appropriate base class
4. Implement read from `self.coordinator.data` and write via `self.coordinator.client.write_value()`
5. Register platform in `PLATFORMS` list in `__init__.py`

### Entity State Management

Entities use optimistic updates: immediately update `self.coordinator.data` after write operations and call `self.async_write_ha_state()` to reflect changes without waiting for next poll cycle.

## Home Assistant Integration

**Entry Point:** Home Assistant loads via `async_setup_entry()` which:
1. Creates BiasHTTPClient with host/port from config
2. Initializes BiasDataUpdateCoordinator with configured poll interval
3. Performs initial data fetch (`async_config_entry_first_refresh()`)
4. Forwards setup to number and switch platforms

**Cleanup:** `async_unload_entry()` unloads platforms and closes HTTP session

## Known Limitations

- Input channel controls (PATH_INPUT_*) are defined but not implemented
- Fixed 4-channel configuration (no dynamic channel detection)
- HTTP only (no HTTPS support)
- Local polling architecture (no push notifications from device)

## Related Projects

See [MezzoHomeAssistantControl](https://github.com/christianweinmayr/MezzoHomeAssistantControl) for the UDP-based Mezzo amplifier integration - uses different protocol but similar entity structure.
