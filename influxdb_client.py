from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
from config import INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def save_weekly_data(sensor_data, ml_result):
    point = Point("iot_weekly_data") \
        .tag("device", "raspberrypi") \
        .field("light", sensor_data.get("light", 0)) \
        .field("temperature", sensor_data.get("temperature", 0)) \
        .field("humidity", sensor_data.get("humidity", 0)) \
        .field("flow", sensor_data.get("flow", 0)) \
        .field("ammonia", sensor_data.get("ammonia", 0)) \
        .field("ph", sensor_data.get("ph", 0)) \
        .field("ml_result", str(ml_result)) \
        .time(datetime.utcnow())
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    print("[InfluxDB] Weekly data saved")
