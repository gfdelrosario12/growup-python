from bmp280 import BMP280
import smbus2

class AirSensor:
    def __init__(self):
        self.bus = smbus2.SMBus(1)
        self.sensor = BMP280(i2c_dev=self.bus)
    def read(self):
        return {
            "temperature": round(self.sensor.get_temperature(), 2),
            "pressure": round(self.sensor.get_pressure(), 2)
        }