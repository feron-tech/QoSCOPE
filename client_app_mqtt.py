import time
import paho.mqtt.client as mqtt
import random
import string
import sys
import os
import time


_server_ip = os.getenv("ENV_SERVER_IP")
_server_port = int(os.getenv("ENV_SERVER_PORT", "1883"))
_sleep_sec = float(os.getenv("SLEEP_SEC", "1"))
_max_size = int(os.getenv("MAX_PAYLOAD_SIZE_BYTES", "1000"))

print(f'Will send to ip: {_server_ip}, port: {_server_port}')

unacked_publish = set()


def on_publish(client, userdata, mid, reason_code, properties):
    try:
        userdata.remove(mid)
    except KeyError:
        print("on_publish() is called with a mid not present in unacked_publish")

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish

mqttc.user_data_set(unacked_publish)
mqttc.connect(host=_server_ip, port=_server_port)
mqttc.loop_start()

while True:
    size = random.randint(1, _max_size)
    payload = ''.join(random.choices(string.ascii_letters + string.digits, k=size))

    msg_info = mqttc.publish(topic='golden_unit/test', payload=payload, qos=1)
    unacked_publish.add(msg_info.mid)

    time.sleep(_sleep_sec)

mqttc.disconnect()
mqttc.loop_stop()
