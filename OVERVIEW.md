# Powersoft Bias Home Assistant Integration - Overview

This document provides a comprehensive overview of the Powersoft Bias Home Assistant integration, including the API structure, implementation details, and preset system.

## Table of Contents

1. [Project Overview](#project-overview)
2. [API Structure](#api-structure)
3. [Signal Chain](#signal-chain)
4. [Current Features](#current-features)
5. [Preset System](#preset-system)
6. [Available Parameters](#available-parameters)
7. [Future Expansion](#future-expansion)

---

## Project Overview

### What is This Integration?

A Home Assistant custom integration for **Powersoft Bias series amplifiers** (Q1.5+, Q2, Q5) that provides:
- Real-time control of channel gains and mutes
- Preset management system for saving/recalling configurations
- HTTP REST API communication (unlike Mezzo which uses UDP)
- Complete DSP access (planned future expansion)

### Supported Models

- Void Acoustics Bias Q1.5+
- Powersoft Bias Q2
- Powersoft Bias Q5
- Other Bias series amplifiers with HTTP API

### Key Differences from Mezzo Integration

| Feature | Mezzo | Bias |
|---------|-------|------|
| Protocol | UDP PBus | HTTP REST (JSON) |
| Port | 8002 (UDP) | 80 (HTTP) |
| Data Format | Binary | JSON |
| API Style | Memory-mapped registers | REST endpoints |
| Discovery | UDP broadcast | HTTP endpoint |

---

## API Structure

### Base Communication

**Endpoint:** `POST http://{amplifier-ip}/am`
**Content-Type:** `application/json`

### Request Format

```json
{
  "clientId": "home-assistant",
  "payload": {
    "type": "ACTION",
    "action": {
      "type": "READ|WRITE",
      "values": [
        {
          "id": "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-0/Gain/Value",
          "single": true
        }
      ]
    }
  }
}
```

### Response Format

```json
{
  "version": "1.0.0",
  "clientId": "home-assistant",
  "payload": {
    "type": 100,
    "action": {
      "type": 10,
      "values": [
        {
          "id": "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-0/Gain/Value",
          "data": {
            "type": 20,
            "floatValue": 1.0
          },
          "result": 10
        }
      ]
    }
  },
  "updateId": 48
}
```

### Data Types

| Code | Type | Value Field |
|------|------|-------------|
| 10 | String | `stringValue` |
| 20 | Float | `floatValue` |
| 40 | Boolean | `boolValue` |

### Result Codes

- `10` = Success (RESULT_SUCCESS)
- Other codes indicate errors

---

## Signal Chain

The Bias amplifier processes audio through this chain:

```
Input Sources (Analog/AES3/Network)
    ↓
SourceSelection (Routing + Backup Strategies)
    ↓
InputProcess/Channels (Input EQ, Gain, Delay)
    ↓
InputMatrix (Matrix Mixer)
    ↓
PreOutputProcess (Speaker Tuning EQ, XOver)
    ↓
OutputProcess (Final Gain, Limiters, Protection)
    ↓
Physical Outputs (Channel 0-3)
```

Each stage provides comprehensive control over the audio signal path.

---

## Current Features

### Version 0.2.0

#### Output Channel Control
- **Gain Control** (Number entities)
  - Range: 0.0 - 2.0 (linear)
  - Step: 0.01
  - Real-time updates

- **Mute Control** (Switch entities)
  - Per-channel mute on/off
  - Immediate response

#### Preset System (NEW in v0.2.0)
- **Save/Recall Presets**
  - Capture current amplifier state
  - Apply saved configurations
  - Update existing presets
  - Delete unwanted presets

- **Button Entities**
  - Apply preset buttons
  - Update preset buttons
  - Delete preset buttons
  - Create preset button

- **Services**
  - `save_preset` - Create new preset
  - `update_preset` - Update existing
  - `delete_preset` - Remove preset
  - `rename_preset` - Change preset name

#### Device Information
- Model name
- Serial number
- Manufacturer
- Firmware version
- Network configuration

---

## Preset System

### What Gets Saved

Current implementation captures:
- ✅ Output channel gains (0.0-2.0)
- ✅ Output channel mutes (true/false)
- ✅ Output channel names (strings)
- ✅ Standby state (if available)

### Preset Workflow

```
1. User adjusts amplifier settings
   ↓
2. Press "Create Preset" button (or call service)
   ↓
3. capture_current_state() reads all parameters via API
   ↓
4. SceneManager validates and stores preset
   ↓
5. Preset saved to .storage/powersoft_bias_presets_{entry_id}
   ↓
6. Button entities created for apply/update/delete
```

### Applying Presets

```
1. User presses "Apply Preset" button
   ↓
2. apply_scene() builds batch write request
   ↓
3. All parameters written in single API call
   ↓
4. Coordinator refreshes to show new state
```

### Storage

Presets are stored in Home Assistant's `.storage` directory:
- **Format:** JSON
- **Location:** `.storage/powersoft_bias_presets_{entry_id}`
- **Backup:** Included in HA snapshots
- **Persistence:** Survives HA restarts

---

## Available Parameters

Based on API discovery (see [API_DISCOVERY.md](API_DISCOVERY.md)), the amplifier exposes **hundreds of parameters**:

### Output Channels (Per Channel 0-3)

**Basic Controls** (Implemented ✅)
- Gain/Value (0.0-2.0) - ✅
- Mute/Value (boolean) - ✅
- Name (string) - ✅
- Enable (boolean)
- OutPolarity/Value (phase)

**Delay**
- OutDelay/Enable
- OutDelay/Value (delay time)

**IIR Filters (16 bands per channel)**
- IIR/IIR-{0-15}/Enable
- IIR/IIR-{0-15}/Fc/Value (frequency)
- IIR/IIR-{0-15}/Gain/Value (dB)
- IIR/IIR-{0-15}/Q/Value (Q factor)
- IIR/IIR-{0-15}/Type/Value (filter type)

**Crossovers (2 bands per channel)**
- XOver/XOver-{0-1}/Enable
- XOver/XOver-{0-1}/Fc/Value
- XOver/XOver-{0-1}/Slope/Value
- XOver/XOver-{0-1}/Type/Value

**Dynamic EQ (3 bands per channel)**
- DynamicEq/DYNAMICEQ-{0-2}/Enable
- DynamicEq/DYNAMICEQ-{0-2}/FilterType/Value
- DynamicEq/DYNAMICEQ-{0-2}/Fc/Value
- DynamicEq/DYNAMICEQ-{0-2}/Q/Value
- DynamicEq/DYNAMICEQ-{0-2}/Ratio/Value
- DynamicEq/DYNAMICEQ-{0-2}/AttackTime/Value
- DynamicEq/DYNAMICEQ-{0-2}/ReleaseTime/Value

**Limiters & Protection** (7 types per channel)
- ClipLimiter (Enable, Threshold, Attack, Hold, Release)
- PeakLimiter (Enable, Threshold, Attack, Hold, Release)
- VoltageLimiterRMS (Enable, Threshold, Attack, Hold, Release)
- CurrentLimiterRMS (Enable, Threshold, Attack, Hold, Release)
- CurrentClamp (Enable, Threshold, Attack, Hold, Release)
- ThermalLimiter (Enable, Threshold, Attack, Hold, Release)
- TruePowerLimiter (Enable, Threshold, Attack, Hold, Release)

**Monitoring**
- PilotTone (Enable, Freq, Low, High)
- LoadMonitor (Enable, Freq, Low, High)
- NominalImpedance (Enable, Low, High)

### Input Channels (Per Channel 0-3)

**Basic Controls**
- Gain/Value
- Mute/Value
- InPolarity/Value (phase)
- ShadingGain/Value
- Enable/Value

**Input Delay**
- InDelay/Enable/Value
- InDelay/Value

**Input EQ**
- InputEQ/Enable/Value

**Zone Block** (7-band IIR per input)
- ZoneBlock/Enable/Value
- ZoneBlock/Gain/Value
- ZoneBlock/IIR/IIR-{0-6}/... (full IIR parameters)

### Routing & Matrix

**Input Matrix Mixer**
- InGain-{0-9}/Value (input source gains)
- InMute-{0-9}/Value (input source mutes)
- Channels/Channel-{0-3}/Gain-{0-3}/Value (matrix routing)
- Channels/Channel-{0-3}/Mute-{0-3}/Value (matrix muting)

**Source Selection**
- AnalogInput/Gain/Value
- AnalogInput/Delay/Value
- AES3Input/Gain/Value
- AES3Input/Delay/Value
- NetStreamGroupGain0/Gain/Value
- NetStreamGroupGain1/Gain/Value

**Backup Strategies** (4 strategies)
- BackupStrategy-{0-3}/Enable/Value
- BackupStrategy-{0-3}/Priority-{0-3}/Value
- BackupStrategy-{0-3}/PilotTone/Enable/Value
- BackupStrategy-{0-3}/PilotTone/Freq/Value

### System Settings

**General**
- Standby/Value (power state)
- SignalGenerator/Enable/Value
- SignalGenerator/Gain/Value
- EnergySave/Freq/Value
- EnergySave/Time/Value
- EnergySave/Max/Value
- Gpi/Mode-{0-3}/Value (GPIO configuration)

**Device Information**
- Config/Name (device name)
- Config/Hardware/Model/Name
- Config/Hardware/Model/Serial
- Config/Hardware/Model/Mac
- Config/Software/Firmware/Version

**Network Configuration**
- Networking/Ethernet/Dhcp/Enable
- Networking/Ethernet/Ip
- Networking/Ethernet/Netmask
- Networking/Ethernet/Gateway
- Networking/Ethernet/Dns

---

## Future Expansion

### Short-Term Roadmap (v0.3.0)

**Input Channel Controls**
- Input gain entities
- Input mute switches
- Input polarity switches
- Add to preset system

**Output Delay**
- Delay time number entities
- Delay enable switches
- Include in presets

**Channel Enable/Disable**
- Enable switches per channel
- Include in presets

### Medium-Term Roadmap (v0.4.0)

**Parametric EQ (16 bands per output)**
- Select entity for band selection
- Number entities for Fc, Gain, Q
- Select entity for filter type
- Switch for enable/disable
- Include in presets

**Matrix Mixer**
- Number entities for routing gains
- Switch entities for routing mutes
- Custom card for matrix view

**Limiters Monitoring**
- Sensor entities for gain reduction
- Binary sensors for limiter active
- Threshold number entities

### Long-Term Roadmap (v0.5.0+)

**Advanced DSP**
- Crossover configuration
- Dynamic EQ settings
- FIR filter management

**System Features**
- Input source selection
- Backup strategy configuration
- Network configuration

**Preset Enhancements**
- Import/export presets as JSON
- Preset comparison tool
- Partial presets (specific parameters only)
- Preset templates library

---

## Implementation Priority

Based on user value and complexity:

| Priority | Feature | Value | Complexity | Version |
|----------|---------|-------|------------|---------|
| ✅ Done | Output gain/mute | High | Low | v0.1.0 |
| ✅ Done | Preset system | High | Medium | v0.2.0 |
| 🔄 Next | Input controls | High | Low | v0.3.0 |
| 🔄 Next | Channel delays | Medium | Low | v0.3.0 |
| 📋 Later | Parametric EQ | High | High | v0.4.0 |
| 📋 Later | Matrix mixer | Medium | Medium | v0.4.0 |
| 📋 Later | Limiter monitoring | Medium | Low | v0.4.0 |
| 📋 Later | Crossovers | Low | High | v0.5.0 |
| 📋 Later | Network config | Low | Low | v0.5.0 |

---

## Technical Architecture

### File Structure

```
custom_components/powersoft_bias/
├── __init__.py              # Integration setup, coordinator, services
├── bias_http_client.py      # HTTP API client
├── scene_manager.py         # Preset storage manager
├── button.py                # Preset button entities
├── number.py                # Gain control entities
├── switch.py                # Mute control entities
├── config_flow.py           # Configuration UI
├── const.py                 # Constants and paths
├── services.yaml            # Service definitions
├── manifest.json            # Integration metadata
├── strings.json             # UI strings
└── translations/
    └── en.json              # English translations
```

### Key Classes

**BiasHTTPClient**
- Async HTTP communication
- Batch read/write operations
- `capture_current_state()` for presets
- `apply_scene()` for preset application

**SceneManager**
- Persistent storage (Home Assistant Store)
- CRUD operations for presets
- Validation
- Auto-incrementing IDs

**BiasDataUpdateCoordinator**
- Periodic polling (configurable interval)
- Batch data fetching
- State caching
- Error handling

### Data Flow

```
User Action
    ↓
Home Assistant Entity/Service
    ↓
BiasHTTPClient (HTTP POST /am)
    ↓
Bias Amplifier (JSON response)
    ↓
BiasDataUpdateCoordinator (state update)
    ↓
Entity State Update
    ↓
UI Refresh
```

---

## Resources

- **API Discovery:** [API_DISCOVERY.md](API_DISCOVERY.md) - Complete parameter reference
- **Preset Implementation:** [PRESET_IMPLEMENTATION.md](PRESET_IMPLEMENTATION.md) - Preset system details
- **Development Guide:** [CLAUDE.md](CLAUDE.md) - Integration architecture
- **README:** [README.md](README.md) - Installation and basic usage
- **GitHub:** https://github.com/christianweinmayr/BiasHomeAssistantControl

---

## Support & Contributing

### Getting Help

- Check logs in Home Assistant (Configuration → Logs)
- Review documentation files
- Open GitHub issue with logs and configuration

### Contributing

Contributions welcome for:
- New parameter implementations
- UI improvements
- Documentation enhancements
- Bug fixes
- Testing on different Bias models

### Testing

Test the integration with your Bias amplifier:
1. Install via HACS
2. Configure via UI
3. Test basic controls (gain, mute)
4. Create and apply presets
5. Report any issues

---

## Version History

**v0.2.0** (2025-01-20)
- ✅ Added preset system
- ✅ Button entities for presets
- ✅ Services for preset management
- ✅ Persistent storage
- ✅ Batch API operations

**v0.1.0** (2025-01-19)
- ✅ Initial release
- ✅ Output gain controls
- ✅ Output mute switches
- ✅ Device discovery
- ✅ Config flow
- ✅ HACS support

---

## License

MIT License - See LICENSE file for details

## Credits

Developed by Christian Weinmayr

Related project: [MezzoHomeAssistantControl](https://github.com/christianweinmayr/MezzoHomeAssistantControl) - UDP-based Mezzo amplifier integration
