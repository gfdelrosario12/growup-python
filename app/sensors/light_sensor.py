import smbus

class BH1750:
    def __init__(self, addr=0x23):
        self.bus = smbus.SMBus(1)
        self.addr = addr
        self.mode = 0x10

    def read_light(self):
        data = self.bus.read_i2c_block_data(self.addr, self.mode)
        lux = (data[0] << 8) + data[1]
        return lux / 1.2
