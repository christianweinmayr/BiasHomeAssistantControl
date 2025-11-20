# Preset System Implementation

This document describes the preset/scene management system for the Powersoft Bias integration.

## Overview

The preset system allows users to save and recall complete amplifier configurations. Presets capture:
- Output channel gains (0.0-2.0)
- Output channel mute states
- Output channel names
- Standby state (if available)

## Architecture

### Components

**1. Scene Manager (`scene_manager.py`)**
- Manages preset storage using Home Assistant's persistent storage
- Handles create, read, update, delete (CRUD) operations
- Validates preset configurations
- Stores presets in `.storage/powersoft_bias_presets_{entry_id}`

**2. HTTP Client Methods (`bias_http_client.py`)**
- `capture_current_state()` - Reads all current amplifier settings
- `apply_scene()` - Applies a complete preset configuration

**3. Services (`__init__.py`)**
- `powersoft_bias.save_preset` - Create new preset from current state
- `powersoft_bias.update_preset` - Update existing preset
- `powersoft_bias.delete_preset` - Delete a preset
- `powersoft_bias.rename_preset` - Rename a preset

**4. Button Entities (`button.py`)**
- **Apply Buttons** - One per preset, applies the preset when pressed
- **Update Buttons** - Update preset with current amplifier state
- **Delete Buttons** - Delete the preset
- **Create Button** - Always visible, creates new preset with timestamp name

## Data Structure

### Preset Format

```json
{
  "id": 1,
  "name": "Evening Listening",
  "output_channels": {
    "0": {
      "gain": 0.75,
      "mute": false,
      "name": "Main L"
    },
    "1": {
      "gain": 0.75,
      "mute": false,
      "name": "Main R"
    },
    "2": {
      "gain": 0.5,
      "mute": false,
      "name": "Sub"
    },
    "3": {
      "gain": 0.3,
      "mute": true,
      "name": "Fill"
    }
  },
  "standby": false,
  "created_at": "2025-01-20T12:00:00Z",
  "updated_at": "2025-01-20T14:30:00Z"
}

Note: Channel keys are strings ("0", "1", "2", "3") for JSON compatibility.
```

### Storage Location

Presets are stored in Home Assistant's `.storage` directory:
```
.storage/powersoft_bias_presets_{entry_id}
```

This file is automatically backed up with Home Assistant snapshots.

## Usage

### Creating a Preset

**Method 1: Using the Create Button**
1. Set your amplifier to the desired state
2. Press the "Preset - Create New" button
3. A preset is created with a timestamp name
4. Rename if desired using the service

**Method 2: Using a Service**
```yaml
service: powersoft_bias.save_preset
data:
  name: "My Custom Preset"
```

### Applying a Preset

**Method 1: Using Button Entities**
- Press the "Preset - {name}" button in Home Assistant UI

**Method 2: In Automations**
```yaml
automation:
  - alias: "Apply Evening Preset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: button.press
        target:
          entity_id: button.bias_amplifier_preset_evening_listening
```

### Updating a Preset

**Method 1: Using Update Button**
1. Adjust amplifier to new desired state
2. Press "Preset - Update '{name}'" button
3. Preset is updated with current state

**Method 2: Using Service**
```yaml
service: powersoft_bias.update_preset
data:
  scene_id: 1
```

### Deleting a Preset

**Method 1: Using Delete Button**
- Press "Preset - Delete '{name}'" button

**Method 2: Using Service**
```yaml
service: powersoft_bias.delete_preset
data:
  scene_id: 1
```

### Renaming a Preset

```yaml
service: powersoft_bias.rename_preset
data:
  scene_id: 1
  name: "New Name"
```

## Button Entity Naming

Buttons follow this naming convention:
- **Apply**: `button.{device}_preset_{scene_name}`
- **Update**: `button.{device}_preset_update_{scene_name}`
- **Delete**: `button.{device}_preset_delete_{scene_name}`
- **Create**: `button.{device}_preset_create_new`

Example:
```
button.bias_amplifier_preset_evening_listening
button.bias_amplifier_preset_update_evening_listening
button.bias_amplifier_preset_delete_evening_listening
button.bias_amplifier_preset_create_new
```

## Advanced Usage

### Scheduled Preset Changes

```yaml
automation:
  - alias: "Morning Preset"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.bias_amplifier_preset_morning

  - alias: "Evening Preset"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: button.press
        target:
          entity_id: button.bias_amplifier_preset_evening
```

### Conditional Preset Application

```yaml
automation:
  - alias: "Movie Mode When TV On"
    trigger:
      - platform: state
        entity_id: media_player.tv
        to: "on"
    action:
      - service: button.press
        target:
          entity_id: button.bias_amplifier_preset_movie_mode
```

### Scene Integration

Presets can be part of Home Assistant scenes:

```yaml
scene:
  - name: "Movie Night"
    entities:
      light.living_room: off
      media_player.tv:
        state: "on"
        source: "HDMI 1"
    # Then use automation to trigger preset button
```

## Technical Details

### API Batch Operations

The preset system uses batch HTTP requests for maximum efficiency:

**Capture (READ):**
- Single POST request reads all channel parameters
- ~13 parameters read in one call

**Apply (WRITE):**
- Single POST request writes all channel parameters
- ~8 parameters written in one call (gain + mute for 4 channels)

### Integration Reload

When presets are created, updated, or deleted, the integration automatically reloads to refresh button entities. This ensures the UI stays in sync with stored presets.

### Error Handling

- Failed writes are logged with specific parameter paths
- Standby write failures are non-fatal (may not be supported on all models)
- Invalid preset configurations are rejected with descriptive errors

## Limitations

### Current Version (v0.2.0)

**Included:**
- Output channel gains
- Output channel mutes
- Output channel names
- Standby state

**Not Yet Included:**
- Input channel controls
- Delay settings
- Limiter configurations
- EQ settings (16-band IIR filters)
- Crossover configurations
- Dynamic EQ settings

These features can be added in future versions as the API Discovery document shows they're available.

## Future Enhancements

### Planned Features

1. **Input Channel Support**
   - Input gains, mutes, polarity
   - Extend preset format

2. **Advanced DSP**
   - IIR parametric EQ (16 bands per channel)
   - Crossover settings (2-way per channel)
   - Limiter thresholds

3. **Import/Export**
   - Export presets as JSON files
   - Import presets from files
   - Share presets between installations

4. **Preset Comparison**
   - Compare current state vs preset
   - Show diff before applying
   - Validate preset compatibility

5. **Partial Presets**
   - Save only specific parameters
   - Apply only specific channels
   - Mix and match preset components

## Troubleshooting

### Preset Not Applying

1. Check Home Assistant logs for errors
2. Verify amplifier is online and responding
3. Test individual channel controls work
4. Try recreating the preset

### Buttons Not Appearing

1. Check `.storage/powersoft_bias_presets_{entry_id}` exists
2. Reload the integration
3. Check Home Assistant logs for loading errors
4. Verify integration version is 0.2.0 or higher

### Storage File Corruption

If the preset storage file becomes corrupted:
1. Backup `.storage/powersoft_bias_presets_{entry_id}`
2. Delete the file
3. Reload integration
4. Recreate presets

## Development Notes

### Adding New Parameters

To add new parameters to presets:

1. **Update `capture_current_state()` in `bias_http_client.py`:**
   - Add API paths to read list
   - Structure data in returned dict

2. **Update `apply_scene()` in `bias_http_client.py`:**
   - Add write values to batch request
   - Validate new parameters

3. **Update `validate_scene_config()` in `scene_manager.py`:**
   - Add validation for new parameters
   - Set sensible defaults

4. **Update preset format documentation:**
   - Document new fields
   - Provide examples

### Testing Presets

1. Create a preset with known values
2. Change amplifier state
3. Apply preset
4. Verify all parameters restored correctly
5. Check logs for any warnings or errors

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/christianweinmayr/BiasHomeAssistantControl/issues
- Check logs in Home Assistant for error details
- Include preset JSON and error messages when reporting issues
