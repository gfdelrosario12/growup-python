# MQTT Device Control

## Overview

The GrowUp IoT system now supports MQTT-based device control in addition to HTTP polling. This allows real-time control of devices via MQTT messages.

## Topics

The system subscribes to the following MQTT topics:

```
growup/device/{deviceId}/pump
growup/device/{deviceId}/fan
growup/device/{deviceId}/aerator
growup/device/{deviceId}/growlight
```

Where `{deviceId}` is your unique device identifier (default: `rpi-001`).

## Message Format

**Payload:** String containing either `"true"` or `"false"`

- `"true"` → Turn device **ON**
- `"false"` → Turn device **OFF**

## Configuration

Set these environment variables in your `.env` file:

```bash
# MQTT Broker Connection
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=  # Optional
MQTT_PASSWORD=  # Optional

# Device Identity
DEVICE_ID=rpi-001
```

## Device Mapping

| MQTT Topic Suffix | Control Name | GPIO Pin | Description |
|------------------|--------------|----------|-------------|
| `pump` | pump | GPIO 17 | Submersible Water Pump |
| `fan` | fan | GPIO 18 | Cooling Fan |
| `aerator` | aerator | GPIO 22 | Air Pump |
| `growlight` | growLight | GPIO 23 | LED Grow Light |

**Note:** MQTT topics use lowercase names, but internally map to camelCase config names.

## Usage Examples

### Using mosquitto_pub

```bash
# Turn pump ON
mosquitto_pub -h localhost -t "growup/device/rpi-001/pump" -m "true"

# Turn pump OFF
mosquitto_pub -h localhost -t "growup/device/rpi-001/pump" -m "false"

# Turn fan ON
mosquitto_pub -h localhost -t "growup/device/rpi-001/fan" -m "true"

# Turn all lights OFF
mosquitto_pub -h localhost -t "growup/device/rpi-001/growlight" -m "false"
```

### Using Python paho-mqtt

```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("localhost", 1883, 60)

# Turn aerator ON
client.publish("growup/device/rpi-001/aerator", "true")

# Turn fan OFF
client.publish("growup/device/rpi-001/fan", "false")

client.disconnect()
```

### Using Node.js mqtt

```javascript
const mqtt = require('mqtt');
const client = mqtt.connect('mqtt://localhost:1883');

client.on('connect', () => {
  // Turn pump ON
  client.publish('growup/device/rpi-001/pump', 'true');
  
  // Turn fan OFF
  client.publish('growup/device/rpi-001/fan', 'false');
  
  client.end();
});
```

## Installation

The MQTT client is automatically installed with the base requirements:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install paho-mqtt==1.6.1
```

## Testing

### 1. Start the System

```bash
python main.py
```

You should see:
```
✅ MQTT connected to localhost:1883
📡 Subscribed to: growup/device/rpi-001/pump
📡 Subscribed to: growup/device/rpi-001/fan
📡 Subscribed to: growup/device/rpi-001/aerator
📡 Subscribed to: growup/device/rpi-001/growlight
```

### 2. Send Test Messages

In another terminal:

```bash
# Test pump control
mosquitto_pub -t "growup/device/rpi-001/pump" -m "true"
mosquitto_pub -t "growup/device/rpi-001/pump" -m "false"
```

You should see in the main terminal:
```
🔌 MQTT: pump → ON
🔌 MQTT: pump → OFF
```

## Architecture

```
MQTT Broker (localhost:1883)
    ↓ (publish control messages)
mqtt_control.py (MQTTControlHandler)
    ↓ (parse and validate)
hardware_control.py (HardwareController)
    ↓ (GPIO output)
Physical Relay Module
    ↓ (switch)
Device (Pump, Fan, etc.)
```

## Features

✅ **Real-time Control** - Instant device response via MQTT  
✅ **Non-blocking** - MQTT runs in background thread  
✅ **Graceful Degradation** - System works without MQTT broker  
✅ **Dual Control** - HTTP polling and MQTT control coexist  
✅ **Clean Integration** - No modification to existing HTTP logic  
✅ **Error Handling** - Invalid messages logged, system continues  

## Behavior

- MQTT control handler runs **independently** of HTTP polling
- Both control methods can coexist
- Last command received (HTTP or MQTT) takes precedence
- GPIO state changes are logged for both control methods
- System continues running even if MQTT broker is unavailable

## Troubleshooting

### MQTT Connection Failed

```
❌ MQTT connection failed with code 1
```

**Solution:** Check broker is running:
```bash
# Install Mosquitto
sudo apt-get install mosquitto mosquitto-clients

# Start broker
sudo systemctl start mosquitto
```

### Invalid Payload Warning

```
⚠️  Invalid payload for pump: on (expected 'true' or 'false')
```

**Solution:** Use exactly `"true"` or `"false"` (lowercase strings):
```bash
# Correct
mosquitto_pub -t "growup/device/rpi-001/pump" -m "true"

# Wrong
mosquitto_pub -t "growup/device/rpi-001/pump" -m "on"
mosquitto_pub -t "growup/device/rpi-001/pump" -m "1"
```

### Unknown Device

```
⚠️  Unknown device: light
```

**Solution:** Use correct device names (see table above):
```bash
# Correct
mosquitto_pub -t "growup/device/rpi-001/growlight" -m "true"

# Wrong
mosquitto_pub -t "growup/device/rpi-001/light" -m "true"
```

## Security Considerations

For production deployments:

1. **Use Authentication:**
   ```bash
   MQTT_USERNAME=growup_device
   MQTT_PASSWORD=secure_password
   ```

2. **Use TLS/SSL:**
   ```bash
   MQTT_PORT=8883  # Secure MQTT port
   ```

3. **Firewall MQTT Port:**
   ```bash
   sudo ufw allow from trusted_ip to any port 1883
   ```

4. **Unique Device IDs:**
   ```bash
   DEVICE_ID=greenhouse-rpi-north-001
   ```

## Limitations

- Only supports ON/OFF control (no analog/PWM)
- No feedback/acknowledgment published back to MQTT
- Assumes reliable MQTT broker connection
- No message queuing during disconnect

## Future Enhancements

Possible improvements (not implemented):

- Publish device state changes back to MQTT
- Support for PWM/analog control values
- QoS levels for reliable delivery
- Retained messages for last known state
- MQTT-based sensor telemetry

---

**Note:** This feature adds MQTT control **alongside** existing HTTP polling. Both control methods work independently and simultaneously.
