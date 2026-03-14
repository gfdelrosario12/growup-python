"""
GrowUp IoT System - Sensor Agent
=================================
Reads 8 environmental sensors every second and sends aggregated readings
to the local Spring Boot backend at http://localhost:8080/api/sensor-readings

Also sends:
- Plant growth data to /api/plant-growth
- ML detection results to /api/ml-results
- Receives device controls via MQTT

Sensors:
- Water Temperature (waterTemp)
- pH Level (phLevel)
- Water Level (waterLevel)
- Flow Rate (waterFlow)
- Light Intensity (lightIntensity)
- Humidity (humidity)
- Air Pressure (airPressure)
- Air Temperature (airTemp)

The agent sends data to Spring Boot SensorReadingController via POST /api/sensor-readings.
Camera WebSocket + ML service runs in a background thread.
Receives device control commands via MQTT.

Ready for Raspberry Pi deployment.
"""

import os
import threading
import time
import json
import requests
import queue

from sensors.water_temp import WaterTempSensor
from sensors.ph import PHSensor
from sensors.water_level import WaterLevelSensor
from sensors.flow_rate import FlowRateSensor
from sensors.light import LightSensor
from sensors.humidity import HumiditySensor
from sensors.air_sensor import AirSensor
from utils.mode_manager import ModeManager
from utils.device_controller import DeviceController
from utils.backend_client import BackendClient

# ============================================================
# CONFIGURATION (via environment variables)
# ============================================================
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")
SENSOR_READINGS_ENDPOINT = os.getenv(
    "SENSOR_READINGS_ENDPOINT",
    f"{BACKEND_URL}/api/sensor-readings"
)
PLANT_GROWTH_ENDPOINT = os.getenv(
    "PLANT_GROWTH_ENDPOINT",
    f"{BACKEND_URL}/api/plant-growth"   
)
ML_RESULTS_ENDPOINT = os.getenv(
    "ML_RESULTS_ENDPOINT",
    f"{BACKEND_URL}/api/ml-results"
)
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
SEND_INTERVAL = int(os.getenv("SEND_INTERVAL", "1"))  # Send every second
DEVICE_ID = os.getenv("DEVICE_ID", "pi-001")
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "true").lower() in ("1", "true", "yes")
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost:1883")

# ============================================================
# SENSOR INITIALIZATION
# ============================================================
water_temp = WaterTempSensor()
ph_sensor = PHSensor()
water_level = WaterLevelSensor()
flow_rate = FlowRateSensor()
light = LightSensor()
humidity = HumiditySensor()
air = AirSensor()

# Control command queue (from MQTT)
control_queue = queue.Queue()

# Initialize mode manager
mode_manager = ModeManager(DEVICE_ID, verbose=VERBOSE_LOGGING)

# Backend client for API calls
backend_client = BackendClient(BACKEND_URL, REQUEST_TIMEOUT, VERBOSE_LOGGING)

# Device controller for hardware control
device_controller = DeviceController(DEVICE_ID, verbose=VERBOSE_LOGGING)


def read_all_sensors():
    """
    Read all 8 sensors and return a dict matching the Spring Boot SensorReading model.
    
    Fields expected by POST /api/sensor-readings:
    - waterTemp: float (°C)
    - phLevel: float (0-14)
    - waterLevel: float (%)
    - waterFlow: float (L/min)
    - lightIntensity: float (lux)
    - humidity: float (%)
    - airTemp: float (°C)
    - airPressure: float (hPa)
    """
    try:
        # Read air sensor (returns dict with temperature and pressure)
        air_data = air.read()
        if not isinstance(air_data, dict):
            air_data = {"temperature": 0, "pressure": 0}
        
        return {
            "waterTemp": water_temp.read(),
            "phLevel": ph_sensor.read(),
            "waterLevel": water_level.read(),
            "waterFlow": flow_rate.read(),
            "lightIntensity": light.read(),
            "humidity": humidity.read(),
            "airTemp": air_data.get("temperature", 0),
            "airPressure": air_data.get("pressure", 0)
        }
    except Exception as e:
        print(f"❌ Error reading sensors: {e}")
        return None


def send_to_backend(endpoint, payload):
    """
    Generic function to send data to backend endpoints.
    
    Args:
        endpoint: Full URL to backend endpoint
        payload: dict to POST as JSON
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not payload:
        return False
    
    try:
        response = requests.post(
            endpoint,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            if VERBOSE_LOGGING:
                try:
                    result = response.json()
                    print(f"✅ POST {endpoint.split('/')[-1]} | ID: {result.get('id', 'N/A')} | Status: 200 OK")
                except Exception:
                    print(f"✅ POST {endpoint.split('/')[-1]} | Status: 200 OK")
            return True
        else:
            print(f"⚠️  {endpoint} returned {response.status_code}: {response.text[:100]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⚠️  Request timeout ({REQUEST_TIMEOUT}s) to {endpoint}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"⚠️  Cannot connect to {endpoint}")
        return False
    except Exception as e:
        print(f"❌ Error posting to {endpoint}: {e}")
        return False


def send_sensor_readings(sensor_data):
    """Send sensor readings to /api/sensor-readings"""
    return send_to_backend(SENSOR_READINGS_ENDPOINT, sensor_data)


def send_plant_growth(plant_data):
    """
    Send plant growth data to /api/plant-growth
    
    Expected payload:
    {
      "deviceId": "pi-001",
      "plantName": "Tomato Plant",
      "species": "Solanum lycopersicum",
      "growthStage": "flowering",
      "healthStatus": "healthy",
      "cameraDetections": {...},
      "timestamp": "2026-03-15T10:30:00"
    }
    """
    return send_to_backend(PLANT_GROWTH_ENDPOINT, plant_data)


def send_ml_results(ml_data):
    """
    Send ML detection results to /api/ml-results
    
    Expected payload:
    {
      "deviceId": "pi-001",
      "timestamp": "2026-03-15T10:30:00",
      "detections": [
        {
          "plant_id": 0,
          "bbox": [100, 150, 200, 300],
          "confidence": 0.95,
          "class_name": "plant",
          "age_seconds": 30
        }
      ],
      "health_score": 92,
      "totalPlants": 1,
      "avgConfidence": 0.95
    }
    """
    return send_to_backend(ML_RESULTS_ENDPOINT, ml_data)


def setup_mqtt_control_listener():
    """
    Setup MQTT listener for device control commands.
    Listens on: growup/device/{DEVICE_ID}/control
    """
    try:
        import paho.mqtt.client as mqtt
        
        client = mqtt.Client()
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                # Subscribe to device control topic
                control_topic = f"growup/device/{DEVICE_ID}/control"
                client.subscribe(control_topic)
                
                # Subscribe to system mode topic
                mode_topic = "growup/system/mode"
                client.subscribe(mode_topic)
                
                print(f"✅ Connected to MQTT")
                print(f"   └─ Subscribed to: {control_topic}")
                print(f"   └─ Subscribed to: {mode_topic}")
            else:
                print(f"⚠️  MQTT connection failed with code {rc}")
        
        def on_message(client, userdata, msg):
            try:
                payload = msg.payload.decode('utf-8')
                if VERBOSE_LOGGING:
                    print(f"📩 MQTT: {msg.topic} = {payload}")
                
                # Handle system mode changes
                if msg.topic == "growup/system/mode":
                    mode_manager.set_mode(payload)
                    return
                
                # Handle device control commands
                if f"growup/device/{DEVICE_ID}/control" in msg.topic:
                    control_queue.put({"topic": msg.topic, "payload": payload})
            except Exception as e:
                print(f"❌ Error processing MQTT message: {e}")
        
        client.on_connect = on_connect
        client.on_message = on_message
        
        # Parse MQTT_BROKER (format: host:port)
        if ":" in MQTT_BROKER:
            host, port = MQTT_BROKER.split(":")
            port = int(port)
        else:
            host = MQTT_BROKER
            port = 1883
        
        client.connect(host, port, keepalive=60)
        client.loop_start()
        
        return client
    except ImportError:
        print("⚠️  MQTT support not available (install paho-mqtt)")
        return None
    except Exception as e:
        print(f"⚠️  Failed to setup MQTT control listener: {e}")
        return None


def process_control_commands():
    """Process control commands from the queue"""
    while not control_queue.empty():
        try:
            command = control_queue.get_nowait()
            topic = command.get("topic", "")
            payload = command.get("payload", "")
            
            # Check if we're in MANUAL mode before executing
            if not mode_manager.is_manual_mode():
                if VERBOSE_LOGGING:
                    print(f"⊘ Ignoring control command (AUTO mode active): {payload}")
                continue
            
            # Parse control command (format: action:value)
            if ":" in payload:
                action, value = payload.split(":", 1)
                if VERBOSE_LOGGING:
                    print(f"🎮 Control action: {action} = {value}")
                
                # Execute action via device controller
                device_controller.execute_action(action.lower(), value.lower())
            
        except queue.Empty:
            break
        except Exception as e:
            print(f"❌ Error processing control command: {e}")


def start_camera_service():
    """
    Start camera WebSocket + ML service in a background daemon thread.
    This service captures camera frames, runs YOLO inference, tracks plants,
    and broadcasts detections via WebSocket and MQTT.
    It also sends ML results to /api/ml-results.
    """
    try:
        from camera.ws_server import start_server as start_camera_ws_server
        _HAS_CAMERA = True
    except ImportError:
        _HAS_CAMERA = False
        print("⚠️  Camera module not available (skipping)")
        return
    
    if not _HAS_CAMERA:
        return
    
    try:
        camera_thread = threading.Thread(
            target=start_camera_ws_server,
            daemon=True,
            name="CameraService"
        )
        camera_thread.start()
        print("✅ Camera WebSocket + ML service started (daemon thread)")
    except Exception as e:
        print(f"❌ Failed to start camera service: {e}")


# ============================================================
# MAIN ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🌱 GrowUp IoT Sensor Agent")
    print("=" * 60)
    print(f"Backend URL:            {BACKEND_URL}")
    print(f"Sensor endpoint:        {SENSOR_READINGS_ENDPOINT}")
    print(f"Plant growth endpoint:  {PLANT_GROWTH_ENDPOINT}")
    print(f"ML results endpoint:    {ML_RESULTS_ENDPOINT}")
    print(f"Device ID:              {DEVICE_ID}")
    print(f"Send Interval:          {SEND_INTERVAL}s")
    print(f"MQTT Broker:            {MQTT_BROKER}")
    print(f"Verbose Logging:        {VERBOSE_LOGGING}")
    print("=" * 60)
    print()
    
    # Setup MQTT control listener
    mqtt_client = setup_mqtt_control_listener()
    
    # Start camera service
    start_camera_service()
    
    # Main sensor read and send loop
    last_send_time = 0
    consecutive_failures = 0
    max_consecutive_failures = 10
    frame_count = 0
    
    try:
        while True:
            current_time = time.time()
            frame_count += 1
            
            # Read all sensors
            sensor_data = read_all_sensors()
            
            if sensor_data is None:
                time.sleep(1)
                continue
            
            # Send to backend every SEND_INTERVAL seconds
            if current_time - last_send_time >= SEND_INTERVAL:
                if VERBOSE_LOGGING:
                    print(f"\n📊 Frame {frame_count} | Sensor readings:")
                    for key, value in sensor_data.items():
                        print(f"   {key}: {value}")
                
                # Send sensor readings
                success = send_sensor_readings(sensor_data)
                
                # Optionally send plant growth data (can be triggered by events)
                # Example: send_plant_growth({...})
                
                if success:
                    last_send_time = current_time
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"🚨 WARNING: {consecutive_failures} consecutive backend failures!")
            
            # Process control commands from MQTT
            process_control_commands()
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down GrowUp IoT Sensor Agent...")
        if mqtt_client:
            mqtt_client.loop_stop()
        print("Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error in main loop: {e}")
        raise