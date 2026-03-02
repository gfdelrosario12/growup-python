#!/usr/bin/env python3
"""
GrowUp IoT System - Main Entry Point
=====================================
Unified entry point that coordinates ALL system components with modular architecture:

1. Sensor Reading & Data Sync
2. Hardware Control (GPIO relays)
3. Preset Automation (with manual override support)
4. MQTT Control Handler
5. Camera ML Detection (YOLO)
6. LCD Viewer (optional)
7. REST API Server
8. WebSocket Camera Stream

Usage:
    python3 main.py                    # Run full system
    python3 main.py --no-lcd           # Run without LCD viewer
    python3 main.py --no-camera        # Run without camera ML
    python3 main.py --api-only         # Run only REST API server
    python3 main.py --camera-only      # Run only camera WebSocket server

Architecture:
    Frontend ←→ Spring Boot Backend ←→ Raspberry Pi (this script)
                                         ↓
                                       GPIO Hardware + Sensors + Camera + LCD
"""

import time
import argparse
import sys
import signal
import threading
from typing import Optional

# Import modular components
from app.controllers.hardware_control import HardwareController, cleanup_hardware
from app.controllers.mqtt_control import MQTTControlHandler
from app.controllers.preset_automation import PresetAutomation
from app.sensors.temp_sensor import read_water_temp, read_air_temp
from app.sensors.ph_sensor import read_ph
from app.sensors.humidity_sensor import read_humidity
from app.sensors.light_sensor import read_light_intensity
from app.sensors.ammonia_sensor import read_ammonia
from app.sensors.water_flow_sensor import read_water_flow
from app.utils.config import (
    BACKEND_SENSOR_READINGS,
    BACKEND_CONTROLS,
    SEND_INTERVAL,
    CONTROL_POLL_INTERVAL,
    VERBOSE_LOGGING,
    print_config
)
from app.utils.influxdb_client import InfluxDBClient
from app.utils.system_manager import SystemManager

# Optional components
try:
    from app.services.camera_ml import start_camera_ml
    CAMERA_ML_AVAILABLE = True
except ImportError:
    print("⚠️  Camera ML not available (missing dependencies)")
    CAMERA_ML_AVAILABLE = False

try:
    from app.services.lcd_viewer import LCDViewer
    LCD_AVAILABLE = True
except ImportError:
    print("⚠️  LCD Viewer not available (missing tkinter)")
    LCD_AVAILABLE = False


class GrowUpSystem:
    """Main system coordinator - integrates all modular components"""
    
    def __init__(self, enable_lcd=False, enable_camera=True):
        self.running = False
        self.enable_lcd = enable_lcd and LCD_AVAILABLE
        self.enable_camera = enable_camera and CAMERA_ML_AVAILABLE
        
        # State management
        self.last_sensor_data = {}
        self.last_send_time = 0
        self.consecutive_failures = 0
        
        # Core components
        self.hardware: Optional[HardwareController] = None
        self.mqtt: Optional[MQTTControlHandler] = None
        self.preset_automation: Optional[PresetAutomation] = None
        self.influx_client: Optional[InfluxDBClient] = None
        self.system_manager: Optional[SystemManager] = None
        
        # Optional components
        self.lcd_viewer: Optional['LCDViewer'] = None
        self.camera_thread: Optional[threading.Thread] = None
        
        # Worker threads
        self.sensor_thread: Optional[threading.Thread] = None
        self.control_thread: Optional[threading.Thread] = None
        self.automation_thread: Optional[threading.Thread] = None
    
    def initialize(self):
        """Initialize all system components"""
        print("\n" + "=" * 70)
        print("🌱 GrowUp IoT System - Modular Architecture")
        print("=" * 70)
        print_config()
        print("=" * 70)
        
        # Initialize hardware controller
        print("\n🔧 Initializing Hardware Controller...")
        self.hardware = HardwareController()
        
        # Initialize MQTT control handler
        print("📡 Initializing MQTT Control Handler...")
        self.mqtt = MQTTControlHandler(self.hardware)
        
        # Initialize preset automation
        print("🤖 Initializing Preset Automation...")
        self.preset_automation = PresetAutomation(self.hardware, self.mqtt)
        
        # Initialize InfluxDB client
        print("📊 Initializing InfluxDB Client...")
        self.influx_client = InfluxDBClient()
        
        # Initialize system manager
        print("⚙️  Initializing System Manager...")
        self.system_manager = SystemManager()
        
        # Initialize LCD viewer if enabled
        if self.enable_lcd:
            print("🖥️  Initializing LCD Viewer...")
            self.lcd_viewer = LCDViewer(self)
        
        # Initialize camera ML if enabled
        if self.enable_camera:
            print("📷 Initializing Camera ML (YOLO)...")
            self.camera_thread = threading.Thread(target=start_camera_ml, daemon=True)
        
        print("\n✅ All components initialized successfully!")
        print("=" * 70 + "\n")
    
    def start(self):
        """Start all system components"""
        self.running = True
        
        # Start MQTT handler
        if self.mqtt:
            print("🚀 Starting MQTT Handler...")
            self.mqtt.start()
        
        # Start camera ML
        if self.camera_thread:
            print("🚀 Starting Camera ML...")
            self.camera_thread.start()
        
        # Start LCD viewer
        if self.lcd_viewer:
            print("🚀 Starting LCD Viewer...")
            # LCD runs in main thread (Tkinter requirement)
            threading.Thread(target=self._run_lcd, daemon=True).start()
        
        # Start sensor reading thread
        print("🚀 Starting Sensor Reading Thread...")
        self.sensor_thread = threading.Thread(target=self._sensor_loop, daemon=True)
        self.sensor_thread.start()
        
        # Start control polling thread
        print("🚀 Starting Control Polling Thread...")
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        
        # Start automation thread
        print("🚀 Starting Preset Automation Thread...")
        self.automation_thread = threading.Thread(target=self._automation_loop, daemon=True)
        self.automation_thread.start()
        
        print("\n✅ All threads started!")
        print("=" * 70)
        print("📡 System is now running...")
        print("   - Press Ctrl+C to stop")
        print("=" * 70 + "\n")
    
    def _sensor_loop(self):
        """Sensor reading and data sync loop"""
        while self.running:
            try:
                # Read all sensors
                sensor_data = {
                    "waterTemp": read_water_temp(),
                    "airTemp": read_air_temp(),
                    "ph": read_ph(),
                    "humidity": read_humidity(),
                    "lightIntensity": read_light_intensity(),
                    "ammonia": read_ammonia(),
                    "waterFlow": read_water_flow(),
                    "timestamp": int(time.time() * 1000)
                }
                
                # Update LCD if enabled
                if self.lcd_viewer:
                    self.lcd_viewer.update_sensor_data(sensor_data)
                
                # Send to backend (every SEND_INTERVAL or on significant change)
                current_time = time.time()
                if (current_time - self.last_send_time >= SEND_INTERVAL or
                    self._has_significant_change(sensor_data)):
                    
                    if self._send_sensor_data(sensor_data):
                        self.last_send_time = current_time
                        self.consecutive_failures = 0
                    else:
                        self.consecutive_failures += 1
                
                # Store to InfluxDB
                if self.influx_client:
                    self.influx_client.write_sensor_data(sensor_data)
                
                # Update last data
                self.last_sensor_data = sensor_data
                
            except Exception as e:
                print(f"❌ Sensor loop error: {e}")
            
            time.sleep(1)  # Read sensors every 1 second
    
    def _control_loop(self):
        """Control polling loop - fetch backend control state"""
        while self.running:
            try:
                # Poll backend for control state
                # Backend should reflect MQTT control state
                # This is for backward compatibility
                pass
                
            except Exception as e:
                print(f"❌ Control loop error: {e}")
            
            time.sleep(CONTROL_POLL_INTERVAL)
    
    def _automation_loop(self):
        """Preset automation loop"""
        while self.running:
            try:
                if self.preset_automation:
                    self.preset_automation.apply_active_preset()
            except Exception as e:
                print(f"❌ Automation loop error: {e}")
            
            time.sleep(1)  # Check every second
    
    def _run_lcd(self):
        """Run LCD viewer (must be in separate thread due to Tkinter)"""
        if self.lcd_viewer:
            self.lcd_viewer.run()
    
    def _has_significant_change(self, new_data: dict) -> bool:
        """Check if sensor data has significant change"""
        if not self.last_sensor_data:
            return True
        
        thresholds = {
            "waterTemp": 0.5,
            "airTemp": 1.0,
            "ph": 0.2,
            "humidity": 5.0,
            "lightIntensity": 100,
            "ammonia": 0.05,
            "waterFlow": 2.0
        }
        
        for key, threshold in thresholds.items():
            old_val = self.last_sensor_data.get(key, 0)
            new_val = new_data.get(key, 0)
            if abs(new_val - old_val) >= threshold:
                return True
        
        return False
    
    def _send_sensor_data(self, data: dict) -> bool:
        """Send sensor data to backend"""
        try:
            import requests
            response = requests.post(
                BACKEND_SENSOR_READINGS,
                json=data,
                timeout=10
            )
            if response.status_code == 200:
                if VERBOSE_LOGGING:
                    print(f"✅ Sensor data sent: {data}")
                return True
            else:
                print(f"❌ Failed to send sensor data: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending sensor data: {e}")
            return False
    
    def get_control_state(self) -> dict:
        """Get current control state"""
        if self.hardware:
            return self.hardware.get_control_state()
        return {}
    
    def stop(self):
        """Stop all components gracefully"""
        print("\n🛑 Stopping GrowUp IoT System...")
        self.running = False
        
        # Stop MQTT
        if self.mqtt:
            self.mqtt.stop()
        
        # Stop LCD
        if self.lcd_viewer:
            self.lcd_viewer.stop()
        
        # Cleanup hardware
        if self.hardware:
            cleanup_hardware()
        
        print("✅ System stopped gracefully")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='GrowUp IoT System')
    parser.add_argument('--lcd', action='store_true', help='Enable LCD viewer')
    parser.add_argument('--no-lcd', action='store_true', help='Disable LCD viewer')
    parser.add_argument('--no-camera', action='store_true', help='Disable camera ML')
    parser.add_argument('--api-only', action='store_true', help='Run only REST API server')
    parser.add_argument('--camera-only', action='store_true', help='Run only camera WebSocket server')
    args = parser.parse_args()
    
    # Run specific component only
    if args.api_only:
        print("🚀 Running REST API Server only...")
        from app.api.server import app
        app.run(host='0.0.0.0', port=5000, debug=False)
        return
    
    if args.camera_only:
        print("🚀 Running Camera WebSocket Server only...")
        import asyncio
        from app.services.camera_ws import start_server
        asyncio.run(start_server())
        return
    
    # Determine LCD setting
    enable_lcd = args.lcd and not args.no_lcd
    enable_camera = not args.no_camera
    
    # Create and initialize system
    system = GrowUpSystem(enable_lcd=enable_lcd, enable_camera=enable_camera)
    
    def signal_handler(sig, frame):
        print("\n⚠️  Received interrupt signal...")
        system.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        system.initialize()
        system.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Keyboard interrupt received...")
        system.stop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        system.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
