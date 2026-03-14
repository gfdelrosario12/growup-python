from gpiozero import DigitalInputDevice

class WaterLevelSensor:
    def __init__(self, pin=27):
        self.sensor = DigitalInputDevice(pin)
    def read(self):
        return int(self.sensor.value)