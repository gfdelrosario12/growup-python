"""
System Mode Manager Module
===========================
Manages global system modes (AUTO/MANUAL) and broadcasts to all devices via MQTT.
AUTO: System operates autonomously based on sensor readings and rules.
MANUAL: System responds to backend commands.
"""

import os
from enum import Enum
from typing import Dict, Callable, Optional
import json

class SystemMode(Enum):
    """Global system operating modes."""
    AUTO = "AUTO"      # Autonomous operation
    MANUAL = "MANUAL"  # Backend-controlled operation


class ModeManager:
    """
    Centralized system mode manager.
    Handles mode switching, broadcasting, and callbacks.
    """
    
    def __init__(self, device_id: str = "pi-001", verbose: bool = False):
        """
        Initialize mode manager.
        
        Args:
            device_id: Device identifier
            verbose: Enable verbose logging
        """
        self.device_id = device_id
        self.verbose = verbose
        self.mode = SystemMode.AUTO  # Default to AUTO
        self.mode_callbacks = []  # Functions to call when mode changes
        self.mode_history = []  # Track mode changes
    
    def register_mode_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback to be called when mode changes.
        
        Args:
            callback: Function to call on mode change
                     Signature: callback(mode: str) -> None
        
        Example:
            manager.register_mode_callback(on_mode_changed)
        """
        self.mode_callbacks.append(callback)
        self._log(f"✅ Registered mode callback")
    
    def set_mode(self, mode: str) -> bool:
        """
        Set system mode.
        
        Args:
            mode: "AUTO" or "MANUAL"
        
        Returns:
            bool: True if mode changed successfully
        """
        try:
            mode_enum = SystemMode[mode.upper()]
            
            # Only log if actually changing
            if self.mode == mode_enum:
                self._log(f"ℹ️  Mode already {mode_enum.value}")
                return True
            
            old_mode = self.mode.value
            self.mode = mode_enum
            
            self._log(f"🎛️  System mode: {old_mode} → {mode_enum.value}")
            
            # Track in history
            self.mode_history.append({
                "from": old_mode,
                "to": mode_enum.value,
                "timestamp": self._timestamp()
            })
            
            # Call registered callbacks
            for callback in self.mode_callbacks:
                try:
                    callback(mode_enum.value)
                except Exception as e:
                    print(f"⚠️  Mode callback error: {e}")
            
            return True
        
        except KeyError:
            print(f"❌ Invalid mode: {mode}. Use AUTO or MANUAL")
            return False
    
    def get_mode(self) -> str:
        """Get current system mode."""
        return self.mode.value
    
    def is_auto_mode(self) -> bool:
        """Check if in AUTO mode."""
        return self.mode == SystemMode.AUTO
    
    def is_manual_mode(self) -> bool:
        """Check if in MANUAL mode."""
        return self.mode == SystemMode.MANUAL
    
    def get_status(self) -> Dict:
        """Get mode manager status."""
        return {
            "device_id": self.device_id,
            "current_mode": self.mode.value,
            "mode_history": self.mode_history[-5:] if self.mode_history else [],
            "total_mode_changes": len(self.mode_history)
        }
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    @staticmethod
    def _timestamp() -> str:
        """Get current timestamp in ISO format."""
        import time
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


# Example usage:
# manager = ModeManager("pi-001", verbose=True)
# manager.register_mode_callback(on_system_mode_changed)
# manager.set_mode("MANUAL")
# print(manager.get_status())
