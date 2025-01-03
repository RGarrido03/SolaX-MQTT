import logging
from typing import Any

import paho.mqtt.client as mqtt


def connect_mqtt(
    broker: str,
    username: str = None,
    password: str = None,
) -> mqtt.Client | None:
    client = mqtt.Client()
    client.reconnect_delay_set(min_delay=1, max_delay=120)

    if username and password:
        client.username_pw_set(username, password)

    try:
        client.connect(broker)
        client.on_disconnect = lambda client, userdata, rc: client.reconnect()
        return client
    except Exception as err:
        logging.error(f"MQTT connection error: {err}")
        exit(1)


def publish_to_mqtt(client: mqtt.Client, topic: str, value: Any, retain: bool = False):
    try:
        client.publish(topic, value, retain=retain)
    except Exception as err:
        logging.error(f"MQTT publish error: {err}")
