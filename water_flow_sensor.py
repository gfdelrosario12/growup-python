import RPi.GPIO as GPIO

class FlowSensor:
    def __init__(self, pin):
        self.pin = pin
        self.flow_count = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=self.flow_pulse)

    def flow_pulse(self, channel):
        self.flow_count += 1

    def get_flow_rate(self):
        count = self.flow_count
        self.flow_count = 0
        return count
