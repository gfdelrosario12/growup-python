"""
GrowUp IoT System - Main Entry Point
=====================================
Single unified entry point that coordinates ALL system components:

1. Sensor Reading (every 1s, send to backend every 60s or on significant change)
2. Hardware Control (poll backend every 5s, apply GPIO changes)
3. Camera ML Detection (YOLO object detection with WebSocket)
4. LCD Viewer GUI (optional, Tkinter interface)
5. Backend Communication (Spring Boot REST API)

Usage:
    python3 main.py                    # Run without LCD viewer
    python3 main.py --lcd              # Run with LCD viewer
    python3 main.py --lcd --demo       # Run with LCD viewer in demo mode
    python3 main.py --no-camera        # Run without camera ML

Architecture:
Frontend ← → Spring Boot Backend ← → Raspberry Pi (this script)
                                     ↓
                                   GPIO Hardware + Camera + LCD
"""

import time
import requests
import threading
import argparse
import sys
import signal
from typing import Dict, Optional
from datetime import datetime

# Import configuration - Temporary: using old config until full migration
# TODO: Migrate to src.config.settings
try:
    from config import (
        BACKEND_SENSOR_READINGS,
        BACKEND_CONTROLS,
        SEND_INTERVAL,
        CONTROL_POLL_INTERVAL,
        REQUEST_TIMEOUT,
        VERBOSE_LOGGING,
        LOG_SENSOR_READINGS,
        LOG_CONTROL_CHANGES,
        is_significant_change,
        print_config
    )
except (ImportError, ModuleNotFoundError):
    # Fallback: use defaults if config.py is deleted
    print("⚠️  Old config.py not found, using defaults")
    BACKEND_SENSOR_READINGS = "http://localhost:8080/api/sensor-readings"
    BACKEND_CONTROLS = "http://localhost:8080/api/controls"
    SEND_INTERVAL = 60
    CONTROL_POLL_INTERVAL = 5
    REQUEST_TIMEOUT = 10
    VERBOSE_LOGGING = True
    LOG_SENSOR_READINGS = True
    LOG_CONTROL_CHANGES = True
    
    def is_significant_change(key, old_val, new_val):
        thresholds = {
            "waterTemp": 0.5, "ph": 0.2, "dissolvedO2": 0.5,
            "ammonia": 0.05, "airTemp": 1.0, "waterFlow": 2.0,
            "humidity": 5.0, "lightIntensity": 100
        }
        threshold = thresholds.get(key, 0)
        return abs(new_val - old_val) >= threshold
    
    def print_config():
        print(f"Backend: {BACKEND_SENSOR_READINGS}")
        print(f"Send Interval: {SEND_INTERVAL}s")
        print(f"Control Poll: {CONTROL_POLL_INTERVAL}s")

# Import hardware controller
from hardware_control import get_hardware_controller, cleanup_hardware

# Import sensor reading
from server import read_all_sensors, get_ml_data

class GrowUpSystem:
    """Main system coordinator - integrates all components"""
    
    def __init__(self, enable_lcd=False, enable_camera=True, demo_mode=False):
        self.running = False
        self.enable_lcd = enable_lcd
        self.enable_camera = enable_camera
        self.demo_mode = demo_mode
        
        # State management
        self.last_sensor_data = {}
        self.last_send_time = 0
        self.consecutive_failures = 0
        
        # Component references
        self.hardware = None
        self.lcd_viewer = None
        self.camera_thread = None
        self.mqtt_handler = None  # MQTT control handler
        self.preset_automation = None  # Preset automation handler
        
        # Shared data for LCD viewer
        self.shared_data = {
            'sensors': {},
            'controls': {},
            'detections': [],
            'logs': []
        }
        
        print("\n" + "="*60)
        print("🌱 GrowUp IoT System Initializing...")
        print("="*60)
        print_config()
        print(f"LCD Viewer: {'✅ Enabled' if enable_lcd else '❌ Disabled'}")
        print(f"Camera ML: {'✅ Enabled' if enable_camera else '❌ Disabled'}")
        print(f"Demo Mode: {'✅ Enabled' if demo_mode else '❌ Disabled'}")
        print("="*60 + "\n")
    
    def initialize_components(self):
        """Initialize all system components"""
        try:
            # Initialize hardware controller
            if not self.demo_mode:
                self.hardware = get_hardware_controller()
                self.log("✅ Hardware controller initialized")
            else:
                self.log("⚠️  Running in DEMO mode (no GPIO)")
            
            # Initialize MQTT control handler (if not demo mode)
            if not self.demo_mode:
                try:
                    from mqtt_control import get_mqtt_handler
                    self.mqtt_handler = get_mqtt_handler()
                    if self.mqtt_handler.start():
                        self.log("✅ MQTT control handler started")
                    else:
                        self.log("⚠️  MQTT control handler failed to start")
                except ImportError:
                    self.log("⚠️  MQTT control not available (paho-mqtt not installed)")
                except Exception as e:
                    self.log(f"⚠️  MQTT control initialization failed: {e}")
            
            # Initialize camera ML if enabled
            if self.enable_camera and not self.demo_mode:
                self.start_camera_ml()
            
            # Initialize LCD viewer if enabled
            if self.enable_lcd:
                self.start_lcd_viewer()
            
            return True
            
        except Exception as e:
            self.log(f"❌ Component initialization failed: {e}")
            return False
    
    def start_camera_ml(self):
        """Start camera ML detection in separate thread"""
        try:
            from camera_ws import start_camera_detection
            self.camera_thread = threading.Thread(
                target=start_camera_detection,
                args=(self.on_detection_callback,),
                daemon=True
            )
            self.camera_thread.start()
            self.log("✅ Camera ML detection started")
        except (ImportError, ModuleNotFoundError) as e:
            self.log(f"⚠️  Camera ML not available: {e}")
        except Exception as e:
            self.log(f"⚠️  Camera ML initialization failed: {e}")
    
    def on_detection_callback(self, detections):
        """Callback when camera detects objects"""
        self.shared_data['detections'] = detections
        if self.lcd_viewer:
            self.lcd_viewer.update_detections(detections)
    
    def start_lcd_viewer(self):
        """Start LCD viewer in separate thread"""
        try:
            from lcd_viewer import LCDViewer
            
            def run_lcd():
                self.lcd_viewer = LCDViewer(demo_mode=self.demo_mode)
                self.lcd_viewer.run()
            
            lcd_thread = threading.Thread(target=run_lcd, daemon=False)
            lcd_thread.start()
            self.log("✅ LCD Viewer started")
            
        except ImportError as e:
            self.log(f"⚠️  LCD Viewer not available: {e}")
            self.log("    Install tkinter: sudo apt-get install python3-tk")
        except Exception as e:
            self.log(f"⚠️  LCD Viewer initialization failed: {e}")
    
    def check_significant_change(self, new_data: Dict) -> bool:
        """Check if any sensor has changed significantly"""
        if not self.last_sensor_data:
            return True  # First reading
        
        for key, new_value in new_data.items():
            if key in self.last_sensor_data:
                old_value = self.last_sensor_data[key]
                if isinstance(new_value, (int, float)) and isinstance(old_value, (int, float)):
                    if is_significant_change(key, old_value, new_value):
                        if VERBOSE_LOGGING:
                            self.log(f"⚡ Significant change: {key} {old_value} → {new_value}")
                        return True
        
        return False
    
    def send_sensor_data_to_backend(self):
        """Send sensor data to Spring Boot backend"""
        try:
            # Read sensors
            sensor_data = read_all_sensors() if not self.demo_mode else self.get_mock_sensors()
            ml_data = get_ml_data() if not self.demo_mode else {}
            
            if not sensor_data:
                return
            
            combined_data = {**sensor_data, **ml_data}
            
            # Update shared data for LCD
            self.shared_data['sensors'] = combined_data
            if self.lcd_viewer:
                self.lcd_viewer.update_sensors(combined_data)
            
            # Check if we should send
            current_time = time.time()
            time_since_last_send = current_time - self.last_send_time
            
            should_send = (
                time_since_last_send >= SEND_INTERVAL or
                self.check_significant_change(combined_data)
            )
            
            if not should_send:
                return
            
            # Prepare payload for Spring Boot
            payload = {
                "waterTemp": combined_data.get("waterTemp"),
                "phLevel": combined_data.get("ph"),  # Backend uses phLevel
                "dissolvedO2": combined_data.get("dissolvedO2"),
                "airTemp": combined_data.get("airTemp"),
                "lightIntensity": combined_data.get("lightIntensity"),
                "waterLevel": combined_data.get("waterLevel"),
                "waterFlow": combined_data.get("waterFlow"),
                "humidity": combined_data.get("humidity"),
                "ammonia": combined_data.get("ammonia"),
                "airPressure": combined_data.get("airPressure"),
                "plantHeight": combined_data.get("plantHeight"),
                "plantLeaves": combined_data.get("plantLeaves"),
                "plantHealth": combined_data.get("plantHealth"),
            }
            
            # Send to backend
            response = requests.post(
                BACKEND_SENSOR_READINGS,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if LOG_SENSOR_READINGS:
                    quality = result.get("waterQualityScore", "N/A")
                    health = result.get("healthStatus", "N/A")
                    self.log(f"📤 Sent to backend | Quality: {quality} | Status: {health}")
                
                # Update state
                self.last_sensor_data = combined_data
                self.last_send_time = current_time
                self.consecutive_failures = 0
            else:
                self.log(f"⚠️  Backend returned {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 5:
                self.log(f"🚨 WARNING: {self.consecutive_failures} consecutive backend failures!")
            
        except Exception as e:
            self.log(f"❌ Error sending sensor data: {e}")
    
    def poll_control_updates_from_backend(self):
        """Poll backend for control updates from frontend"""
        try:
            response = requests.get(
                f"{BACKEND_CONTROLS}/latest",
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                controls = data.get("controls", {})
                
                if controls:
                    # Update shared data for LCD
                    self.shared_data['controls'] = controls
                    if self.lcd_viewer:
                        self.lcd_viewer.update_controls(controls)
                    
                    # Apply controls to hardware (respecting manual overrides)
                    if self.hardware:
                        current_states = self.hardware.get_all_states()
                        
                        for control_name, desired_state in controls.items():
                            # Skip if device has manual override
                            if self.mqtt_handler and self.mqtt_handler.is_device_manual(control_name):
                                continue
                            
                            current_state = current_states.get(control_name)
                            
                            if current_state != desired_state:
                                success = self.hardware.update_control(control_name, desired_state)
                                
                                if success and LOG_CONTROL_CHANGES:
                                    status = "ON" if desired_state else "OFF"
                                    self.log(f"🔄 Backend update: {control_name} → {status}")
                        
                        # Send acknowledgment
                        self.send_control_acknowledgment(self.hardware.get_all_states())
            
        except requests.exceptions.RequestException:
            pass  # Silent fail for control polling
        except Exception as e:
            self.log(f"❌ Error polling controls: {e}")
    
    def send_control_acknowledgment(self, states: Dict[str, bool]):
        """Send current control states back to backend"""
        try:
            requests.post(
                f"{BACKEND_CONTROLS}/acknowledge",
                json={"controls": states, "timestamp": datetime.now().isoformat()},
                timeout=REQUEST_TIMEOUT
            )
        except Exception:
            pass  # Silent fail
    
    def sensor_loop(self):
        """Main sensor reading and sending loop"""
        self.log("📊 Sensor loop started")
        
        while self.running:
            try:
                self.send_sensor_data_to_backend()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.log(f"❌ Sensor loop error: {e}")
                time.sleep(5)
    
    def control_loop(self):
        """Poll backend for control updates"""
        self.log("🎛️  Control loop started")
        
        while self.running:
            try:
                self.poll_control_updates_from_backend()
                time.sleep(CONTROL_POLL_INTERVAL)
            except Exception as e:
                self.log(f"❌ Control loop error: {e}")
                time.sleep(5)
    
    def get_mock_sensors(self):
        """Mock sensor data for demo mode"""
        import random
        return {
            "waterTemp": round(22 + random.uniform(-2, 2), 1),
            "ph": round(7.0 + random.uniform(-0.3, 0.3), 2),
            "dissolvedO2": round(7.5 + random.uniform(-1, 1), 1),
            "airTemp": round(24 + random.uniform(-2, 2), 1),
            "lightIntensity": int(800 + random.uniform(-200, 200)),
            "waterLevel": int(80 + random.uniform(-10, 10)),
            "waterFlow": round(10 + random.uniform(-2, 2), 1),
            "humidity": int(60 + random.uniform(-10, 10)),
            "ammonia": round(0.05 + random.uniform(-0.02, 0.02), 3),
            "airPressure": round(1013 + random.uniform(-5, 5), 1),
        }
    
    def log(self, message: str):
        """Centralized logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        # Add to shared logs for LCD
        self.shared_data['logs'].append(log_entry)
        if len(self.shared_data['logs']) > 100:
            self.shared_data['logs'] = self.shared_data['logs'][-100:]
    
    def start(self):
        """Start the integrated system"""
        self.log("🚀 Starting GrowUp IoT System...")
        
        if not self.initialize_components():
            self.log("❌ Failed to initialize components")
            return
        
        self.running = True
        
        # Start sensor loop
        sensor_thread = threading.Thread(target=self.sensor_loop, daemon=True)
        sensor_thread.start()
        
        # Start control loop
        control_thread = threading.Thread(target=self.control_loop, daemon=True)
        control_thread.start()
        
        self.log("✅ All systems operational")
        self.log("📤 Sending data every 60s or on significant change")
        self.log("📥 Polling controls every 5s")
        self.log("Press Ctrl+C to stop\n")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("\n🛑 Shutting down...")
            self.stop()
    
    def stop(self):
        """Stop all system components"""
        self.running = False
        
        # Stop MQTT control handler
        if self.mqtt_handler:
            try:
                self.mqtt_handler.stop()
            except Exception as e:
                self.log(f"⚠️  Error stopping MQTT handler: {e}")
        
        if self.hardware:
            cleanup_hardware()
        
        self.log("✅ System stopped")
        sys.exit(0)

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Received interrupt signal...")
    sys.exit(0)

def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='GrowUp IoT System - Integrated Aquaponics Monitor & Control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py                    # Run without LCD viewer
  python3 main.py --lcd              # Run with LCD viewer
  python3 main.py --lcd --demo       # Run in demo mode (no hardware)
  python3 main.py --no-camera        # Run without camera ML
        """
    )
    
    parser.add_argument(
        '--lcd',
        action='store_true',
        help='Enable LCD viewer GUI'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Run in demo mode (mock sensors, no GPIO)'
    )
    
    parser.add_argument(
        '--no-camera',
        action='store_true',
        help='Disable camera ML detection'
    )
    
    args = parser.parse_args()
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start system
    system = GrowUpSystem(
        enable_lcd=args.lcd,
        enable_camera=not args.no_camera,
        demo_mode=args.demo
    )
    
    system.start()

if __name__ == "__main__":
    main()
