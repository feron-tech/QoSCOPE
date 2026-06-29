import paho.mqtt.client as mqtt
import json


class MQTTClient:
    def __init__(self, broker: str, port: int, username: str, password: str):
        self.client: mqtt.Client = mqtt.Client()
        self.client.username_pw_set(username, password)
        _ = self.client.connect(broker, port, 60)
        _ = self.client.loop_start()

    def publish_json(self, topic: str, data: dict[str, int]):
        payload = json.dumps(data)
        result = self.client.publish(topic, payload)
        return result.rc == mqtt.MQTT_ERR_SUCCESS


MQTT_BROKER = "10.242.211.200"
MQTT_PORT = 1884
MQTT_USER = "myuser"
MQTT_PASS = "vicomtech"
MQTT_TOPIC = "data"


def post_mqtt_metric(value: int):
    mqtt = MQTTClient(MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS)

    if not mqtt.publish_json(MQTT_TOPIC, {"custom_user_value": value}):
        print("Error sending to the MQTT broker.")
    else:
        print("Successful transmission to the MQTT broker.")
