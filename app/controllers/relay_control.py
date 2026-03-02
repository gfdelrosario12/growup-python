import RPi.GPIO as GPIO

class Relay:
    def __init__(self, pins):
        self.pins = pins
        GPIO.setmode(GPIO.BCM)
        for pin in pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def set(self, channel, state):
        GPIO.output(self.pins[channel], GPIO.HIGH if state else GPIO.LOW)
