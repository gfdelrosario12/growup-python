"""
GrowUp IoT System - Settings Management
=======================================
Environment-based configuration with validation and type safety.
"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

from ..core.exceptions import ConfigurationError, MissingConfigError, InvalidConfigError


# Load environment variables from .env file
load_dotenv()


@dataclass
class BackendConfig:
    """Backend API configuration."""
    
    host: str
    port: int = 8080
    use_https: bool = False
    timeout: int = 10
    api_key: Optional[str] = None
    
    @property
    def base_url(self) -> str:
        """Get base URL."""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    @property
    def sensor_readings_url(self) -> str:
        """Get sensor readings endpoint URL."""
        return f"{self.base_url}/api/sensor-readings"
    
    @property
    def controls_url(self) -> str:
        """Get controls endpoint URL."""
        return f"{self.base_url}/api/controls"


@dataclass
class GPIOConfig:
    """GPIO pin configuration."""
    
    pump_pin: int = 17
    fan_pin: int = 18
    ph_adjustment_pin: int = 27
    aerator_pin: int = 22
    grow_light_pin: int = 23
    
    relay_active_high: bool = True
    
    def get_pin(self, control_name: str) -> int:
        """Get GPIO pin for control."""
        pin_map = {
            "pump": self.pump_pin,
            "fan": self.fan_pin,
            "phAdjustment": self.ph_adjustment_pin,
            "aerator": self.aerator_pin,
            "growLight": self.grow_light_pin
        }
        pin = pin_map.get(control_name)
        if pin is None:
            raise InvalidConfigError(f"Unknown control name: {control_name}")
        return pin


@dataclass
class SensorConfig:
    """Sensor configuration."""
    
    # I2C addresses
    bme280_address: int = 0x76
    bh1750_address: int = 0x23
    
    # ADC channels
    ph_channel: int = 0
    do_channel: int = 1
    ammonia_channel: int = 2
    
    # GPIO pins
    flow_sensor_pin: int = 24
    ultrasonic_trigger_pin: int = 25
    ultrasonic_echo_pin: int = 8
    
    # Calibration values
    ph_calibration_offset: float = 0.0
    ph_calibration_slope: float = 1.0
    
    # Reading intervals (seconds)
    read_interval: float = 1.0


@dataclass
class TimingConfig:
    """Timing configuration."""
    
    send_interval: int = 60  # seconds
    control_poll_interval: int = 5  # seconds
    
    # Significant change thresholds
    temp_threshold: float = 0.5  # ±0.5°C
    ph_threshold: float = 0.2  # ±0.2 pH
    do_threshold: float = 0.5  # ±0.5 mg/L
    ammonia_threshold: float = 0.05  # ±0.05 ppm
    humidity_threshold: float = 5.0  # ±5%
    light_threshold: float = 100.0  # ±100 lux
    
    def get_threshold(self, sensor_key: str) -> float:
        """Get threshold for sensor."""
        threshold_map = {
            "water_temp": self.temp_threshold,
            "air_temp": self.temp_threshold,
            "ph_level": self.ph_threshold,
            "dissolved_o2": self.do_threshold,
            "ammonia": self.ammonia_threshold,
            "humidity": self.humidity_threshold,
            "light_intensity": self.light_threshold
        }
        return threshold_map.get(sensor_key, 0.0)


@dataclass
class CameraConfig:
    """Camera configuration."""
    
    enabled: bool = True
    resolution: tuple = (640, 480)
    fps: int = 15
    model_path: Optional[str] = None
    confidence_threshold: float = 0.5


@dataclass
class LoggingConfig:
    """Logging configuration."""
    
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5
    console_output: bool = True


@dataclass
class Settings:
    """Main settings class."""
    
    # Environment
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Configuration sections
    backend: BackendConfig = field(default_factory=BackendConfig)
    gpio: GPIOConfig = field(default_factory=GPIOConfig)
    sensors: SensorConfig = field(default_factory=SensorConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    # System
    demo_mode: bool = False
    enable_lcd: bool = False
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        
        # Backend configuration
        backend_host = os.getenv("BACKEND_HOST")
        if not backend_host:
            raise MissingConfigError("BACKEND_HOST environment variable is required")
        
        backend = BackendConfig(
            host=backend_host,
            port=int(os.getenv("BACKEND_PORT", "8080")),
            use_https=os.getenv("BACKEND_USE_HTTPS", "false").lower() == "true",
            timeout=int(os.getenv("BACKEND_TIMEOUT", "10")),
            api_key=os.getenv("BACKEND_API_KEY")
        )
        
        # GPIO configuration
        gpio = GPIOConfig(
            pump_pin=int(os.getenv("GPIO_PUMP_PIN", "17")),
            fan_pin=int(os.getenv("GPIO_FAN_PIN", "18")),
            ph_adjustment_pin=int(os.getenv("GPIO_PH_PIN", "27")),
            aerator_pin=int(os.getenv("GPIO_AERATOR_PIN", "22")),
            grow_light_pin=int(os.getenv("GPIO_LIGHT_PIN", "23")),
            relay_active_high=os.getenv("RELAY_ACTIVE_HIGH", "true").lower() == "true"
        )
        
        # Sensor configuration
        sensors = SensorConfig(
            read_interval=float(os.getenv("SENSOR_READ_INTERVAL", "1.0"))
        )
        
        # Timing configuration
        timing = TimingConfig(
            send_interval=int(os.getenv("SEND_INTERVAL", "60")),
            control_poll_interval=int(os.getenv("CONTROL_POLL_INTERVAL", "5"))
        )
        
        # Camera configuration
        camera = CameraConfig(
            enabled=os.getenv("CAMERA_ENABLED", "true").lower() == "true",
            model_path=os.getenv("CAMERA_MODEL_PATH")
        )
        
        # Logging configuration
        logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            file_path=os.getenv("LOG_FILE_PATH"),
            console_output=os.getenv("LOG_CONSOLE", "true").lower() == "true"
        )
        
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            demo_mode=os.getenv("DEMO_MODE", "false").lower() == "true",
            enable_lcd=os.getenv("ENABLE_LCD", "false").lower() == "true",
            backend=backend,
            gpio=gpio,
            sensors=sensors,
            timing=timing,
            camera=camera,
            logging=logging
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        # Validate backend
        if not self.backend.host:
            raise InvalidConfigError("Backend host cannot be empty")
        
        if not 1 <= self.backend.port <= 65535:
            raise InvalidConfigError(f"Invalid backend port: {self.backend.port}")
        
        # Validate GPIO pins
        valid_pins = range(2, 28)  # Raspberry Pi GPIO pin range
        for control in ["pump", "fan", "phAdjustment", "aerator", "growLight"]:
            pin = self.gpio.get_pin(control)
            if pin not in valid_pins:
                raise InvalidConfigError(f"Invalid GPIO pin for {control}: {pin}")
        
        # Validate timing
        if self.timing.send_interval < 1:
            raise InvalidConfigError("Send interval must be at least 1 second")
        
        if self.timing.control_poll_interval < 1:
            raise InvalidConfigError("Control poll interval must be at least 1 second")
        
        # Validate logging
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level not in valid_levels:
            raise InvalidConfigError(f"Invalid log level: {self.logging.level}")


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
        _settings.validate()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = None
    return get_settings()
