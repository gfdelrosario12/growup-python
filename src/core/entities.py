"""
GrowUp IoT System - Domain Entities
===================================
Core domain entities representing business objects.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class HealthStatus(Enum):
    """Health status enumeration."""
    EXCELLENT = "Excellent"
    GOOD = "Good"
    WARNING = "Warning"
    CRITICAL = "Critical"
    UNKNOWN = "Unknown"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SensorReading:
    """Sensor reading entity."""
    
    # Water quality sensors
    water_temp: Optional[float] = None
    ph_level: Optional[float] = None
    dissolved_o2: Optional[float] = None
    ammonia: Optional[float] = None
    water_level: Optional[float] = None
    water_flow: Optional[float] = None
    
    # Air quality sensors
    air_temp: Optional[float] = None
    humidity: Optional[float] = None
    air_pressure: Optional[float] = None
    light_intensity: Optional[float] = None
    
    # Plant metrics (from ML)
    plant_height: Optional[float] = None
    plant_leaves: Optional[int] = None
    plant_health: Optional[float] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    reading_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "waterTemp": self.water_temp,
            "phLevel": self.ph_level,
            "dissolvedO2": self.dissolved_o2,
            "ammonia": self.ammonia,
            "waterLevel": self.water_level,
            "waterFlow": self.water_flow,
            "airTemp": self.air_temp,
            "humidity": self.humidity,
            "airPressure": self.air_pressure,
            "lightIntensity": self.light_intensity,
            "plantHeight": self.plant_height,
            "plantLeaves": self.plant_leaves,
            "plantHealth": self.plant_health,
            "timestamp": self.timestamp.isoformat()
        }
    
    def is_valid(self) -> bool:
        """Check if reading has minimum required data."""
        return any([
            self.water_temp is not None,
            self.ph_level is not None,
            self.dissolved_o2 is not None
        ])


@dataclass
class ControlState:
    """Hardware control state entity."""
    
    pump: bool = True
    fan: bool = False
    ph_adjustment: bool = True
    aerator: bool = True
    grow_light: bool = True
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    state_id: Optional[str] = None
    source: str = "system"  # system, backend, manual
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert to dictionary format."""
        return {
            "pump": self.pump,
            "fan": self.fan,
            "phAdjustment": self.ph_adjustment,
            "aerator": self.aerator,
            "growLight": self.grow_light
        }
    
    def get_control(self, name: str) -> bool:
        """Get control state by name."""
        control_map = {
            "pump": self.pump,
            "fan": self.fan,
            "phAdjustment": self.ph_adjustment,
            "aerator": self.aerator,
            "growLight": self.grow_light
        }
        return control_map.get(name, False)
    
    def set_control(self, name: str, value: bool) -> None:
        """Set control state by name."""
        if name == "pump":
            self.pump = value
        elif name == "fan":
            self.fan = value
        elif name == "phAdjustment":
            self.ph_adjustment = value
        elif name == "aerator":
            self.aerator = value
        elif name == "growLight":
            self.grow_light = value


@dataclass
class Detection:
    """Object detection result entity."""
    
    class_name: str
    confidence: float
    bbox: tuple  # (x, y, width, height)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "className": self.class_name,
            "confidence": self.confidence,
            "bbox": {
                "x": self.bbox[0],
                "y": self.bbox[1],
                "width": self.bbox[2],
                "height": self.bbox[3]
            },
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SystemStatus:
    """System status entity."""
    
    status: HealthStatus = HealthStatus.UNKNOWN
    uptime: float = 0.0  # seconds
    sensor_reading: Optional[SensorReading] = None
    control_state: Optional[ControlState] = None
    detections: List[Detection] = field(default_factory=list)
    
    backend_connected: bool = False
    hardware_initialized: bool = False
    camera_active: bool = False
    
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "status": self.status.value,
            "uptime": self.uptime,
            "sensorReading": self.sensor_reading.to_dict() if self.sensor_reading else None,
            "controlState": self.control_state.to_dict() if self.control_state else None,
            "detections": [d.to_dict() for d in self.detections],
            "backendConnected": self.backend_connected,
            "hardwareInitialized": self.hardware_initialized,
            "cameraActive": self.camera_active,
            "errors": self.errors,
            "warnings": self.warnings,
            "lastUpdated": self.last_updated.isoformat()
        }


@dataclass
class Alert:
    """System alert entity."""
    
    alert_type: str  # ph_low, temp_high, etc.
    severity: AlertSeverity
    message: str
    sensor_value: Optional[float] = None
    threshold: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "alertType": self.alert_type,
            "severity": self.severity.value,
            "message": self.message,
            "sensorValue": self.sensor_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged
        }
