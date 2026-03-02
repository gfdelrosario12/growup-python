"""
API Configuration for GrowUp IoT System
Centralized configuration for backend communication
"""

import os

# ========================================
# BACKEND API CONFIGURATION
# ========================================

# Spring Boot Backend URL
BACKEND_HOST = os.getenv("BACKEND_HOST", "localhost")
BACKEND_PORT = os.getenv("BACKEND_PORT", "8080")
BACKEND_BASE_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"

# API Endpoints
BACKEND_SENSOR_READINGS = f"{BACKEND_BASE_URL}/api/sensor-readings"
BACKEND_LATEST = f"{BACKEND_BASE_URL}/api/sensor-readings/latest"
BACKEND_LAST_24H = f"{BACKEND_BASE_URL}/api/sensor-readings/last-24h"

# ========================================
# DATA TRANSMISSION SETTINGS
# ========================================

# Send interval (seconds) - how often to send data to backend
SEND_INTERVAL = int(os.getenv("SEND_INTERVAL", "1"))  # Default: 1 second

# Request timeout (seconds)
REQUEST_TIMEOUT = 2

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# ========================================
# FLASK SERVER CONFIGURATION
# ========================================

FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# ========================================
# CAMERA WEBSOCKET CONFIGURATION
# ========================================

WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("WS_PORT", "8765"))

# ========================================
# LOGGING CONFIGURATION
# ========================================

# Enable verbose logging
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "True").lower() == "true"

# Log sensor readings to console
LOG_SENSOR_READINGS = os.getenv("LOG_SENSOR_READINGS", "False").lower() == "true"

# ========================================
# SENSOR CONFIGURATION
# ========================================

# Enable/disable individual sensors
SENSORS_ENABLED = {
    "water_temp": True,
    "ph": True,
    "dissolved_o2": False,  # Not yet implemented
    "air_temp": True,
    "light": True,
    "water_level": False,  # Not yet implemented
    "water_flow": True,
    "humidity": True,
    "ammonia": True,
    "air_pressure": True,
}

# Sensor default values (fallback if sensor fails)
SENSOR_DEFAULTS = {
    "waterTemp": 23.0,
    "ph": 7.0,
    "dissolvedO2": 7.8,
    "airTemp": 24.0,
    "lightIntensity": 500,
    "waterLevel": 85,
    "waterFlow": 12,
    "humidity": 65,
    "ammonia": 0.02,
    "airPressure": 1013.25,
}

# ========================================
# ML CONFIGURATION
# ========================================

# Enable ML inference
ML_ENABLED = os.getenv("ML_ENABLED", "True").lower() == "true"

# YOLO model path
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")

# ML inference interval (seconds) - run ML less frequently than sensors
ML_INFERENCE_INTERVAL = int(os.getenv("ML_INFERENCE_INTERVAL", "5"))

# ========================================
# WEEKLY LOGGING CONFIGURATION
# ========================================

# Enable weekly data logging to InfluxDB
WEEKLY_LOGGING_ENABLED = os.getenv("WEEKLY_LOGGING_ENABLED", "True").lower() == "true"

# ========================================
# HELPER FUNCTIONS
# ========================================

def get_backend_url():
    """Get the backend sensor readings endpoint URL"""
    return BACKEND_SENSOR_READINGS

def get_send_interval():
    """Get the data send interval in seconds"""
    return SEND_INTERVAL

def is_sensor_enabled(sensor_name):
    """Check if a specific sensor is enabled"""
    return SENSORS_ENABLED.get(sensor_name, False)

def get_sensor_default(sensor_key):
    """Get default value for a sensor"""
    return SENSOR_DEFAULTS.get(sensor_key, 0)

def print_config():
    """Print current configuration (useful for debugging)"""
    print("\n" + "="*60)
    print("🔧 GrowUp IoT System Configuration")
    print("="*60)
    print(f"Backend URL: {BACKEND_SENSOR_READINGS}")
    print(f"Send Interval: {SEND_INTERVAL} second(s)")
    print(f"Flask Server: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"WebSocket Server: ws://{WS_HOST}:{WS_PORT}")
    print(f"ML Enabled: {ML_ENABLED}")
    print(f"Verbose Logging: {VERBOSE_LOGGING}")
    print("="*60 + "\n")

# ========================================
# ENVIRONMENT SETUP INSTRUCTIONS
# ========================================

"""
To override configuration, set environment variables:

export BACKEND_HOST=192.168.1.100
export BACKEND_PORT=8080
export SEND_INTERVAL=2
export ML_ENABLED=False
export VERBOSE_LOGGING=True

Or create a .env file:

BACKEND_HOST=192.168.1.100
BACKEND_PORT=8080
SEND_INTERVAL=2
ML_ENABLED=False
VERBOSE_LOGGING=True

Then run with python-dotenv:
pip install python-dotenv
"""
