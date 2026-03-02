from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import os

# Import camera and sensors from root directory
try:
    from camera_ml import CameraML
except ImportError:
    print("⚠️  camera_ml not available - ML features disabled")
    CameraML = None

try:
    from light_sensor import BH1750
    from temp_sensor import DS18B20
    from humidity_sensor import BME280Sensor
    from water_flow_sensor import FlowSensor
    from ammonia_sensor import MQ137
    from ph_sensor import PHSensor
    SENSORS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Some sensors not available: {e}")
    print("   Using mock sensor data")
    SENSORS_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

# Initialize sensors (only if available)
if SENSORS_AVAILABLE:
    try:
        light = BH1750()
        temp = DS18B20(4)
        humidity_sensor = BME280Sensor()
        flow = FlowSensor(5)
        ammonia = MQ137(0)
        ph = PHSensor(1)
        print("✅ Sensors initialized")
    except Exception as e:
        print(f"⚠️  Sensor initialization failed: {e}")
        print("   Will use mock data")
        SENSORS_AVAILABLE = False

# Initialize camera ML (only if available)
if CameraML:
    try:
        camera_ml = CameraML()
        print("✅ Camera ML initialized")
    except Exception as e:
        print(f"⚠️  Camera ML initialization failed: {e}")
        camera_ml = None
else:
    camera_ml = None

# Hardware control state (in-memory, will sync with GPIO in production)
hardware_state = {
    "pump": True,
    "fan": False,
    "phAdjustment": True,
    "aerator": True,
    "growLight": True
}

def read_all_sensors():
    """Consolidated sensor reading function matching frontend structure"""
    try:
        # Use real sensors if available
        if SENSORS_AVAILABLE:
            humidity_data = humidity_sensor.read()
            
            return {
                "waterTemp": temp.read_temp(),  # DS18B20
                "ph": ph.read(),  # PH4502C
                "dissolvedO2": 7.8,  # TODO: Add DO sensor when available
                "airTemp": humidity_data.get("temperature", 24.0),  # BME280
                "lightIntensity": light.read_light(),  # BH1750
                "waterLevel": 85,  # TODO: Add HC-SR04 sensor when available
                "waterFlow": flow.get_flow_rate(),  # YF-S201
                "humidity": humidity_data.get("humidity", 65),  # BME280
                "ammonia": ammonia.read(),  # MQ137
                "airPressure": humidity_data.get("pressure", 1013.25),  # BME280
            }
    except Exception as e:
        print(f"Error reading sensors: {e}")
    
    # Return mock defaults if sensors unavailable or failed
    return {
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

def get_ml_data():
    """Get ML inference results with plant metrics"""
    try:
        if camera_ml and camera_ml.last_result:
            # Extract plant metrics from ML model
            # TODO: Parse actual YOLO results for plant detection
            return {
                "height": 19.5,  # cm
                "leaves": 14,
                "health": 99,  # percentage
                "detections": len(camera_ml.last_result) if camera_ml.last_result else 0,
                "timestamp": None  # Will be set by backend
            }
    except Exception as e:
        print(f"Error reading ML data: {e}")
    
    return None

# ============================================
# SENSOR ENDPOINTS
# ============================================

@app.route('/sensors', methods=['GET'])
def get_sensors():
    """Get all sensor readings + ML data"""
    try:
        sensor_data = read_all_sensors()
        ml_data = get_ml_data()
        
        return jsonify({
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "data": {**sensor_data, **ml_data}
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ============================================
# HARDWARE CONTROL ENDPOINTS (NEW)
# ============================================

@app.route('/controls', methods=['GET'])
def get_controls():
    """Get current hardware control states"""
    try:
        return jsonify({
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "data": hardware_state
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/controls', methods=['POST'])
def update_controls():
    """
    Update hardware control states
    Body: { "pump": true, "fan": false, ... }
    """
    try:
        data = request.get_json()
        
        # Validate input
        valid_keys = {"pump", "fan", "phAdjustment", "aerator", "growLight"}
        for key in data:
            if key not in valid_keys:
                return jsonify({
                    "status": "error",
                    "message": f"Invalid control key: {key}"
                }), 400
        
        # Update state
        hardware_state.update(data)
        
        # TODO: In production, trigger GPIO pins here
        # Example:
        # import RPi.GPIO as GPIO
        # if 'pump' in data:
        #     GPIO.output(PUMP_PIN, GPIO.HIGH if data['pump'] else GPIO.LOW)
        # if 'fan' in data:
        #     GPIO.output(FAN_PIN, GPIO.HIGH if data['fan'] else GPIO.LOW)
        # ... etc
        
        print(f"✅ Hardware controls updated: {hardware_state}")
        
        return jsonify({
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "data": hardware_state,
            "message": "Controls updated successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/controls/<control_name>', methods=['PUT'])
def update_single_control(control_name):
    """
    Update a single hardware control
    Body: { "value": true }
    """
    try:
        if control_name not in hardware_state:
            return jsonify({
                "status": "error",
                "message": f"Invalid control: {control_name}"
            }), 400
        
        data = request.get_json()
        if 'value' not in data or not isinstance(data['value'], bool):
            return jsonify({
                "status": "error",
                "message": "Request must include 'value' as boolean"
            }), 400
        
        hardware_state[control_name] = data['value']
        
        # TODO: Trigger GPIO pin for this specific control
        print(f"✅ {control_name} set to {data['value']}")
        
        return jsonify({
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "data": {
                "control": control_name,
                "value": data['value']
            },
            "message": f"{control_name} updated successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ============================================
# SYSTEM STATUS ENDPOINT
# ============================================

@app.route('/status', methods=['GET'])
def get_system_status():
    """Get complete system status (sensors + controls)"""
    try:
        sensor_data = read_all_sensors()
        ml_data = get_ml_data()
        
        return jsonify({
            "status": "success",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "data": {
                "sensors": {**sensor_data, **ml_data},
                "controls": hardware_state,
                "uptime": "7d 14h 32m",  # TODO: Calculate actual uptime
                "firmware": "v2.1.3"
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 GrowUp IoT Flask Server Starting...")
    print("=" * 50)
    print("📡 Available Endpoints:")
    print("   GET  /sensors          - Get sensor readings + ML data")
    print("   GET  /controls         - Get current control states")
    print("   POST /controls         - Update all controls")
    print("   PUT  /controls/<name>  - Update single control")
    print("   GET  /status           - Get complete system status")
    print("=" * 50)
    print("🌐 Server running on http://0.0.0.0:5000")
    print("💡 Camera WebSocket runs separately on ngrok")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
