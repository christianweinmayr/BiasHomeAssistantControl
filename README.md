# Powersoft Bias Amplifier - Home Assistant Integration

Home Assistant custom integration for **Powersoft Bias series amplifiers** (Q1.5+, Q2, Q5, etc.) using the HTTP REST API.

## Overview

This integration allows you to control Powersoft Bias amplifiers through Home Assistant. Unlike the Mezzo series which use UDP PBus protocol, Bias amplifiers use an HTTP REST API for communication.

### Supported Models

- Void Acoustics Bias Q1.5+
- Powersoft Bias Q2
- Powersoft Bias Q5
- Other Bias series amplifiers with HTTP API

## Features

- **Volume Control**: Adjust gain for each output channel (Number entities)
- **Mute Control**: Mute/unmute each channel individually (Switch entities)
- **Auto-discovery**: Automatic device detection via config flow
- **Real-time Updates**: Configurable polling interval (5-300 seconds)

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the menu (⋮) and select "Custom repositories"
4. Add `https://github.com/christianweinmayr/BiasHomeAssistantControl` as a custom repository
5. Install "Powersoft Bias Amplifiers"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/powersoft_bias` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Powersoft Bias"
4. Enter your amplifier's IP address (and optionally port/scan interval)
5. The integration will auto-detect your amplifier and create entities

## Entities

For each Bias amplifier, the following entities are created:

### Number Entities (Volume/Gain)
- `number.bias_amplifier_channel_1_gain`
- `number.bias_amplifier_channel_2_gain`
- `number.bias_amplifier_channel_3_gain`
- `number.bias_amplifier_channel_4_gain`

### Switch Entities (Mute)
- `switch.bias_amplifier_channel_1_mute`
- `switch.bias_amplifier_channel_2_mute`
- `switch.bias_amplifier_channel_3_mute`
- `switch.bias_amplifier_channel_4_mute`

## Technical Details

### Protocol

The Bias series uses an HTTP REST API with JSON payload:

- **Endpoint**: `POST http://<ip>/am`
- **Format**: JSON with hierarchical parameter paths
- **Port**: 80 (HTTP)

Example request:
```json
{
  "clientId": "home-assistant",
  "payload": {
    "type": "ACTION",
    "action": {
      "type": "READ",
      "values": [
        {"id": "/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-0/Gain/Value", "single": true}
      ]
    }
  }
}
```

### API Paths

- **Channel Gain**: `/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{n}/Gain/Value`
- **Channel Mute**: `/Device/Audio/Presets/Live/OutputProcess/Channels/Channel-{n}/Mute/Value`
- **Device Serial**: `/Device/Config/Hardware/Model/Serial`
- **Device Model**: `/Device/Config/Hardware/Model/Name`

## Troubleshooting

### Amplifier not discovered

1. Verify the IP address is correct
2. Check that the amplifier is powered on and connected to the network
3. Ensure port 80 (HTTP) is accessible
4. Try accessing `http://<amplifier-ip>/info` in a browser - you should see device info

### Connection errors

- Check your network firewall isn't blocking HTTP traffic to port 80
- Verify the amplifier's web interface works by visiting its IP in a browser

## Related Projects

- [MezzoHomeAssistantControl](https://github.com/christianweinmayr/MezzoHomeAssistantControl) - Integration for Powersoft Mezzo amplifiers (UDP PBus protocol)

## License

MIT License - See LICENSE file for details

## Credits

Developed by Christian Weinmayr

## Support

For issues or feature requests, please open an issue on [GitHub](https://github.com/christianweinmayr/BiasHomeAssistantControl/issues).
