# 🔧 Raspberry Pi Hardware Control Guide

**This repository contains ONLY Raspberry Pi/hardware code**

The Spring Boot backend is in a **separate repository**.

---

## 📁 Repository Structure

```
rpi/
├── main.py                          # Main orchestrator
├── server.py                        # Flask API (optional/debugging)
├── config.py                        # System configuration
├── hardware_control.py              # GPIO control module
├── requirements.txt                 # Python dependencies
│
├── sensors/                         # Sensor modules
│   ├── temp_sensor.py
│   ├── ph_sensor.py
│   ├── humidity_sensor.py
│   ├── light_sensor.py
│   ├── water_flow_sensor.py
│   └── ammonia_sensor.py
│
├── camera/
│   ├── camera_ml.py                # ML processor
│   └── camera_ws.py                # WebSocket streamer (ngrok)
│
└── docs/                            # Documentation
```

---

## 🎯 Raspberry Pi Role

The Raspberry Pi acts as an **IoT device** that:

1. **Reads sensors** every second
2. **Sends data** to Spring Boot backend (every 60s or on significant change)
3. **Polls for control commands** from backend (every 5s)
4. **Controls hardware** via GPIO pins

---

## 🔌 Hardware Connections

### GPIO Pin Mapping (5-Channel Relay Module)

| GPIO Pin | Relay Channel | Device | Voltage | Purpose |
|----------|---------------|--------|---------|---------|
| GPIO 17 | CH1 | Submersible Pump | 220V AC | Water circulation |
| GPIO 18 | CH2 | DC Fan | 12V DC | Air circulation |
| GPIO 27 | CH3 | pH Dosing Pump | 12V DC | pH adjustment |
| GPIO 22 | CH4 | Air Pump/Aerator | 220V AC | Oxygen circulation |
| GPIO 23 | CH5 | LED Grow Light | 220V AC | Plant lighting |

### Wiring Diagram

```
Raspberry Pi          5V Relay Module        Devices
┌──────────┐         ┌──────────────┐       
│          │         │              │       
│  GPIO 17 ├────────►│ IN1  ├──┤NO ├──────► Pump (220V)
│  GPIO 18 ├────────►│ IN2  ├──┤NO ├──────► Fan (12V)
│  GPIO 27 ├────────►│ IN3  ├──┤NO ├──────► pH Pump (12V)
│  GPIO 22 ├────────►│ IN4  ├──┤NO ├──────► Aerator (220V)
│  GPIO 23 ├────────►│ IN5  ├──┤NO ├──────► Grow Light (220V)
│          │         │              │       
│  GND     ├────────►│ GND          │       
│          │         │              │       
└──────────┘         │  VCC (5V)    │←───── External 5V Power
                     └──────────────┘       
```

**⚠️ IMPORTANT**: 
- Use external 5V power supply for relay module (not Raspberry Pi 5V pin)
- 220V devices MUST be wired by qualified electrician
- Test with low voltage devices first (12V)

---

## 🔄 Data Flow

### Sending Sensor Data to Backend

```python
# Every 60 seconds OR on significant change:

Sensors → Read values → Check thresholds → Send to backend
                                             ↓
                                    POST /api/sensor-readings
                                             ↓
                                    Spring Boot saves to DB
```

**Significant Change Thresholds** (defined in `config.py`):
- Water temp: ±0.5°C
- pH: ±0.2
- Dissolved O2: ±0.5 mg/L
- Ammonia: ±0.05 ppm

### Receiving Control Commands from Backend

```python
# Every 5 seconds:

Raspberry Pi polls → GET /api/controls/latest
                     ↓
                Backend returns control states
                     ↓
                hardware_control.py applies to GPIO
                     ↓
                Hardware devices ON/OFF
```

---

## 📡 Backend API Endpoints (Reference)

**Note**: These endpoints are implemented in your **Spring Boot backend repository**.

### 1. POST /api/sensor-readings
**What**: Raspberry Pi sends sensor data here  
**When**: Every 60s or on significant change  
**Body**:
```json
{
  "waterTemp": 24.5,
  "phLevel": 6.8,
  "dissolvedO2": 7.8,
  "airTemp": 25.0,
  "humidity": 65,
  "lightIntensity": 450,
  "waterLevel": 85,
  "waterFlow": 12,
  "ammonia": 0.02,
  "airPressure": 1013.2
}
```

### 2. GET /api/controls/latest
**What**: Raspberry Pi polls for control commands  
**When**: Every 5 seconds  
**Response**:
```json
{
  "id": 123,
  "timestamp": "2026-03-01T10:30:45",
  "pump": true,
  "fan": false,
  "phAdjustment": true,
  "aerator": true,
  "growLight": true,
  "activePreset": "balanced"
}
```

### 3. POST /api/controls/acknowledge (Optional)
**What**: Raspberry Pi confirms control application  
**When**: After applying controls to GPIO  
**Body**:
```json
{
  "controlStateId": 123,
  "acknowledged": true,
  "appliedAt": "2026-03-01T10:30:50"
}
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure Backend URL

Edit `config.py`:
```python
BACKEND_URL = "http://your-backend-server:8080"
BACKEND_ENABLED = True
```

### 3. Test Hardware Control

```bash
# Test GPIO pins (without backend)
python3 hardware_control.py

# Test sensor reading
python3 -c "from sensors.temp_sensor import DS18B20; print(DS18B20(4).read_temp())"
```

### 4. Run Main Orchestrator

```bash
python3 main.py
```

Expected output:
```
🚀 GrowUp IoT System Starting...
✅ Hardware controller initialized
✅ Sensors initialized
📡 Sensor loop started (1s checks, 60s send)
🎮 Control loop started (5s polling)
📹 Camera ML loop started (5s)
🌱 System running!
```

---

## 🔧 Configuration (`config.py`)

### Backend Settings
```python
BACKEND_URL = "http://localhost:8080"
BACKEND_ENABLED = True
```

### GPIO Pin Mapping
```python
GPIO_PINS = {
    "pump": 17,
    "fan": 18,
    "phAdjustment": 27,
    "aerator": 22,
    "growLight": 23
}
```

### Timing Settings
```python
SENSOR_SEND_INTERVAL = 60  # Send data every 60 seconds
CONTROL_POLL_INTERVAL = 5   # Poll controls every 5 seconds
ML_PROCESS_INTERVAL = 5     # ML inference every 5 seconds
```

### Significant Change Thresholds
```python
SIGNIFICANT_CHANGE = {
    "waterTemp": 0.5,      # ±0.5°C
    "ph": 0.2,             # ±0.2
    "dissolvedO2": 0.5,    # ±0.5 mg/L
    "ammonia": 0.05        # ±0.05 ppm
}
```

---

## 📊 Hardware Control API (`hardware_control.py`)

### Initialize Controller

```python
from hardware_control import HardwareController

controller = HardwareController()
```

### Control Individual Devices

```python
# Turn pump ON
controller.set_relay("pump", True)

# Turn fan OFF
controller.set_relay("fan", False)
```

### Apply All Controls at Once

```python
controls = {
    "pump": True,
    "fan": False,
    "phAdjustment": True,
    "aerator": True,
    "growLight": True
}

controller.apply_controls(controls)
```

### Get Current States

```python
states = controller.get_states()
print(states)
# {'pump': True, 'fan': False, 'phAdjustment': True, ...}
```

### Emergency Stop

```python
controller.emergency_stop()  # Turn OFF all devices
```

---

## 🐛 Troubleshooting

### GPIO Permission Errors

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Reboot
sudo reboot
```

### Backend Connection Failed

```bash
# Test backend connectivity
curl http://localhost:8080/api/health

# Check config.py has correct BACKEND_URL
nano config.py
```

### Relay Not Switching

```bash
# Test GPIO manually
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.OUT); GPIO.output(17, GPIO.HIGH)"

# Check wiring connections
# Verify external 5V power to relay module
```

### Sensors Not Reading

```bash
# Check I2C devices
i2cdetect -y 1

# Check 1-Wire interface (DS18B20)
ls /sys/bus/w1/devices/
```

---

## 🔐 Security Notes

1. **Never expose Raspberry Pi directly to internet**
   - All communication goes through Spring Boot backend
   - Backend handles authentication/authorization

2. **Use HTTPS in production**
   ```python
   BACKEND_URL = "https://your-backend-server:8443"
   ```

3. **Secure GPIO access**
   - Only main.py should import hardware_control
   - No direct GPIO access from Flask server

4. **Electrical safety**
   - 220V devices wired by professionals only
   - Use GFCI/RCD protection on AC circuits
   - Test with low voltage first

---

## 📈 Performance Metrics

- **Sensor reading**: 1s interval (local)
- **Data sending**: 60s interval or on significant change
- **Control polling**: 5s interval
- **Network traffic**: ~1-2 requests/minute (efficient!)
- **GPIO response time**: < 100ms

---

## 📚 Related Documentation

- **Main README**: [`../README.md`](../README.md)
- **API Documentation**: [`API_DOCUMENTATION.md`](API_DOCUMENTATION.md)
- **Setup Guide**: [`SETUP_GUIDE.md`](SETUP_GUIDE.md)
- **Spring Boot Backend**: (separate repository)

---

**Built for GrowUp IoT Aquaponics System** 🌱
