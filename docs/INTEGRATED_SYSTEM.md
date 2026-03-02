# GrowUp IoT System - Integrated System Guide

## 🎯 Overview

This is a **unified, cohesive system** where `main.py` serves as the single entry point that coordinates ALL components:

- ✅ **Sensor Reading** - Read sensors every 1s, send to backend intelligently
- ✅ **Hardware Control** - Poll backend for control commands, apply to GPIO
- ✅ **Camera ML Detection** - YOLO object detection (optional)
- ✅ **LCD Viewer** - Real-time GUI display (optional)
- ✅ **Backend Communication** - Spring Boot REST API integration

---

## 🚀 Quick Start

### Standard Mode (No LCD)
```bash
python3 main.py
```

### With LCD Viewer
```bash
python3 main.py --lcd
```

### Demo Mode (No Hardware)
```bash
python3 main.py --lcd --demo
```

### Interactive Launcher
```bash
./start.sh
```

---

## 📁 System Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    main.py (ENTRY POINT)                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  GrowUpSystem Class                                   │ │
│  │  • Coordinates all components                         │ │
│  │  • Manages threads                                    │ │
│  │  • Shared data management                             │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │Sensor Loop  │  │Control Loop │  │  LCD Viewer      │ │
│  │(Thread 1)   │  │(Thread 2)   │  │  (Optional)      │ │
│  │             │  │             │  │                  │ │
│  │Every 1s:    │  │Every 5s:    │  │Tkinter GUI:      │ │
│  │• Read       │  │• Poll       │  │• Camera feed     │ │
│  │  sensors    │  │  backend    │  │• Sensor data     │ │
│  │• Check      │  │• Apply GPIO │  │• Controls        │ │
│  │  changes    │  │• Update LCD │  │• Logs            │ │
│  │• Send if:   │  │             │  │                  │ │
│  │  - 60s pass │  │             │  │                  │ │
│  │  - Big chg  │  │             │  │                  │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘ │
│         │                │                   │            │
│         └────────────────┴───────────────────┘            │
│                          ↓                                │
│              Shared Data Dictionary                       │
│              • sensors: {}                                │
│              • controls: {}                               │
│              • detections: []                             │
│              • logs: []                                   │
└────────────────────────────────────────────────────────────┘
                           ↓
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
┌────────────────────┐           ┌──────────────────────┐
│  hardware_control  │           │  Spring Boot Backend │
│  • GPIO pins       │           │  • PostgreSQL DB     │
│  • Relay control   │           │  • Analytics         │
└────────────────────┘           └──────────────────────┘
```

---

## 🔄 Data Flow

### 1. Sensor Reading → Backend

```
main.py (every 1s)
    ↓
Read sensors (server.py)
    ↓
Check: 60s passed OR significant change?
    ↓
YES → POST /api/sensor-readings
    {
      "waterTemp": 23.5,
      "phLevel": 7.0,
      ...
    }
    ↓
Backend saves to PostgreSQL
    ↓
Backend calculates analytics:
  • Water quality score
  • Health status
  • Alerts
    ↓
Returns enriched data
```

### 2. Frontend Control → Hardware

```
Frontend Settings Page
    ↓
User toggles "Pump" ON
    ↓
POST /api/controls
    {
      "pump": true,
      "fan": false,
      ...
    }
    ↓
Backend saves to control_states table
    ↓
main.py polls (every 5s)
    ↓
GET /api/controls/latest
    ↓
Receives new state
    ↓
hardware_control.py
    ↓
GPIO.output(17, HIGH) ← Relay CH1
    ↓
Pump turns ON! 🌊
    ↓
POST /api/controls/acknowledge
```

### 3. LCD Viewer Integration

```
main.py coordinates everything
    ↓
Shared data dictionary
    ↓
    ├→ Sensor loop updates sensors: {}
    ├→ Control loop updates controls: {}
    ├→ Camera updates detections: []
    └→ All components add to logs: []
    ↓
lcd_viewer.py (separate thread)
    ↓
Reads from shared data
    ↓
Updates Tkinter GUI (non-blocking)
```

---

## ⚙️ Configuration

### Backend URL (`config.py`)
```python
BACKEND_HOST = "http://192.168.1.100:8080"  # Your backend server
BACKEND_SENSOR_READINGS = f"{BACKEND_HOST}/api/sensor-readings"
BACKEND_CONTROLS = f"{BACKEND_HOST}/api/controls"
```

### GPIO Pins (`config.py`)
```python
GPIO_PINS = {
    "pump": 17,           # Relay CH1 → Submersible Pump
    "fan": 18,            # Relay CH2 → DC Fan
    "phAdjustment": 27,   # Relay CH3 → pH Dosing Pump
    "aerator": 22,        # Relay CH4 → Air Pump
    "growLight": 23,      # Relay CH5 → LED Grow Light
}
```

### Timing (`config.py`)
```python
SEND_INTERVAL = 60               # Send data every 60 seconds
CONTROL_POLL_INTERVAL = 5        # Poll for controls every 5 seconds

# Significant change thresholds (triggers immediate send)
SIGNIFICANT_CHANGE_THRESHOLDS = {
    "waterTemp": 0.5,      # ±0.5°C
    "ph": 0.2,             # ±0.2 pH
    "dissolvedO2": 0.5,    # ±0.5 mg/L
    ...
}
```

---

## 📊 Backend API Requirements

Your Spring Boot backend must implement these endpoints:

### 1. POST /api/sensor-readings
**Purpose:** Receive sensor data from Raspberry Pi

**Request Body:**
```json
{
  "waterTemp": 23.5,
  "phLevel": 7.0,
  "dissolvedO2": 8.2,
  "airTemp": 25.0,
  "lightIntensity": 450,
  "waterLevel": 85,
  "waterFlow": 12,
  "humidity": 65,
  "ammonia": 0.02,
  "airPressure": 1013.5,
  "plantHeight": 19.5,
  "plantLeaves": 14,
  "plantHealth": 95
}
```

**Response:**
```json
{
  "id": 12345,
  "timestamp": "2024-01-15T14:30:00",
  ...all sensor fields...,
  "waterQualityScore": 92.5,
  "healthStatus": "Excellent",
  "phAlert": false,
  "temperatureAlert": false
}
```

### 2. GET /api/sensor-readings/latest
**Purpose:** Frontend gets latest sensor data

**Response:** Same as POST response above

### 3. GET /api/sensor-readings/last-24h
**Purpose:** Frontend gets 24-hour history

**Response:** Array of sensor readings

### 4. POST /api/controls
**Purpose:** Frontend sends control updates

**Request Body:**
```json
{
  "pump": true,
  "fan": false,
  "phAdjustment": true,
  "aerator": true,
  "growLight": true
}
```

### 5. GET /api/controls/latest
**Purpose:** Raspberry Pi polls for control changes

**Response:**
```json
{
  "id": 123,
  "timestamp": "2024-01-15T14:30:00",
  "controls": {
    "pump": true,
    "fan": false,
    "phAdjustment": true,
    "aerator": true,
    "growLight": true
  }
}
```

### 6. POST /api/controls/acknowledge
**Purpose:** Raspberry Pi confirms control applied

**Request Body:**
```json
{
  "controls": { ... },
  "timestamp": "2024-01-15T14:30:00"
}
```

---

## 🧪 Testing

### Test Without Hardware (Demo Mode)
```bash
python3 main.py --lcd --demo
```
This will:
- ✅ Show LCD viewer with mock data
- ✅ Simulate sensor readings
- ✅ Allow testing UI without GPIO

### Test Sensor Reading
```bash
# In separate terminal, watch logs
python3 main.py

# You should see:
# 📊 Sensor loop started
# 📤 Sent to backend | Quality: 92.5 | Status: Excellent
```

### Test Hardware Control
```bash
# 1. Start system
python3 main.py

# 2. From frontend, toggle pump
# You should see:
# 🔄 Backend update: pump → ON
# 🔌 pump → ON (GPIO 17)
```

### Test LCD Viewer
```bash
python3 main.py --lcd --demo
```

---

## 🔧 Troubleshooting

### Backend Connection Failed
```
❌ Error sending sensor data: Connection refused
```
**Solution:** Check `BACKEND_HOST` in `config.py`, ensure backend is running

### GPIO Permission Denied
```
❌ Failed to initialize GPIO: Permission denied
```
**Solution:** Run with sudo or add user to gpio group:
```bash
sudo usermod -a -G gpio $USER
# Logout and login again
```

### LCD Viewer Won't Start
```
⚠️  LCD Viewer not available: No module named 'tkinter'
```
**Solution:** Install tkinter:
```bash
sudo apt-get install python3-tk
```

### Camera ML Not Working
```
⚠️  Camera ML not available: No module named 'cv2'
```
**Solution:** Install OpenCV:
```bash
pip install opencv-python
```

---

## 📈 Performance

- **CPU Usage:** ~10-15% (Raspberry Pi 4)
- **RAM Usage:** ~200-300 MB
- **Network:** ~5 KB per sensor send (every 60s = ~7.2 MB/day)
- **GPIO Response:** < 100ms (control command to relay activation)

---

## 🛡️ Security

### Production Checklist
- [ ] Change `BACKEND_HOST` to HTTPS URL
- [ ] Add API authentication tokens
- [ ] Configure firewall (block Flask port 5000 if used)
- [ ] Use environment variables for sensitive config
- [ ] Enable SSL for database connections

---

## 📝 Summary

| Component | Status | Thread | Update Frequency |
|-----------|--------|--------|------------------|
| **Sensor Reading** | ✅ | Thread 1 | Every 1s (send when needed) |
| **Control Polling** | ✅ | Thread 2 | Every 5s |
| **LCD Viewer** | Optional | Main thread | Real-time |
| **Camera ML** | Optional | Thread 3 | Real-time |
| **Backend Sync** | ✅ | Via threads | As needed |

**Result:** Single cohesive system, efficient communication, real-time control! 🎉

---

## 🔗 Related Documentation

- [`README.md`](../README.md) - Project overview
- [`config.py`](../config.py) - Configuration file
- [`hardware_control.py`](../hardware_control.py) - GPIO control
- [`docs/RPI_HARDWARE_GUIDE.md`](RPI_HARDWARE_GUIDE.md) - Hardware setup
- [`docs/LCD_VIEWER.md`](LCD_VIEWER.md) - LCD viewer guide
