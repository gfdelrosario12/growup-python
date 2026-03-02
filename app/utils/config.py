"""
GrowUp IoT System - Configuration (LEGACY)
==========================================
⚠️  DEPRECATED: This file is being replaced by src/config/settings.py
For new code, use: from src.config.settings import get_settings

This file is kept temporarily for backward compatibility.
"""

# ============================================
# BACKEND CONFIGURATION (Spring Boot Middleware)
# ============================================
BACKEND_HOST = "http://localhost:8080"
BACKEND_SENSOR_READINGS = f"{BACKEND_HOST}/api/sensor-readings"
BACKEND_CONTROLS = f"{BACKEND_HOST}/api/controls"
BACKEND_THRESHOLDS = f"{BACKEND_HOST}/api/thresholds"

# ============================================
# TIMING CONFIGURATION
# ============================================
SEND_INTERVAL = 60  # Send sensor data every 60 seconds
CONTROL_POLL_INTERVAL = 5  # Poll backend for control changes every 5 seconds

# Significant change thresholds (triggers immediate send)
SIGNIFICANT_CHANGE_THRESHOLDS = {
    "waterTemp": 0.5,      # ±0.5°C change triggers send
    "ph": 0.2,             # ±0.2 pH change triggers send
    "dissolvedO2": 0.5,    # ±0.5 mg/L change triggers send
    "ammonia": 0.05,       # ±0.05 ppm change triggers send
    "airTemp": 1.0,        # ±1.0°C change triggers send
    "waterFlow": 2.0,      # ±2.0 L/min change triggers send
    "humidity": 5.0,       # ±5% change triggers send
    "lightIntensity": 100, # ±100 lux change triggers send
}

# ============================================
# GPIO PIN CONFIGURATION (Relay Module)
# ============================================
GPIO_PINS = {
    "pump": 17,           # GPIO 17 → Relay CH1 → Submersible Pump (220V)
    "fan": 18,            # GPIO 18 → Relay CH2 → DC Fan (12V)
    "phAdjustment": 27,   # GPIO 27 → Relay CH3 → pH Dosing Pump (12V)
    "aerator": 22,        # GPIO 22 → Relay CH4 → Air Pump/Aerator (220V)
    "growLight": 23,      # GPIO 23 → Relay CH5 → LED Grow Light (220V)
}

RELAY_ACTIVE_HIGH = True

# ============================================
# REQUEST SETTINGS
# ============================================
REQUEST_TIMEOUT = 10  # seconds

# ============================================
# LOGGING CONFIGURATION
# ============================================
VERBOSE_LOGGING = True
LOG_SENSOR_READINGS = True
LOG_CONTROL_CHANGES = True
LOG_BACKEND_REQUESTS = True

# ============================================
# SYSTEM DEFAULTS
# ============================================
DEFAULT_CONTROLS = {
    "pump": True,
    "fan": False,
    "phAdjustment": True,
    "aerator": True,
    "growLight": True,
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def print_config():
    """Print current configuration"""
    print("=" * 50)
    print("GrowUp IoT System Configuration")
    print("=" * 50)
    print(f"Backend Host: {BACKEND_HOST}")
    print(f"Send Interval: {SEND_INTERVAL}s")
    print(f"Control Poll: {CONTROL_POLL_INTERVAL}s")
    print(f"GPIO Pins: {GPIO_PINS}")
    print("=" * 50)

def get_gpio_pin(control_name: str) -> int:
    """Get GPIO pin number for a control"""
    return GPIO_PINS.get(control_name, -1)

def is_significant_change(sensor_key: str, old_value: float, new_value: float) -> bool:
    """Check if sensor change is significant enough to trigger immediate send"""
    threshold = SIGNIFICANT_CHANGE_THRESHOLDS.get(sensor_key, 0)
    return abs(new_value - old_value) >= threshold

"""
GrowUp IoT System - Configuration
==================================
All system-wide configuration settings
"""

# ============================================
# BACKEND CONFIGURATION (Spring Boot Middleware)
# ============================================
# Frontend connects ONLY to Spring Boot backend
# Raspberry Pi sends data TO Spring Boot
# Spring Boot acts as single source of truth

BACKEND_HOST = "http://localhost:8080"
BACKEND_SENSOR_READINGS = f"{BACKEND_HOST}/api/sensor-readings"
BACKEND_CONTROLS = f"{BACKEND_HOST}/api/controls"
BACKEND_THRESHOLDS = f"{BACKEND_HOST}/api/thresholds"

# ============================================
# FLASK SERVER (Internal Only - Not Exposed)
# ============================================
# Flask runs locally for hardware control only
# NOT accessible from frontend directly

FLASK_HOST = "127.0.0.1"  # Localhost only
FLASK_PORT = 5000
FLASK_DEBUG = False  # Set True for development

# ============================================
# TIMING CONFIGURATION
# ============================================

# Send sensor data to backend every 60 seconds
SEND_INTERVAL = 60  # 1 minute

# Poll backend for control changes every 5 seconds
CONTROL_POLL_INTERVAL = 5

# Significant change thresholds (triggers immediate send)
SIGNIFICANT_CHANGE_THRESHOLDS = {
    "waterTemp": 0.5,      # ±0.5°C change triggers send
    "ph": 0.2,             # ±0.2 pH change triggers send
    "dissolvedO2": 0.5,    # ±0.5 mg/L change triggers send
    "ammonia": 0.05,       # ±0.05 ppm change triggers send
    "airTemp": 1.0,        # ±1.0°C change triggers send
    "waterFlow": 2.0,      # ±2.0 L/min change triggers send
    "humidity": 5.0,       # ±5% change triggers send
    "lightIntensity": 100, # ±100 lux change triggers send
}

# ============================================
# GPIO PIN CONFIGURATION (Relay Module)
# ============================================
# 5V Relay Module connected to Raspberry Pi GPIO

GPIO_PINS = {
    "pump": 17,           # GPIO 17 → Relay CH1 → Submersible Pump (220V)
    "fan": 18,            # GPIO 18 → Relay CH2 → DC Fan (12V)
    "phAdjustment": 27,   # GPIO 27 → Relay CH3 → pH Dosing Pump (12V)
    "aerator": 22,        # GPIO 22 → Relay CH4 → Air Pump/Aerator (220V)
    "growLight": 23,      # GPIO 23 → Relay CH5 → LED Grow Light (220V)
}

# Relay logic (some relays are active LOW, some active HIGH)
# Set to True if relay activates on GPIO HIGH
# Set to False if relay activates on GPIO LOW (common for optocoupler relays)
RELAY_ACTIVE_HIGH = True

# ============================================
# SENSOR CONFIGURATION
# ============================================

# I2C Sensor Addresses
I2C_ADDRESSES = {
    "BME280": 0x76,      # Air temp, humidity, pressure
    "BH1750": 0x23,      # Light intensity
}

# 1-Wire Sensor IDs (replace with your actual sensor IDs)
ONEWIRE_SENSORS = {
    "DS18B20_WATER": "28-000000000000",  # Water temperature sensor
}

# Analog Sensor Channels (if using ADC like MCP3008)
ADC_CHANNELS = {
    "pH": 0,             # Channel 0
    "dissolvedO2": 1,    # Channel 1
    "ammonia": 2,        # Channel 2
}

# Flow sensor GPIO pin (interrupt-based)
FLOW_SENSOR_PIN = 24

# Ultrasonic sensor pins (HC-SR04 for water level)
ULTRASONIC_TRIGGER = 25
ULTRASONIC_ECHO = 8

# ============================================
# REQUEST SETTINGS
# ============================================
REQUEST_TIMEOUT = 10  # seconds

# ============================================
# LOGGING CONFIGURATION
# ============================================
VERBOSE_LOGGING = True
LOG_SENSOR_READINGS = True
LOG_CONTROL_CHANGES = True
LOG_BACKEND_REQUESTS = True

LOG_FILE = "/var/log/growup/system.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# ============================================
# CAMERA CONFIGURATION (ngrok WebSocket)
# ============================================
CAMERA_WEBSOCKET_PORT = 8765
CAMERA_RESOLUTION = (640, 480)
CAMERA_FPS = 15

# ============================================
# SYSTEM DEFAULTS
# ============================================

# Default control states (on system startup)
DEFAULT_CONTROLS = {
    "pump": True,
    "fan": False,
    "phAdjustment": True,
    "aerator": True,
    "growLight": True,
}

# ============================================
# HELPER FUNCTIONS
# ============================================

def print_config():
    """Print current configuration"""
    print("=" * 50)
    print("GrowUp IoT System Configuration")
    print("=" * 50)
    print(f"Backend Host: {BACKEND_HOST}")
    print(f"Send Interval: {SEND_INTERVAL}s")
    print(f"Control Poll: {CONTROL_POLL_INTERVAL}s")
    print(f"Flask Port: {FLASK_PORT} (internal only)")
    print(f"GPIO Pins: {GPIO_PINS}")
    print("=" * 50)

def get_gpio_pin(control_name: str) -> int:
    """Get GPIO pin number for a control"""
    return GPIO_PINS.get(control_name, -1)

def is_significant_change(sensor_key: str, old_value: float, new_value: float) -> bool:
    """Check if sensor change is significant enough to trigger immediate send"""
    threshold = SIGNIFICANT_CHANGE_THRESHOLDS.get(sensor_key, 0)
    return abs(new_value - old_value) >= threshold
