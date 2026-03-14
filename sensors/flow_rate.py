from gpiozero import DigitalInputDevice
import time

class FlowRateSensor:
    def __init__(self, pin=22):
        self.sensor = DigitalInputDevice(pin)
        self.pulses = 0
        self.sensor.when_activated = self._pulse
        self.last_time = time.time()

    def _pulse(self):
        self.pulses += 1

    def read(self):
        current_time = time.time()
        flow = self.pulses / (current_time - self.last_time)
        self.pulses = 0
        self.last_time = current_time
        return round(flow, 2)