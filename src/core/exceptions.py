"""
GrowUp IoT System - Core Exceptions
===================================
Custom exception hierarchy for domain-specific error handling.
"""

from typing import Optional, Dict, Any


class GrowUpError(Exception):
    """Base exception for all GrowUp IoT system errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# Hardware Exceptions
class HardwareError(GrowUpError):
    """Base exception for hardware-related errors."""
    pass


class GPIOError(HardwareError):
    """GPIO pin operation failed."""
    pass


class SensorError(HardwareError):
    """Sensor reading or initialization failed."""
    pass


class SensorNotFoundError(SensorError):
    """Sensor device not found or not connected."""
    pass


class SensorReadError(SensorError):
    """Failed to read data from sensor."""
    pass


class CameraError(HardwareError):
    """Camera operation failed."""
    pass


# Configuration Exceptions
class ConfigurationError(GrowUpError):
    """Configuration-related errors."""
    pass


class MissingConfigError(ConfigurationError):
    """Required configuration parameter missing."""
    pass


class InvalidConfigError(ConfigurationError):
    """Configuration parameter has invalid value."""
    pass


# Communication Exceptions
class CommunicationError(GrowUpError):
    """Base exception for communication errors."""
    pass


class BackendConnectionError(CommunicationError):
    """Failed to connect to backend server."""
    pass


class BackendAPIError(CommunicationError):
    """Backend API returned error response."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(
            message=message,
            error_code=f"HTTP_{status_code}" if status_code else None,
            details={"response": response_data} if response_data else {}
        )
        self.status_code = status_code


class NetworkTimeoutError(CommunicationError):
    """Network request timed out."""
    pass


# Validation Exceptions
class ValidationError(GrowUpError):
    """Data validation failed."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None
    ) -> None:
        super().__init__(
            message=message,
            details={"field": field, "value": value}
        )
        self.field = field
        self.value = value


class InvalidSensorDataError(ValidationError):
    """Sensor data validation failed."""
    pass


class InvalidControlStateError(ValidationError):
    """Control state validation failed."""
    pass


# System Exceptions
class SystemError(GrowUpError):
    """System-level errors."""
    pass


class InitializationError(SystemError):
    """Component initialization failed."""
    pass


class ShutdownError(SystemError):
    """System shutdown failed."""
    pass


# Resource Exceptions
class ResourceError(GrowUpError):
    """Resource-related errors."""
    pass


class ResourceNotFoundError(ResourceError):
    """Required resource not found."""
    pass


class ResourceBusyError(ResourceError):
    """Resource is currently in use."""
    pass
