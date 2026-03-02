"""
GrowUp IoT System - Core Interfaces
===================================
Abstract base classes defining contracts for system components.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from .entities import SensorReading, ControlState, Detection


class ISensorReader(ABC):
    """Interface for sensor reading implementations."""
    
    @abstractmethod
    def read(self) -> float:
        """Read current value from sensor."""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize sensor hardware."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup sensor resources."""
        pass
    
    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if sensor is available."""
        pass


class IHardwareController(ABC):
    """Interface for hardware control implementations."""
    
    @abstractmethod
    def set_state(self, control_name: str, state: bool) -> None:
        """Set control state."""
        pass
    
    @abstractmethod
    def get_state(self, control_name: str) -> bool:
        """Get current control state."""
        pass
    
    @abstractmethod
    def get_all_states(self) -> Dict[str, bool]:
        """Get all control states."""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize hardware."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup hardware resources."""
        pass


class IBackendClient(ABC):
    """Interface for backend API client."""
    
    @abstractmethod
    def send_sensor_reading(self, reading: SensorReading) -> Dict[str, Any]:
        """Send sensor reading to backend."""
        pass
    
    @abstractmethod
    def get_latest_controls(self) -> Optional[ControlState]:
        """Get latest control state from backend."""
        pass
    
    @abstractmethod
    def acknowledge_controls(self, state: ControlState) -> None:
        """Acknowledge control state applied."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check backend connectivity."""
        pass


class IDetectionEngine(ABC):
    """Interface for ML detection engine."""
    
    @abstractmethod
    def detect(self, frame: Any) -> List[Detection]:
        """Perform object detection on frame."""
        pass
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize detection engine."""
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        """Check if engine is ready."""
        pass


class IRepository(ABC):
    """Generic repository interface."""
    
    @abstractmethod
    def save(self, entity: Any) -> Any:
        """Save entity."""
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: Any) -> Optional[Any]:
        """Find entity by ID."""
        pass
    
    @abstractmethod
    def find_all(self) -> List[Any]:
        """Find all entities."""
        pass
    
    @abstractmethod
    def delete(self, entity_id: Any) -> None:
        """Delete entity."""
        pass


class ILogger(ABC):
    """Interface for logging implementations."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        pass
    
    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        pass


class IConfigProvider(ABC):
    """Interface for configuration providers."""
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass
    
    @abstractmethod
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value."""
        pass
    
    @abstractmethod
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        pass
    
    @abstractmethod
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        pass
    
    @abstractmethod
    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value."""
        pass


class IEventBus(ABC):
    """Interface for event bus implementations."""
    
    @abstractmethod
    def publish(self, event_type: str, data: Any) -> None:
        """Publish event."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> None:
        """Subscribe to event."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> None:
        """Unsubscribe from event."""
        pass
