# 🌱 GrowUp IoT System - Comprehensive Guide

A complete IoT system for plant growth monitoring and control on Raspberry Pi. Reads 8 environmental sensors, captures camera feeds with ML plant detection, and sends data to a Spring Boot backend. Supports both autonomous (AUTO) and manual (MANUAL) operating modes.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Features](#features)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [API Endpoints](#api-endpoints)
7. [Device Control](#device-control)
8. [System Modes](#system-modes)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)

---

## System Architecture

### Components

```
┌─────────────────────────────────────────┐
│     Raspberry Pi IoT Agent              │
├─────────────────────────────────────────┤
│                                         │
│  1. Sensor Agent (main.py)              │
│     ├─ Read 8 sensors every 1s         │
│     ├─ POST to /api/sensor-readings    │
│     ├─ Listen MQTT for control         │
│     └─ Process device commands         │
│                                         │
│  2. Camera Service (camera/ws_server.py)
│     ├─ Capture frames @ 5 FPS          │
│     ├─ YOLO inference                  │
│     ├─ Plant tracking + health scoring │
│     ├─ POST to /api/ml-results        │
│     ├─ WebSocket broadcast             │
│     └─ MQTT publish detections         │
│                                         │
│  3. Mode Manager (utils/mode_manager.py)
│     ├─ Global system mode (AUTO/MANUAL)
│     ├─ Mode switching                  │
│     └─ Callback notifications          │
│                                         │
│  4. Device Controller                  │
│     (utils/device_controller.py)       │
│     ├─ Hardware control callbacks      │
│     ├─ Action execution                │
│     └─ History tracking                │
│                                         │
│  5. Backend Client                     │
│     (utils/backend_client.py)          │
│     ├─ Sensor readings POST            │
│     ├─ Plant growth POST               │
│     ├─ ML results POST                 │
│     └─ Control acknowledgment          │
│                                         │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        │ HTTP POST           │ MQTT
        │                     │
   ┌────▼──────────┐   ┌──────▼────────┐
   │ Spring Boot   │   │ MQTT Broker   │
   │ Backend       │   │ (Mosquitto)   │
   │ :8080         │   │ :1883         │
   └───────────────┘   └───────────────┘
```

### Data Flows

| Component | Source | Destination | Frequency | Format |
|-----------|--------|-------------|-----------|--------|
| Sensor Agent | 8 sensors | /api/sensor-readings | 1/s | JSON |
| Camera Service | YOLO | /api/ml-results | Every frame | JSON |
| Device Control | MQTT | Hardware | On-demand | action:value |
| System Mode | MQTT | ModeManager | On-demand | AUTO/MANUAL |

---

## Features

### ✅ Sensor Monitoring (8 Sensors)
- **Water Temperature** (°C)
- **pH Level** (0-14)
- **Water Level** (%)
- **Flow Rate** (L/min)
- **Light Intensity** (lux)
- **Humidity** (%)
- **Air Pressure** (hPa)
- **Air Temperature** (°C)

### ✅ Camera & ML
- Real-time YOLO inference
- Persistent plant tracking across frames
- Health score computation (0-100)
- Bounding box detection
- Confidence scoring
- Anomaly detection (missing/new plants)

### ✅ Backend Integration
- **Sensor Readings**: `/api/sensor-readings` (1/s)
- **Plant Growth**: `/api/plant-growth` (event-driven)
- **ML Results**: `/api/ml-results` (per-frame)
- **Device Control**: MQTT `growup/device/{id}/control`
- **System Mode**: MQTT `growup/system/mode`

### ✅ Operating Modes
- **AUTO**: System operates autonomously (sensor-based rules)
- **MANUAL**: System responds to backend commands

### ✅ Control Actions
- Pump (on/off)
- Light (0-100 brightness)
- Heater (0-50°C)
- Fan (off/low/medium/high)
- Ventilation (on/off)

### ✅ Deployment Ready
- Raspberry Pi optimized
- Systemd service included
- Environment-based configuration
- Error handling & retries
- Verbose logging mode

---

## Installation

### Prerequisites

- Raspberry Pi (3B+ or later recommended)
- Raspberry Pi OS (Bullseye or newer)
- Python 3.8+
- Camera module (USB or Pi Camera)
- Network connection to backend

### Step 1: Clone Repository

```bash
cd /home/pi  # or your preferred directory
git clone <repository-url>
cd growup-python
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your settings
```

### Step 5: Verify Sensors & Camera

```bash
# Test sensor imports
python3 -c "from sensors.water_temp import WaterTempSensor; print('✅ Sensors OK')"

# Test camera
python3 -c "import cv2; print('✅ Camera OK')"

# Test MQTT
python3 -c "import paho.mqtt.client as mqtt; print('✅ MQTT OK')"
```

### Step 6: Start the Agent

```bash
python3 main.py
```

---

## Configuration

### Environment Variables

Create `.env` file from `.env.example`:

#### Backend Configuration
```bash
BACKEND_URL=http://localhost:8080
SENSOR_READINGS_ENDPOINT=http://localhost:8080/api/sensor-readings
PLANT_GROWTH_ENDPOINT=http://localhost:8080/api/plant-growth
ML_RESULTS_ENDPOINT=http://localhost:8080/api/ml-results
REQUEST_TIMEOUT=10
SEND_INTERVAL=1
DEVICE_ID=pi-001
```

#### Logging
```bash
VERBOSE_LOGGING=true  # Set to false for production
```

#### Camera Configuration
```bash
CAM_WS_HOST=0.0.0.0
CAM_WS_PORT=8765
CAM_INDEX=0           # 0 = default, 1 = second camera
CAM_MODEL_PATH=yolov8n.pt
CAM_SEND_FRAMES=false # Don't send base64 frames to save bandwidth
CAM_FRAME_SCALE=0.5   # Scale down for faster inference
CAM_CAPTURE_FPS=5
SEND_ML_RESULTS=true  # Send to backend
```

#### MQTT Configuration
```bash
MQTT_BROKER=localhost:1883
MQTT_DETECTIONS_TOPIC=camera/detections
```

---

## Usage

### Start the System

```bash
# Activate virtual environment
source venv/bin/activate

# Run with verbose logging
VERBOSE_LOGGING=true python3 main.py

# Or with custom backend
BACKEND_URL=http://192.168.1.100:8080 python3 main.py
```

### Expected Output

```
============================================================
🌱 GrowUp IoT Sensor Agent
============================================================
Backend URL:            http://localhost:8080
Sensor endpoint:        http://localhost:8080/api/sensor-readings
Plant growth endpoint:  http://localhost:8080/api/plant-growth
ML results endpoint:    http://localhost:8080/api/ml-results
Device ID:              pi-001
Send Interval:          1s
MQTT Broker:            localhost:1883
Verbose Logging:        True
============================================================

✅ Connected to MQTT
   └─ Subscribed to: growup/device/pi-001/control
   └─ Subscribed to: growup/system/mode
✅ Camera WebSocket + ML service started (daemon thread)

📊 Frame 1 | Sensor readings:
   waterTemp: 22.5
   phLevel: 7.2
   waterLevel: 85.0
   waterFlow: 10.5
   lightIntensity: 800
   humidity: 65.0
   airTemp: 24.0
   airPressure: 1013.5
✅ POST sensor-readings | Status: 200 OK
```

---

## API Endpoints

### 1. Sensor Readings

**Endpoint:** `POST /api/sensor-readings`

**Sent:** Every second

**Payload:**
```json
{
  "waterTemp": 22.5,
  "phLevel": 7.2,
  "waterLevel": 85.0,
  "waterFlow": 10.5,
  "lightIntensity": 800,
  "humidity": 65.0,
  "airTemp": 24.0,
  "airPressure": 1013.5
}
```

**Response (200 OK):**
```json
{
  "id": 123,
  "timestamp": "2026-03-15T10:30:00",
  "waterTemp": 22.5,
  ...
}
```

### 2. Plant Growth

**Endpoint:** `POST /api/plant-growth`

**Sent:** Event-driven (manual or automatic)

**Payload:**
```json
{
  "deviceId": "pi-001",
  "plantName": "Tomato Plant",
  "species": "Solanum lycopersicum",
  "growthStage": "flowering",
  "healthStatus": "healthy",
  "cameraDetections": {
    "total_plants": 1,
    "health_score": 92
  },
  "timestamp": "2026-03-15T10:30:00"
}
```

### 3. ML Results

**Endpoint:** `POST /api/ml-results`

**Sent:** Every frame (configurable FPS)

**Payload:**
```json
{
  "deviceId": "pi-001",
  "timestamp": "2026-03-15T10:30:00",
  "detections": [
    {
      "plant_id": 0,
      "bbox": [100, 150, 200, 300],
      "confidence": 0.95,
      "class_name": "plant",
      "age_seconds": 30,
      "tracking_frames": 15
    }
  ],
  "health_score": 92,
  "totalPlants": 1,
  "avgConfidence": 0.95
}
```

---

## Device Control

### Control Commands via MQTT

**Topic:** `growup/device/{DEVICE_ID}/control`

**Format:** `action:value`

### Supported Actions

| Action | Values | Example |
|--------|--------|---------|
| pump | on, off | `pump:on` |
| light | 0-100 | `light:75` |
| heater | 0-50 | `heater:25` |
| fan | off, low, medium, high | `fan:high` |
| vent | on, off | `vent:on` |

### Example Control Commands

```bash
# Turn pump on
mosquitto_pub -h localhost -t "growup/device/pi-001/control" -m "pump:on"

# Set light to 75% brightness
mosquitto_pub -h localhost -t "growup/device/pi-001/control" -m "light:75"

# Set heater to 25°C
mosquitto_pub -h localhost -t "growup/device/pi-001/control" -m "heater:25"

# Set fan to high
mosquitto_pub -h localhost -t "growup/device/pi-001/control" -m "fan:high"
```

### Control Flow

1. Backend sends control command
2. Pi receives via MQTT
3. **If MANUAL mode**: Execute action immediately
4. **If AUTO mode**: Ignore command (system-controlled)
5. Action tracked in history

---

## System Modes

### AUTO Mode

System operates autonomously based on sensor readings and predefined rules.

**Usage:**
```bash
# Set via MQTT
mosquitto_pub -h localhost -t "growup/system/mode" -m "AUTO"

# Or via backend
curl -X POST http://localhost:8080/api/system/mode/AUTO
```

**Behavior:**
- Ignores backend control commands
- Operates based on sensor thresholds
- Logs all decisions
- Can override for critical situations

### MANUAL Mode

System responds to backend commands via MQTT.

**Usage:**
```bash
# Set via MQTT
mosquitto_pub -h localhost -t "growup/system/mode" -m "MANUAL"

# Or via backend
curl -X POST http://localhost:8080/api/system/mode/MANUAL
```

**Behavior:**
- Accepts control commands from backend
- Executes actions immediately
- User responsible for decisions
- Good for testing or emergency control

### Mode Switching

The system starts in **AUTO** mode by default.

**Change via Backend:**
```bash
POST /api/system/mode/MANUAL
POST /api/system/mode/AUTO
```

**Change via MQTT:**
```bash
mosquitto_pub -t "growup/system/mode" -m "MANUAL"
mosquitto_pub -t "growup/system/mode" -m "AUTO"
```

**Programmatically:**
```python
from utils.mode_manager import ModeManager
manager = ModeManager("pi-001")
manager.set_mode("MANUAL")
```

---

## Systemd Service (Optional)

Run as system service on Raspberry Pi.

### 1. Copy Service File

```bash
sudo cp growup-sensor.service /etc/systemd/system/
```

### 2. Edit Paths (if needed)

```bash
sudo nano /etc/systemd/system/growup-sensor.service
# Update WorkingDirectory and ExecStart paths if different
```

### 3. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable growup-sensor
sudo systemctl start growup-sensor
```

### 4. Monitor

```bash
# View status
sudo systemctl status growup-sensor

# View logs
sudo journalctl -u growup-sensor -f

# Stop service
sudo systemctl stop growup-sensor
```

---

## Testing

### Test Backend Connectivity

```bash
# Check if backend is running
curl http://localhost:8080/api/sensor-readings

# Send test sensor reading
curl -X POST http://localhost:8080/api/sensor-readings \
  -H "Content-Type: application/json" \
  -d '{
    "waterTemp": 22.5,
    "phLevel": 7.2,
    "waterLevel": 85.0,
    "waterFlow": 10.5,
    "lightIntensity": 800,
    "humidity": 65.0,
    "airTemp": 24.0,
    "airPressure": 1013.5
  }'
```

### Test MQTT Connectivity

```bash
# Check if broker is running
mosquitto_sub -h localhost -t "test" -C 1

# Subscribe to control topic
mosquitto_sub -h localhost -t "growup/device/pi-001/control"

# Publish test command (in another terminal)
mosquitto_pub -h localhost -t "growup/device/pi-001/control" -m "pump:on"
```

### Test Camera WebSocket

```bash
# Connect to WebSocket (requires websocat)
websocat ws://localhost:8765

# Should receive detection data every frame
```

---

## Troubleshooting

### Backend Connection Failed

```
⚠️  Cannot connect to http://localhost:8080/api/sensor-readings
```

**Solutions:**
1. Verify backend is running: `curl http://localhost:8080/api/sensor-readings`
2. Check backend URL in `.env`
3. Verify firewall allows port 8080
4. Check network connectivity: `ping backend-ip`

### MQTT Connection Failed

```
⚠️  MQTT connect failed
```

**Solutions:**
1. Install MQTT broker: `sudo apt-get install mosquitto mosquitto-clients`
2. Start broker: `mosquitto`
3. Verify broker address in `.env`
4. Check if broker is running: `mosquitto_sub -h localhost -t test`

### Camera Not Found

```
❌ Unable to open camera index 0
```

**Solutions:**
1. List camera devices: `v4l2-ctl --list-devices`
2. Try different index: `export CAM_INDEX=1`
3. Check permissions: `ls -la /dev/video*`
4. Test camera: `fswebcam /tmp/test.jpg`

### High CPU Usage

**Solutions:**
1. Reduce frame rate: `export CAM_CAPTURE_FPS=3`
2. Increase frame scale: `export CAM_FRAME_SCALE=0.7`
3. Use smaller YOLO model: `export CAM_MODEL_PATH=yolov8n.pt`
4. Disable frame sending: `export CAM_SEND_FRAMES=false`

### Sensors Not Reading

**Solutions:**
1. Verify sensor hardware is connected
2. Check sensor driver files in `sensors/`
3. Test individual sensor: `python3 -c "from sensors.water_temp import WaterTempSensor; s = WaterTempSensor(); print(s.read())"`
4. Check GPIO pins are correct
5. Verify I2C/SPI is enabled: `sudo raspi-config`

### Control Commands Ignored

**Solutions:**
1. Check system mode: `VERBOSE_LOGGING=true python3 main.py`
2. If AUTO mode, switch to MANUAL: `mosquitto_pub -t "growup/system/mode" -m "MANUAL"`
3. Verify MQTT broker is running
4. Check if hardware callback is registered
5. View control queue: Check logs for "Control action" messages

---

## Module Reference

### utils/backend_client.py
Reusable HTTP client for all backend endpoints.

```python
from utils.backend_client import BackendClient

client = BackendClient("http://localhost:8080")
client.send_sensor_reading(22.5, 7.2, 85.0, 10.5, 800, 65.0, 24.0, 1013.5)
client.send_plant_growth("pi-001", "Tomato", "Solanum", "flowering", "healthy")
client.send_ml_results("pi-001", detections, 92, 1, 0.95)
```

### utils/device_controller.py
Hardware control action management.

```python
from utils.device_controller import DeviceController, MockHardware

controller = DeviceController("pi-001")
controller.register_action("pump", MockHardware.set_pump)
controller.parse_mqtt_command("pump:on")
```

### utils/mode_manager.py
Global system mode management.

```python
from utils.mode_manager import ModeManager

manager = ModeManager("pi-001")
manager.set_mode("MANUAL")
manager.register_mode_callback(on_mode_changed)
print(manager.get_status())
```

### camera/ws_server.py
Camera capture, ML inference, and WebSocket broadcasting.

- Real-time YOLO detection
- Plant tracking with persistent IDs
- Health score computation
- WebSocket and MQTT broadcasting

### camera/ml_classification.py
YOLO wrapper for inference.

```python
from camera.ml_classification import MLClassifier

classifier = MLClassifier("yolov8n.pt")
detections = classifier.classify_frame(frame)
```

---

## Best Practices

✅ **Configuration Management**
- All settings in `.env` (no hardcoding)
- Use different `.env` files for dev/prod
- Keep `.env` out of version control

✅ **Error Handling**
- Always catch exceptions in critical loops
- Log errors with context
- Gracefully degrade on failures
- Retry transient failures

✅ **Logging**
- Enable `VERBOSE_LOGGING=true` during development
- Disable in production to reduce overhead
- Check systemd journal: `journalctl -u growup-sensor -f`

✅ **Performance**
- Reduce `CAM_CAPTURE_FPS` on weak hardware
- Increase `CAM_FRAME_SCALE` for faster inference
- Use smaller YOLO models (nano, small)
- Set `CAM_SEND_FRAMES=false` to save bandwidth

✅ **Security**
- Don't commit `.env` files
- Use strong MQTT broker credentials (if exposed)
- Validate all MQTT messages
- Run with minimal permissions

✅ **Monitoring**
- Regularly check logs
- Monitor memory and CPU usage
- Test control commands
- Verify sensor readings

---

## Contributing

### Adding a New Sensor

1. Create `sensors/new_sensor.py`:
```python
class NewSensor:
    def __init__(self, pin=None):
        # Initialize hardware
        pass
    
    def read(self):
        # Return sensor reading as float
        return 0.0
```

2. Update `main.py`:
```python
from sensors.new_sensor import NewSensor
new_sensor = NewSensor()
# Add to read_all_sensors() dict
```

3. Update backend model to include new field

### Adding a New Control Action

1. Create hardware callback:
```python
def control_new_device(value):
    # Implement hardware control
    return True  # Return success/failure
```

2. Register in `main.py`:
```python
device_controller.register_action("new_device", control_new_device)
```

3. Use via MQTT:
```bash
mosquitto_pub -t "growup/device/pi-001/control" -m "new_device:on"
```

### Code Standards

- Use type hints: `def read(self) -> float:`
- Write docstrings: `"""Read and return sensor value."""`
- Handle exceptions gracefully
- Log important operations
- Test before committing

---

## License

MIT

---

## Support

For detailed information:
- **Backend Integration**: See `BACKEND_INTEGRATION.md`
- **Deployment Checklist**: See `DEPLOYMENT.md`
- **Quick Commands**: See `QUICK_REFERENCE.md`
- **API Examples**: See `BACKEND_UPDATE.md`

---

**Ready to deploy on Raspberry Pi! 🚀**