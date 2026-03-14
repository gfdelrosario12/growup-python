"""
Device Control Handler Module
==============================
Handles incoming MQTT control commands and applies them to hardware.
Supports modes: AUTO, MANUAL
Actions: pump, light, heater, fan, etc.
"""

import os
from typing import Dict, Callable, Optional
from enum import Enum

class ControlMode(Enum):
    """Device control modes."""
    AUTO = "AUTO"      # Automatic control based on sensor readings
    MANUAL = "MANUAL"  # Manual control via backend commands


class ControlAction(Enum):
    """Supported control actions."""
    PUMP = "pump"
    LIGHT = "light"
    HEATER = "heater"
    FAN = "fan"
    VENT = "vent"


class DeviceController:
    """
    Centralized device control handler.
    Manages control mode, actions, and hardware callbacks.
    """
    
    def __init__(self, device_id: str = "pi-001", verbose: bool = False):
        """
        Initialize device controller.
        
        Args:
            device_id: Device identifier
            verbose: Enable verbose logging
        """
        self.device_id = device_id
        self.verbose = verbose
        self.mode = ControlMode.AUTO
        self.actions = {}  # {action: callback_function}
        self.action_history = []  # Track executed actions
    
    def register_action(self, action: str, callback: Callable[[str], bool]) -> None:
        """
        Register a hardware control action callback.
        
        Args:
            action: Action name (e.g., "pump", "light")
            callback: Function that executes the action
                     Signature: callback(value: str) -> bool
                     Example: callback("on") returns True if successful
        
        Example:
            controller.register_action("pump", hardware.set_pump_state)
        """
        self.actions[action] = callback
        self._log(f"✅ Registered action: {action}")
    
    def set_mode(self, mode: str) -> bool:
        """
        Set device control mode.
        
        Args:
            mode: "AUTO" or "MANUAL"
        
        Returns:
            bool: True if mode changed successfully
        """
        try:
            mode_enum = ControlMode[mode.upper()]
            self.mode = mode_enum
            self._log(f"🎮 Control mode changed to {mode_enum.value}")
            self.action_history.append({
                "action": "mode",
                "value": mode_enum.value,
                "status": "success"
            })
            return True
        except KeyError:
            print(f"❌ Invalid mode: {mode}. Use AUTO or MANUAL")
            return False
    
    def execute_action(self, action: str, value: str) -> bool:
        """
        Execute a control action.
        
        Args:
            action: Action name (e.g., "pump")
            value: Action value (e.g., "on", "off", "80")
        
        Returns:
            bool: True if action executed successfully
        """
        # Check if action is registered
        if action not in self.actions:
            print(f"❌ Action not registered: {action}")
            return False
        
        # Check if we're in the right mode
        if self.mode == ControlMode.AUTO:
            self._log(f"⚠️  Skipping action '{action}' (AUTO mode, backend control disabled)")
            return False
        
        # Execute the action
        try:
            callback = self.actions[action]
            result = callback(value)
            
            if result:
                self._log(f"✅ Action '{action}' executed with value '{value}'")
                self.action_history.append({
                    "action": action,
                    "value": value,
                    "status": "success"
                })
            else:
                print(f"❌ Action '{action}' failed to execute")
                self.action_history.append({
                    "action": action,
                    "value": value,
                    "status": "failed"
                })
            
            return result
        except Exception as e:
            print(f"❌ Error executing action '{action}': {e}")
            self.action_history.append({
                "action": action,
                "value": value,
                "status": "error",
                "error": str(e)
            })
            return False
    
    def parse_mqtt_command(self, payload: str) -> bool:
        """
        Parse and execute MQTT control command.
        
        Format: action:value
        Examples:
            - pump:on
            - pump:off
            - light:80
            - heater:25.5
            - mode:MANUAL
        
        Args:
            payload: MQTT message payload
        
        Returns:
            bool: True if command executed successfully
        """
        try:
            parts = payload.split(":", 1)
            if len(parts) != 2:
                print(f"❌ Invalid command format: {payload}. Use 'action:value'")
                return False
            
            action, value = parts
            
            # Special handling for mode change
            if action.lower() == "mode":
                return self.set_mode(value)
            
            # Execute regular action
            return self.execute_action(action.lower(), value.lower())
        
        except Exception as e:
            print(f"❌ Error parsing MQTT command: {e}")
            return False
    
    def get_status(self) -> Dict:
        """Get current control status."""
        return {
            "device_id": self.device_id,
            "mode": self.mode.value,
            "registered_actions": list(self.actions.keys()),
            "last_actions": self.action_history[-10:] if self.action_history else []
        }
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)


# Mock hardware callbacks for testing
class MockHardware:
    """Mock hardware for testing without real GPIO."""
    
    @staticmethod
    def set_pump(state: str) -> bool:
        """Mock pump control."""
        print(f"💧 [MOCK] Pump set to: {state}")
        return state.lower() in ("on", "off")
    
    @staticmethod
    def set_light(brightness: str) -> bool:
        """Mock light control (0-100)."""
        try:
            brightness_val = int(brightness)
            if 0 <= brightness_val <= 100:
                print(f"💡 [MOCK] Light set to: {brightness}%")
                return True
        except ValueError:
            pass
        print(f"❌ [MOCK] Invalid brightness: {brightness}")
        return False
    
    @staticmethod
    def set_heater(temp: str) -> bool:
        """Mock heater control."""
        try:
            temp_val = float(temp)
            if 0 <= temp_val <= 50:
                print(f"🔥 [MOCK] Heater set to: {temp}°C")
                return True
        except ValueError:
            pass
        print(f"❌ [MOCK] Invalid temperature: {temp}")
        return False
    
    @staticmethod
    def set_fan(speed: str) -> bool:
        """Mock fan control."""
        print(f"🌀 [MOCK] Fan set to: {speed}")
        return speed.lower() in ("off", "low", "medium", "high")


# Example usage:
# controller = DeviceController("pi-001", verbose=True)
# controller.register_action("pump", MockHardware.set_pump)
# controller.register_action("light", MockHardware.set_light)
# controller.register_action("heater", MockHardware.set_heater)
# controller.register_action("fan", MockHardware.set_fan)
# 
# controller.parse_mqtt_command("pump:on")
# controller.parse_mqtt_command("light:75")
# controller.set_mode("MANUAL")
# controller.execute_action("heater", "25")
