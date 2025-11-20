# Powersoft Bias Q1.5+ REST API - Complete Discovery

This document contains comprehensive information about all available parameters discovered through the Bias amplifier REST API.

## Device Information

**Model:** Bias Q1.5+ (Quattrocanali Q2404)
**Manufacturer:** Powersoft
**Serial Number:** 1207269
**Firmware Version:** 1.12.0.84
**MAC Address:** 00:21:84:00:00:01
**Channels:** 4 output channels, 4 input channels

## API Structure

### Base Endpoint
- **URL:** `POST http://{ip}/am`
- **Content-Type:** `application/json`

### Request Format
```json
{
  "clientId": "client-identifier",
  "payload": {
    "type": "ACTION",
    "action": {
      "type": "READ|WRITE",
      "values": [
        {"id": "/path/to/parameter", "single": true|false}
      ]
    }
  }
}
```

### Data Types
- `10` = String (`stringValue`)
- `20` = Float (`floatValue`)
- `40` = Boolean (`boolValue`)

### Response Result Codes
- `10` = Success (RESULT_SUCCESS)

## Device Configuration Paths

### Hardware Information
```
/Device/Config/Name                              - "Bias Q1.5+"
/Device/Config/EASY_SWAP_ID                      - Device ID
/Device/Config/PROJECT_INFO                      - Project description
/Device/Config/Hardware/Channels                 - "4"
/Device/Config/Hardware/Model/Manufacturer       - "Powersoft"
/Device/Config/Hardware/Model/Family             - "Quattrocanali"
/Device/Config/Hardware/Model/Model              - "Q2404"
/Device/Config/Hardware/Model/Serial             - Serial number
/Device/Config/Hardware/Model/Mac                - MAC address
```

### Software Information
```
/Device/Config/Software/Firmware/Version         - Firmware version
```

### Network Configuration
```
/Device/Config/Networking/Ethernet/Dhcp/Enable   - DHCP mode
/Device/Config/Networking/Ethernet/Ip            - IP address
/Device/Config/Networking/Ethernet/Netmask       - Subnet mask
/Device/Config/Networking/Ethernet/Gateway       - Gateway IP
/Device/Config/Networking/Ethernet/Dns           - DNS server
```

## Audio Processing Hierarchy

The audio processing chain is structured as:
1. **SourceSelection** - Input routing and backup strategies
2. **InputProcess** - Input channel processing
3. **InputMatrix** - Matrix mixer (input to channel routing)
4. **PreOutputProcess** - Pre-output processing (EQ, XOver, etc.)
5. **OutputProcess** - Final output processing (limiters, gain, etc.)

All audio parameters are under: `/Device/Audio/Presets/Live/`

---

## 1. Source Selection & Routing

### Input Source Configuration
```
/Device/Audio/Presets/Live/SourceSelection/AnalogInput/Gain/Value
/Device/Audio/Presets/Live/SourceSelection/AnalogInput/Delay/Value
/Device/Audio/Presets/Live/SourceSelection/AES3Input/Gain/Value
/Device/Audio/Presets/Live/SourceSelection/AES3Input/Delay/Value
/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain0/Gain/Value
/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain0/Delay/Value
/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain1/Gain/Value
/Device/Audio/Presets/Live/SourceSelection/NetStreamGroupGain1/Delay/Value
```

### Routing Configuration
```
/Device/Audio/Presets/Live/SourceSelection/RoutingChannel-{0-3}/Src-{0-3}/Value
```
- Maps source inputs to routing channels

### Backup/Redundancy Strategy
For each BackupStrategy-{0-3}:
```
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/Enable/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/Manual/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/DefaultPriority/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/Priority-{0-3}/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/PilotTone/Enable/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/PilotTone/Freq/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/PilotTone/Low/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/PilotTone/High/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/PilotTone/GpioEnable/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/CustomThresholdSignalDetect/Enable/Value
/Device/Audio/Presets/Live/SourceSelection/BackupStrategy/BackupStrategy-{n}/CustomThresholdSignalDetect/Src-{0-3}/Value
```

---

## 2. Input Matrix (Mixer)

### Global Input Controls
```
/Device/Audio/Presets/Live/InputMatrix/InGain-{0-3,8-9}/Value    - Input source gains
/Device/Audio/Presets/Live/InputMatrix/InMute-{0-3,8-9}/Value    - Input source mutes
```

### Matrix Mixer (Per Channel)
For each Channel-{0-3}:
```
/Device/Audio/Presets/Live/InputMatrix/Channels/Channel-{n}/Gain-{0-3}/Value
/Device/Audio/Presets/Live/InputMatrix/Channels/Channel-{n}/Mute-{0-3}/Value
```
- Controls routing gain from each input to each output channel

### Extra Control
```
/Device/Audio/Presets/Live/InputMatrix/Generals/ExtraControl/Enable/Value
```

---

## 3. Input Process (Per Input Channel)

Base path: `/Device/Audio/Presets/Live/InputProcess/Channels/Channel-{0-3}/`

### Basic Controls
```
Enable/Value                - Enable/disable input channel
Gain/Value                  - Input gain
Mute/Value                  - Input mute
ShadingGain/Value           - Shading gain adjustment
InPolarity/Value            - Phase inversion
```

### Input Delay
```
InDelay/Enable/Value        - Enable input delay
InDelay/Value               - Delay time
```

### Input EQ
```
InputEQ/Enable/Value        - Enable input EQ
```

### Zone Block Processing
```
ZoneBlock/Enable/Value
ZoneBlock/Gain/Value
ZoneBlock/IIR/IIR-{0-6}/Enable
ZoneBlock/IIR/IIR-{0-6}/Fc/Value
ZoneBlock/IIR/IIR-{0-6}/Gain/Value
ZoneBlock/IIR/IIR-{0-6}/Q/Value
ZoneBlock/IIR/IIR-{0-6}/Slope/Value
ZoneBlock/IIR/IIR-{0-6}/Type/Value
```

---

## 4. Pre-Output Process (Per Channel)

Base path: `/Device/Audio/Presets/Live/PreOutputProcess/Channels/Channel-{0-3}/`

### Basic Controls
```
Gain/Value                  - Pre-output gain
Mute/Value                  - Pre-output mute
Polarity/Value              - Phase polarity
IsHighZActive/Value         - High-Z mode indicator
```

### Filter Names
```
FilterNameA                 - Filter preset name A
FilterNameB                 - Filter preset name B
FilterNameC                 - Filter preset name C
```

### Delay
```
Delay/Enable
Delay/Value                 - Delay time
```

### IIR Filters (8 bands)
For each IIR-{0-7}:
```
IIR/IIR-{n}/Enable
IIR/IIR-{n}/Fc/Value        - Center frequency
IIR/IIR-{n}/Gain/Value      - Gain
IIR/IIR-{n}/Q/Value         - Q factor
IIR/IIR-{n}/Slope/Value     - Filter slope
IIR/IIR-{n}/Type/Value      - Filter type
```

### FIR Filters
```
FIR/Enable
FIR/Taps                    - FIR tap data
FIR/nTaps                   - Number of taps
```

### Crossover (2 bands)
For each XOver-{0-1}:
```
XOver/XOver-{n}/Enable
XOver/XOver-{n}/Fc/Value    - Crossover frequency
XOver/XOver-{n}/Slope/Value - Crossover slope
XOver/XOver-{n}/Type/Value  - Crossover type
```

### Harmonic Generator
```
HarmonicGenerator/Enable/Value
HarmonicGenerator/Gain/Value
HarmonicGenerator/H2/Value
HarmonicGenerator/H3/Value
HarmonicGenerator/H4/Value
HarmonicGenerator/H5/Value
... (14 parameters total)
```

---

## 5. Output Process (Per Channel)

Base path: `/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{0-3}/`

### Basic Controls
```
Name                        - Channel name
Enable                      - Enable/disable channel
Gain/Value                  - Output gain (0.0-2.0)
Mute/Value                  - Mute (boolean)
OutPolarity/Value           - Output polarity/phase
Modified                    - Modified flag
```

### Output Delay
```
OutDelay/Enable
OutDelay/Value              - Delay time
```

### Bridge Mode
```
Bridge/Value                - Bridge mode enable
```

### Feedloop
```
Feedloop/Enable
Feedloop/Value              - Feedloop gain
```

---

### IIR Filters (16 bands)
For each IIR-{0-15}:
```
IIR/IIR-{n}/Enable
IIR/IIR-{n}/Fc/Value        - Center frequency
IIR/IIR-{n}/Gain/Value      - Gain adjustment
IIR/IIR-{n}/Q/Value         - Q factor
IIR/IIR-{n}/Slope/Value     - Filter slope
IIR/IIR-{n}/Type/Value      - Filter type (HP, LP, PEQ, etc.)
```

### FIR Filters
```
FIR/Enable
FIR/Taps                    - FIR coefficient data
FIR/nTaps                   - Number of taps
```

### Crossover (2 bands)
For each XOver-{0-1}:
```
XOver/XOver-{n}/Enable
XOver/XOver-{n}/Fc/Value
XOver/XOver-{n}/Slope/Value
XOver/XOver-{n}/Type/Value
```

---

### Dynamic EQ (3 bands)
For each DYNAMICEQ-{0-2}:
```
DynamicEq/DYNAMICEQ-{n}/Enable
DynamicEq/DYNAMICEQ-{n}/Position/Value          - Pre/Post position
DynamicEq/DYNAMICEQ-{n}/FilterType/Value        - Filter type
DynamicEq/DYNAMICEQ-{n}/LimiterType/Value       - Limiter type
DynamicEq/DYNAMICEQ-{n}/Fc/Value                - Center frequency
DynamicEq/DYNAMICEQ-{n}/Q/Value                 - Q factor
DynamicEq/DYNAMICEQ-{n}/MinGain/Value           - Minimum gain
DynamicEq/DYNAMICEQ-{n}/Ratio/Value             - Compression ratio
DynamicEq/DYNAMICEQ-{n}/AttackTime/Value
DynamicEq/DYNAMICEQ-{n}/ReleaseTime/Value
```

---

### Limiters & Protection

#### Clip Limiter
```
ClipLimiter/Enable
ClipLimiter/Threshold/Value
ClipLimiter/Gain/Value
ClipLimiter/AttackTime/Value
ClipLimiter/HoldTime/Value
ClipLimiter/ReleaseTime/Value
ClipLimiter/Flags/Value
```

#### Peak Limiter
```
PeakLimiter/Enable
PeakLimiter/Threshold/Value
PeakLimiter/Gain/Value
PeakLimiter/AttackTime/Value
PeakLimiter/HoldTime/Value
PeakLimiter/ReleaseTime/Value
```
Plus embedded IIR filters (IIR-{0-1})

#### Voltage Limiter RMS
```
VoltageLimiterRMS/Enable
VoltageLimiterRMS/Threshold/Value
VoltageLimiterRMS/Gain/Value
VoltageLimiterRMS/AttackTime/Value
VoltageLimiterRMS/HoldTime/Value
VoltageLimiterRMS/ReleaseTime/Value
```
Plus embedded IIR filters (IIR-{0-1})

#### Current Limiter RMS
```
CurrentLimiterRMS/Enable
CurrentLimiterRMS/Threshold/Value
CurrentLimiterRMS/Gain/Value
CurrentLimiterRMS/AttackTime/Value
CurrentLimiterRMS/HoldTime/Value
CurrentLimiterRMS/ReleaseTime/Value
```

#### Current Clamp
```
CurrentClamp/Enable
CurrentClamp/Threshold/Value
CurrentClamp/Gain/Value
CurrentClamp/AttackTime/Value
CurrentClamp/HoldTime/Value
CurrentClamp/ReleaseTime/Value
```

#### Thermal Limiter
```
ThermalLimiter/Enable
ThermalLimiter/Threshold/Value
ThermalLimiter/Gain/Value
ThermalLimiter/AttackTime/Value
ThermalLimiter/HoldTime/Value
ThermalLimiter/ReleaseTime/Value
```

#### True Power Limiter
```
TruePowerLimiter/Enable
TruePowerLimiter/Threshold/Value
TruePowerLimiter/Gain/Value
TruePowerLimiter/AttackTime/Value
TruePowerLimiter/HoldTime/Value
TruePowerLimiter/ReleaseTime/Value
```

---

### Monitoring & Protection

#### Pilot Tone Monitoring
```
PilotTone/Enable/Value
PilotTone/Freq/Value        - Monitoring frequency (typically 20kHz)
PilotTone/Low/Value         - Low threshold
PilotTone/High/Value        - High threshold
```

#### Pilot Tone Generator
```
PilotToneGenerator/Enable/Value
PilotToneGenerator/Freq/Value
PilotToneGenerator/Amplitude/Value
```

#### Load Monitoring
```
LoadMonitor/Enable/Value
LoadMonitor/Freq/Value      - Monitoring frequency
LoadMonitor/Low/Value       - Low impedance threshold
LoadMonitor/High/Value      - High impedance threshold
```

#### Nominal Impedance
```
NominalImpedance/Enable/Value
NominalImpedance/Low/Value  - Minimum impedance
NominalImpedance/High/Value - Maximum impedance
```

---

## 6. General Settings

Base path: `/Device/Audio/Presets/Live/Generals/`

### Signal Generator
```
SignalGenerator/Enable/Value
SignalGenerator/Gain/Value
```

### Power Management
```
Standby/Value
EnergySave/Freq/Value       - Energy save frequency threshold
EnergySave/Time/Value       - Time before energy save (seconds)
EnergySave/Max/Value        - Maximum energy save level
EnergySave/FilterEnable/Value
```

### GPI (General Purpose Inputs)
```
Gpi/Mode-{0-3}/Value        - GPIO mode configuration
```

### System Configuration
```
Config/HwArchitecture       - Hardware architecture ID
LatencyCompensation/Type
LatencyCompensation/Value
```

---

## Implementation Priorities for Home Assistant

### High Priority (User-Facing Controls)
1. **Output Channels** (Already implemented)
   - Gain/Value
   - Mute/Value
   - Name (for friendly naming)

2. **Input Channels**
   - Gain/Value
   - Mute/Value
   - InPolarity/Value

3. **Basic Output Processing**
   - OutDelay/Value
   - OutPolarity/Value
   - Enable (channel enable/disable)

### Medium Priority (Advanced Audio)
4. **IIR Parametric EQ** (Output)
   - 16-band parametric EQ per output channel
   - Enable, Fc, Gain, Q, Type per band

5. **Input Matrix**
   - Matrix mixer gains (input to channel routing)
   - Useful for custom routing scenarios

6. **Limiters** (Output Protection)
   - Enable/Threshold for key limiters
   - Read-only Gain reduction for monitoring

### Low Priority (Professional/Advanced)
7. **Crossovers**
   - XOver configuration (PreOutput + Output)

8. **Dynamic EQ**
   - Advanced dynamic processing

9. **FIR Filters**
   - Advanced speaker correction

10. **Monitoring**
    - Load impedance monitoring
    - Pilot tone status

11. **System Settings**
    - Standby mode
    - Energy save settings

---

## Example API Calls

### Read Multiple Parameters
```json
{
  "clientId": "home-assistant",
  "payload": {
    "type": "ACTION",
    "action": {
      "type": "READ",
      "values": [
        {"id": "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-0/Gain/Value", "single": true},
        {"id": "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-0/Mute/Value", "single": true}
      ]
    }
  }
}
```

### Write a Parameter
```json
{
  "clientId": "home-assistant",
  "payload": {
    "type": "ACTION",
    "action": {
      "type": "WRITE",
      "values": [{
        "id": "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-0/Gain/Value",
        "data": {
          "type": 20,
          "floatValue": 0.75
        },
        "single": true
      }]
    }
  }
}
```

### Browse a Path Tree
Use `"single": false` to get all sub-parameters:
```json
{
  "clientId": "home-assistant",
  "payload": {
    "type": "ACTION",
    "action": {
      "type": "READ",
      "values": [
        {"id": "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-0", "single": false}
      ]
    }
  }
}
```

---

## Notes

1. **Parameter Discovery**: Use `"single": false` to recursively retrieve all parameters under a path
2. **Data Types**: Always match the correct data type when writing (10=string, 20=float, 40=bool)
3. **Result Validation**: Check that `result` equals `10` (RESULT_SUCCESS) for each value
4. **Batch Operations**: Multiple parameters can be read/written in a single request
5. **Channel Indexing**: Channels are 0-indexed (Channel-0 through Channel-3)
6. **Live Preset**: All current parameters are under the "Live" preset path

---

## Signal Chain Summary

```
Input Sources (Analog/AES3/Network)
    ↓
SourceSelection (Routing + Backup)
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

Each stage provides comprehensive control over the audio signal path, from source selection through final output protection.
