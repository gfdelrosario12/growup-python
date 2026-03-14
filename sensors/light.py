import smbus2
import bh1750

class LightSensor:
    def __init__(self):
        self.sensor = bh1750.BH1750()
    def read(self):
        return round(self.sensor.luminance(bh1750.BH1750.CONT_HIRES_1), 2)