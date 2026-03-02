import spidev

class MQ137:
    def __init__(self, channel=0):
        self.channel = channel
        self.spi = spidev.SpiDev()
        self.spi.open(0,0)
        self.spi.max_speed_hz = 1350000

    def read(self):
        adc = self.spi.xfer2([1, (8+self.channel)<<4, 0])
        data = ((adc[1]&3) << 8) + adc[2]
        return data
