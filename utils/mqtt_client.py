import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, broker, port=1883):
        self.client = mqtt.Client()
        self.client.connect(broker, port)

    def publish(self, topic, payload):
        self.client.publish(topic, payload)