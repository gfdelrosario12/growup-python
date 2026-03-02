# GrowUp IoT System - Migration Guide

## 🎯 Overview

This guide explains how to migrate from the current codebase to the new professional architecture while maintaining functionality.

---

## 📋 Prerequisites

### 1. Install New Dependencies
```bash
# For production
pip install -r requirements/prod.txt

# For development (includes testing tools)
pip install -r requirements/dev.txt

# For testing only
pip install -r requirements/test.txt
```

### 2. Create Environment File
```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

**Required variables:**
- `BACKEND_HOST` - Your backend server address
- `BACKEND_PORT` - Backend port (default: 8080)

---

## 🔄 Migration Steps

### Step 1: Update Imports (Gradual)

#### Before:
```python
from config import BACKEND_HOST, GPIO_PINS
print(f"Starting system on {BACKEND_HOST}")
```

#### After:
```python
from src.config.settings import get_settings
from src.config.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)

logger.info(f"Starting system on {settings.backend.base_url}")
```

### Step 2: Use Structured Exceptions

#### Before:
```python
try:
    value = sensor.read()
except Exception as e:
    print(f"Error: {e}")
```

#### After:
```python
from src.core.exceptions import SensorReadError

try:
    value = sensor.read()
except SensorReadError as e:
    logger.error(
        f"Sensor read failed: {e.message}",
        extra={'sensor': sensor.name, 'details': e.details},
        exc_info=True
    )
    # Handle gracefully
```

### Step 3: Use Domain Entities

#### Before:
```python
sensor_data = {
    "waterTemp": 23.5,
    "ph": 7.0,
    "dissolvedO2": 8.2
}
```

#### After:
```python
from src.core.entities import SensorReading

reading = SensorReading(
    water_temp=23.5,
    ph_level=7.0,
    dissolved_o2=8.2
)

# Validate
if reading.is_valid():
    # Send to backend
    data = reading.to_dict()
```

### Step 4: Implement Interfaces

#### Before:
```python
class TemperatureSensor:
    def read(self):
        # Implementation
        pass
```

#### After:
```python
from src.core.interfaces import ISensorReader
from src.core.exceptions import SensorReadError

class TemperatureSensor(ISensorReader):
    """DS18B20 temperature sensor implementation."""
    
    def __init__(self, device_id: str):
        self._device_id = device_id
        self._initialized = False
    
    def read(self) -> float:
        """Read temperature in Celsius."""
        if not self._initialized:
            raise SensorReadError("Sensor not initialized")
        
        try:
            # Read from sensor
            value = self._read_from_device()
            return value
        except Exception as e:
            raise SensorReadError(
                f"Failed to read temperature",
                details={'device_id': self._device_id, 'error': str(e)}
            )
    
    def initialize(self) -> None:
        """Initialize sensor hardware."""
        # Setup code
        self._initialized = True
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        self._initialized = False
    
    @property
    def is_available(self) -> bool:
        """Check if sensor is available."""
        return self._initialized
```

---

## 🗂️ File Migration Map

| Old File | New Location | Status |
|----------|--------------|--------|
| `config.py` | `src/config/settings.py` | ✅ Use `get_settings()` |
| `hardware_control.py` | `src/infrastructure/hardware/gpio_controller.py` | 🔄 TODO |
| `sensors/*.py` | `src/infrastructure/sensors/*.py` | 🔄 TODO |
| `main.py` | `src/application/orchestrators/system_orchestrator.py` | 🔄 TODO |
| `lcd_viewer.py` | `src/presentation/gui/lcd_viewer.py` | 🔄 TODO |
| `camera/*` | `src/infrastructure/camera/*` | 🔄 TODO |

---

## 🧪 Testing Your Migration

### 1. Test Configuration
```python
# test_config.py
from src.config.settings import get_settings

def test_settings():
    settings = get_settings()
    assert settings.backend.host is not None
    assert settings.backend.port > 0
    settings.validate()  # Should not raise
    print("✅ Configuration OK")

if __name__ == "__main__":
    test_settings()
```

### 2. Test Logging
```python
# test_logging.py
from src.config.logging_config import setup_logging, get_logger

setup_logging(level="DEBUG", console_output=True)
logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")

print("✅ Logging OK")
```

### 3. Test Entities
```python
# test_entities.py
from src.core.entities import SensorReading, ControlState

def test_sensor_reading():
    reading = SensorReading(
        water_temp=23.5,
        ph_level=7.0
    )
    assert reading.is_valid()
    data = reading.to_dict()
    assert "waterTemp" in data
    print("✅ SensorReading OK")

def test_control_state():
    state = ControlState(pump=True, fan=False)
    assert state.get_control("pump") == True
    data = state.to_dict()
    assert "pump" in data
    print("✅ ControlState OK")

if __name__ == "__main__":
    test_sensor_reading()
    test_control_state()
```

---

## 📝 Code Style Guidelines

### 1. Use Type Hints
```python
def read_sensor(sensor_id: str) -> float:
    """Read sensor value."""
    pass

def process_data(values: List[float]) -> Dict[str, Any]:
    """Process sensor values."""
    pass
```

### 2. Use Docstrings
```python
def calculate_average(values: List[float]) -> float:
    """
    Calculate average of sensor values.
    
    Args:
        values: List of sensor readings
    
    Returns:
        Average value
    
    Raises:
        ValueError: If values list is empty
    """
    if not values:
        raise ValueError("Cannot calculate average of empty list")
    return sum(values) / len(values)
```

### 3. Use Structured Logging
```python
# ❌ Don't use print
print(f"Reading sensor {sensor_id}: {value}")

# ✅ Use logger
logger.info(
    "Sensor reading completed",
    extra={
        'sensor_id': sensor_id,
        'value': value,
        'unit': 'celsius'
    }
)
```

### 4. Use Context Managers
```python
# ❌ Manual cleanup
sensor = TemperatureSensor()
sensor.initialize()
try:
    value = sensor.read()
finally:
    sensor.cleanup()

# ✅ Context manager
class TemperatureSensor:
    def __enter__(self):
        self.initialize()
        return self
    
    def __exit__(self, *args):
        self.cleanup()

# Usage
with TemperatureSensor() as sensor:
    value = sensor.read()
```

---

## 🔐 Security Best Practices

### 1. Never Hardcode Secrets
```python
# ❌ Don't do this
API_KEY = "secret123"

# ✅ Do this
from src.config.settings import get_settings
settings = get_settings()
api_key = settings.backend.api_key  # From .env
```

### 2. Validate Input
```python
from src.core.exceptions import ValidationError

def set_temperature_threshold(value: float) -> None:
    """Set temperature threshold."""
    if not isinstance(value, (int, float)):
        raise ValidationError(
            "Temperature must be a number",
            field="temperature",
            value=value
        )
    
    if not 0 <= value <= 50:
        raise ValidationError(
            "Temperature must be between 0 and 50°C",
            field="temperature",
            value=value
        )
```

### 3. Sanitize Data
```python
def process_sensor_name(name: str) -> str:
    """Sanitize sensor name."""
    # Remove special characters
    import re
    return re.sub(r'[^a-zA-Z0-9_-]', '', name)
```

---

## 🚀 Running the System

### Development Mode
```bash
# Set environment
export ENVIRONMENT=development
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run
python main.py --lcd --demo
```

### Production Mode
```bash
# Set environment
export ENVIRONMENT=production
export DEBUG=false
export LOG_LEVEL=INFO

# Run
python main.py
```

### With Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements/prod.txt

# Run
python main.py
```

---

## 📊 Verification Checklist

After migration, verify:

- [ ] `.env` file created with all required variables
- [ ] No hardcoded credentials in code
- [ ] All print statements replaced with logger calls
- [ ] Type hints added to functions
- [ ] Exceptions use custom exception classes
- [ ] Configuration accessed via `get_settings()`
- [ ] Tests pass (if written)
- [ ] Code follows PEP 8 style
- [ ] Documentation updated

---

## 🆘 Troubleshooting

### Issue: ImportError for src module
```bash
# Solution: Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/rpi"
```

### Issue: Missing environment variables
```bash
# Solution: Check .env file exists and is loaded
python -c "from src.config.settings import get_settings; print(get_settings().backend.host)"
```

### Issue: GPIO permissions
```bash
# Solution: Add user to gpio group
sudo usermod -a -G gpio $USER
# Logout and login again
```

---

## 📚 Resources

- **PEP 8:** https://pep8.org/
- **Type Hints:** https://docs.python.org/3/library/typing.html
- **Logging:** https://docs.python.org/3/library/logging.html
- **Clean Architecture:** https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html

---

## 🎯 Next Steps

1. Create `.env` file from `.env.example`
2. Test configuration loading
3. Test logging setup
4. Start migrating one module at a time
5. Write tests as you migrate
6. Update documentation

---

**Remember: Migration can be gradual. Old and new code can coexist!** 🚀
