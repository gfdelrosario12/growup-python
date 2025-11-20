from flask import Flask, jsonify
from camera.camera_ml import CameraML
from sensors.light_sensor import BH1750
from sensors.temp_sensor import DS18B20
from sensors.humidity_sensor import BME280Sensor
from sensors.water_flow_sensor import FlowSensor
from sensors.ammonia_sensor import MQ137
from sensors.ph_sensor import PHSensor

app = Flask(__name__)

light = BH1750()
temp = DS18B20(4)
humidity = BME280Sensor()
flow = FlowSensor(5)
ammonia = MQ137(0)
ph = PHSensor(1)
camera_ml = CameraML()

@app.route("/sensors")
def get_sensors():
    data = {
        "light": light.read_light(),
        "temperature": temp.read_temp(),
        "humidity": humidity.read()["humidity"],
        "flow": flow.get_flow_rate(),
        "ammonia": ammonia.read(),
        "ph": ph.read()
    }
    return jsonify(data)

@app.route("/ml_result")
def get_ml_result():
    return jsonify({"result": str(camera_ml.last_result)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
