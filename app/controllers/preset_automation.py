"""
GrowUp IoT System - Preset Automation Handler
=============================================
Handles preset-based automation logic with manual override support.
"""

from typing import Dict, Optional
import time

class PresetAutomation:
    """Preset automation with manual override support"""
    
    # Preset definitions
    PRESETS = {
        "growth": {
            "pump": True,
            "fan": True,
            "aerator": True,
            "growLight": True,
        },
        "night": {
            "pump": True,
            "fan": False,
            "aerator": True,
            "growLight": False,
        },
        "maintenance": {
            "pump": False,
            "fan": True,
            "aerator": False,
            "growLight": True,
        },
        "eco": {
            "pump": True,
            "fan": False,
            "aerator": True,
            "growLight": False,
        }
    }
    
    def __init__(self, hardware_controller, mqtt_handler=None):
        self.hardware = hardware_controller
        self.mqtt = mqtt_handler
        self.last_apply_time = 0
        self.apply_interval = 5  # Apply preset every 5 seconds if needed
    
    def apply_active_preset(self) -> bool:
        """Apply active preset, respecting manual overrides"""
        if not self.mqtt:
            return False
        
        # Rate limit
        current_time = time.time()
        if current_time - self.last_apply_time < self.apply_interval:
            return False
        
        active_preset = self.mqtt.get_active_preset()
        if not active_preset or active_preset not in self.PRESETS:
            return False
        
        preset_config = self.PRESETS[active_preset]
        applied = False
        
        for device_name, preset_state in preset_config.items():
            # Only apply if no manual override
            if self.mqtt.apply_preset_if_no_override(device_name, preset_state):
                applied = True
        
        if applied:
            self.last_apply_time = current_time
        
        return applied
    
    def get_preset_names(self):
        """Get list of available presets"""
        return list(self.PRESETS.keys())
