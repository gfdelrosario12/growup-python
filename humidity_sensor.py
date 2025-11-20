import board, busio, adafruit_bme280

class BME280Sensor:
    def __init__(self, addr=0x76):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=addr)

    def read(self):
        return {
            "temperature": self.sensor.temperature,
            "humidity": self.sensor.humidity,
            "pressure": self.sensor.pressure
        }
