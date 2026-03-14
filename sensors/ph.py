from gpiozero import MCP3008

class PHSensor:
    def __init__(self, channel=0):
        self.adc = MCP3008(channel=channel)
    def read(self):
        voltage = self.adc.value * 3.3
        ph = round(7 + ((2.5 - voltage) / 0.18), 2)
        return ph