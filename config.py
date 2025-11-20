# Sensor GPIO / I2C / ADC configuration
LIGHT_SENSORS = [0x23, 0x5C]
DS18B20_PINS = [4, 17]
BME280_ADDR = 0x76
FLOW_SENSORS = [5, 6]
MQ137_PIN = 0
PH_SENSOR_PIN = 1
RELAY_PINS = [12, 16, 20, 21, 25, 26, 19, 13]

# Server configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
WS_PORT = 8765

# InfluxDB configuration
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "your-token"
INFLUX_ORG = "your-org"
INFLUX_BUCKET = "iot_bucket"
