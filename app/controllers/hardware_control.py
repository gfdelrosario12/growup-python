"""
GrowUp IoT System - Hardware Control Module
============================================
Manages GPIO pins for relay control
"""

from typing import Dict
import time

# Try to import RPi.GPIO, use mock if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    # Mock GPIO for development on non-Raspberry Pi systems
    GPIO_AVAILABLE = False
    
    class MockGPIO:
        """Mock GPIO for testing on non-RPi systems"""
        BCM = "BCM"
        OUT = "OUT"
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode):
            pass
        
        @staticmethod
        def setwarnings(flag):
            pass
        
        @staticmethod
        def setup(pin, mode):
            pass
        
        @staticmethod
        def output(pin, state):
            pass
        
        @staticmethod
        def cleanup():
            pass
    
    GPIO = MockGPIO()
    print("⚠️  RPi.GPIO not available - using mock GPIO for development")

from app.utils.config import GPIO_PINS, RELAY_ACTIVE_HIGH, DEFAULT_CONTROLS, LOG_CONTROL_CHANGES

class HardwareController:
    """Controls hardware via GPIO pins"""
    
    def __init__(self):
        """Initialize GPIO pins and set default states"""
        self.current_state: Dict[str, bool] = DEFAULT_CONTROLS.copy()
        self._initialized = False
        self._mock_mode = not GPIO_AVAILABLE
        self._initialize_gpio()
    
    def _initialize_gpio(self):
        """Setup GPIO pins"""
        try:
            if not GPIO_AVAILABLE:
                print("⚠️  Running in MOCK GPIO mode (development)")
                self._initialized = True
                for control_name in GPIO_PINS.keys():
                    if LOG_CONTROL_CHANGES:
                        print(f"🔌 Mock: {control_name} initialized")
                return
            
            # Use BCM pin numbering
            GPIO.setmode(GPIO.BCM)
            
            # Disable warnings
            GPIO.setwarnings(False)
            
            # Setup all control pins as outputs
            for control_name, pin in GPIO_PINS.items():
                GPIO.setup(pin, GPIO.OUT)
                
                # Set initial state
                initial_state = self.current_state.get(control_name, False)
                self._set_gpio_pin(pin, initial_state)
                
                if LOG_CONTROL_CHANGES:
                    print(f"✅ Initialized {control_name} on GPIO {pin} → {'ON' if initial_state else 'OFF'}")
            
            self._initialized = True
            print("✅ Hardware controller initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize GPIO: {e}")
            print("⚠️  Running in MOCK mode (no actual GPIO control)")
            self._initialized = False
            self._mock_mode = True
    
    def _set_gpio_pin(self, pin: int, state: bool):
        """Set GPIO pin to HIGH or LOW based on relay logic"""
        if self._mock_mode:
            # Mock mode - just log
            return
        
        if not self._initialized:
            return
        
        try:
            if RELAY_ACTIVE_HIGH:
                # Relay activates on HIGH
                GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            else:
                # Relay activates on LOW (inverted logic for optocoupler)
                GPIO.output(pin, GPIO.LOW if state else GPIO.HIGH)
        except Exception as e:
            print(f"❌ GPIO error on pin {pin}: {e}")
    
    def update_control(self, control_name: str, state: bool) -> bool:
        """
        Update a single control
        
        Args:
            control_name: Name of control (pump, fan, phAdjustment, aerator, growLight)
            state: True for ON, False for OFF
            
        Returns:
            bool: Success status
        """
        if control_name not in GPIO_PINS:
            print(f"❌ Invalid control name: {control_name}")
            return False
        
        try:
            pin = GPIO_PINS[control_name]
            
            # Update GPIO
            self._set_gpio_pin(pin, state)
            
            # Update internal state
            old_state = self.current_state.get(control_name)
            self.current_state[control_name] = state
            
            if LOG_CONTROL_CHANGES and old_state != state:
                status = "ON" if state else "OFF"
                mode_prefix = "[MOCK] " if self._mock_mode else ""
                print(f"🔌 {mode_prefix}{control_name} → {status} (GPIO {pin})")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to update {control_name}: {e}")
            return False
    
    def update_multiple_controls(self, controls: Dict[str, bool]) -> Dict[str, bool]:
        """
        Update multiple controls at once
        
        Args:
            controls: Dictionary of control_name: state
            
        Returns:
            dict: Updated control states
        """
        for control_name, state in controls.items():
            self.update_control(control_name, state)
        
        return self.get_all_states()
    
    def get_state(self, control_name: str) -> bool:
        """Get current state of a control"""
        return self.current_state.get(control_name, False)
    
    def get_all_states(self) -> Dict[str, bool]:
        """Get all control states"""
        return self.current_state.copy()
    
    def get_states(self) -> Dict[str, bool]:
        """Get all control states (alias for get_all_states)"""
        return self.get_all_states()
    
    def emergency_stop(self):
        """Emergency stop - turn off all devices except pump"""
        print("🚨 EMERGENCY STOP ACTIVATED")
        
        for control_name in GPIO_PINS.keys():
            if control_name != "pump":  # Keep pump running
                self.update_control(control_name, False)
        
        print("⚠️  All devices stopped (pump still running)")
    
    def cleanup(self):
        """Cleanup GPIO on shutdown"""
        if self._initialized and GPIO_AVAILABLE and not self._mock_mode:
            print("🧹 Cleaning up GPIO...")
            GPIO.cleanup()
            print("✅ GPIO cleanup complete")
        elif self._mock_mode:
            print("🧹 Mock GPIO cleanup (no action needed)")

# Global hardware controller instance
_hardware_controller = None

def get_hardware_controller() -> HardwareController:
    """Get singleton hardware controller instance"""
    global _hardware_controller
    if _hardware_controller is None:
        _hardware_controller = HardwareController()
    return _hardware_controller

def cleanup_hardware():
    """Cleanup hardware on shutdown"""
    global _hardware_controller
    if _hardware_controller:
        _hardware_controller.cleanup()

# Export GPIO_AVAILABLE for testing
__all__ = ['HardwareController', 'get_hardware_controller', 'cleanup_hardware', 'GPIO_AVAILABLE']

# Example usage
if __name__ == "__main__":
    import time
    
    print("Testing Hardware Controller...")
    controller = get_hardware_controller()
    
    print("\nCurrent states:")
    print(controller.get_all_states())
    
    print("\nTesting pump toggle...")
    controller.update_control("pump", True)
    time.sleep(2)
    controller.update_control("pump", False)
    time.sleep(2)
    
    print("\nTesting grow light...")
    controller.update_control("growLight", True)
    time.sleep(2)
    controller.update_control("growLight", False)
    
    print("\nTesting multiple controls...")
    controller.update_multiple_controls({
        "pump": True,
        "fan": True,
        "aerator": True
    })
    time.sleep(3)
    
    print("\nCleanup...")
    cleanup_hardware()
    print("✅ Test complete")
