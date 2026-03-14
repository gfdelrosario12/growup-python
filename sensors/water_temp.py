from w1thermsensor import W1ThermSensor

class WaterTempSensor:
    def __init__(self):
        self.sensor = W1ThermSensor()
    def read(self):
        return round(self.sensor.get_temperature(), 2)