"""
GrowUp IoT System - MQTT Control Handler
========================================
Handles MQTT-based device control with preset and manual override support.
"""

import os
import time
import threading
from typing import Optional, Dict
import paho.mqtt.client as mqtt


class MQTTControlHandler:
    """MQTT control handler with preset and manual override support"""
    
    def __init__(self, hardware_controller, device_id: str = None):
        self.hardware = hardware_controller
        self.device_id = device_id or os.getenv('DEVICE_ID', 'rpi-001')
        
        self.broker = os.getenv('MQTT_BROKER', 'localhost')
        self.port = int(os.getenv('MQTT_PORT', '1883'))
        self.username = os.getenv('MQTT_USERNAME')
        self.password = os.getenv('MQTT_PASSWORD')
        
        self.client = mqtt.Client(client_id=f"growup-{self.device_id}")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        self.connected = False
        self.running = False
        
        # Hybrid control state
        self.active_preset = None
        self.manual_overrides = {}
        self.preset_lock = threading.Lock()
        
        self.device_topics = {
            f"growup/device/{self.device_id}/pump": "pump",
            f"growup/device/{self.device_id}/fan": "fan",
            f"growup/device/{self.device_id}/aerator": "aerator",
            f"growup/device/{self.device_id}/growlight": "growLight",
        }
        
        self.preset_topic = f"growup/device/{self.device_id}/preset"
        self.clear_override_topic = f"growup/device/{self.device_id}/clear-override"
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ MQTT connected to {self.broker}:{self.port}")
            
            # Subscribe to device control topics
            for topic in self.device_topics.keys():
                client.subscribe(topic)
                print(f"   📡 Subscribed: {topic}")
            
            # Subscribe to preset topic
            client.subscribe(self.preset_topic)
            print(f"   📡 Subscribed: {self.preset_topic}")
            
            # Subscribe to clear override topic
            client.subscribe(self.clear_override_topic)
            print(f"   📡 Subscribed: {self.clear_override_topic}")
        else:
            print(f"❌ MQTT connection failed: {rc}")
            self.connected = False
    
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode('utf-8').strip()
        
        # Handle preset change
        if topic == self.preset_topic:
            self._handle_preset_change(payload)
            return
        
        # Handle clear override
        if topic == self.clear_override_topic:
            self._handle_clear_override(payload)
            return
        
        # Handle individual device control
        if topic in self.device_topics:
            control_name = self.device_topics[topic]
            self._handle_device_control(control_name, payload)
    
    def _handle_preset_change(self, preset_name: str):
        with self.preset_lock:
            if preset_name == "none" or preset_name == "":
                self.active_preset = None
                self.manual_overrides.clear()
                print(f"🔄 Preset cleared - full automation disabled")
            else:
                self.active_preset = preset_name
                print(f"🔄 Active preset changed: {preset_name}")
    
    def _handle_clear_override(self, device_name: str):
        with self.preset_lock:
            if device_name == "all":
                self.manual_overrides.clear()
                print(f"🔄 All manual overrides cleared")
            elif device_name in self.manual_overrides:
                del self.manual_overrides[device_name]
                print(f"🔄 Manual override cleared: {device_name}")
    
    def _handle_device_control(self, control_name: str, payload: str):
        if payload.lower() == "true":
            state = True
        elif payload.lower() == "false":
            state = False
        else:
            print(f"⚠️  Invalid payload for {control_name}: {payload}")
            return
        
        # Set manual override
        with self.preset_lock:
            self.manual_overrides[control_name] = state
        
        # Apply to hardware
        if self.hardware:
            success = self.hardware.update_control(control_name, state)
            if success:
                status = "ON" if state else "OFF"
                print(f"🔌 MQTT manual: {control_name} → {status}")
    
    def is_device_manual(self, device_name: str) -> bool:
        """Check if device has manual override"""
        with self.preset_lock:
            return device_name in self.manual_overrides
    
    def get_manual_override(self, device_name: str) -> Optional[bool]:
        """Get manual override state for device"""
        with self.preset_lock:
            return self.manual_overrides.get(device_name)
    
    def get_active_preset(self) -> Optional[str]:
        """Get current active preset"""
        with self.preset_lock:
            return self.active_preset
    
    def apply_preset_if_no_override(self, device_name: str, preset_state: bool) -> bool:
        """Apply preset state only if no manual override exists"""
        with self.preset_lock:
            if device_name in self.manual_overrides:
                return False
            
            if self.hardware:
                self.hardware.update_control(device_name, preset_state)
            return True
    
    def start(self) -> bool:
        """Start MQTT control handler"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.running = True
            self.client.loop_start()
            time.sleep(1)
            return self.connected
        except Exception as e:
            print(f"❌ MQTT connection error: {e}")
            return False
    
    def stop(self):
        """Stop MQTT control handler"""
        self.running = False
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
        print("🛑 MQTT control handler stopped")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            print(f"⚠️  MQTT disconnected unexpectedly: {rc}")

# Singleton instance
_mqtt_handler: Optional[MQTTControlHandler] = None

def get_mqtt_handler() -> Optional[MQTTControlHandler]:
    """Get MQTT control handler singleton"""
    global _mqtt_handler
    if _mqtt_handler is None:
        try:
            from hardware_control import get_hardware_controller
            hardware = get_hardware_controller()
            _mqtt_handler = MQTTControlHandler(hardware)
        except Exception as e:
            print(f"❌ Failed to create MQTT handler: {e}")
            return None
    return _mqtt_handler
